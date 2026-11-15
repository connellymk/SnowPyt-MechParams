"""Analysis-only Gaussian propagation with shared raw observations.

Vectorized equations are checked against production methods in tests. No draws
are clipped, replaced, or resampled. Conditional summaries retain failure counts.
The framework's density outputs rebuild ufloats; correlated sensitivity is thus
evaluated here from raw draws rather than assuming those outputs retain covariance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from uncertainties import ufloat

from review_metrics import number, path_key, write_json
from snowpyt_mechparams.constants import resolve_grain_form_for_method
from snowpyt_mechparams.methods.layer._applicability import density_bounds
from snowpyt_mechparams.execution import ExecutionConfig, ExecutionEngine
from snowpyt_mechparams.models import Layer, Slab, Pit
from snowpyt_mechparams.snowpilot import parse_caaml_file

SEED = 20261114
# Published coefficients repeated explicitly for independently evaluable samples.
LINEAR = {
    "geldsetzer": {
        "PP": (45, 36),
        "PPgp": (83, 37),
        "DF": (65, 36),
        "FC": (112, 46),
        "DH": (185, 25),
    },
    "kim_jamieson_table2": {
        "PP": (41.3, 40.3),
        "PPgp": (61.8, 46.4),
        "DF": (62.5, 37.4),
        "RGxf": (85, 46.3),
        "FC": (103, 50.6),
        "FCxr": (68.8, 58.6),
        "DH": (214, 19),
        "MFcr": (235, 15.1),
    },
}
MULTI = {
    "FC": (51.9, 19.7, 82.8),
    "FCxr": (60.4, 27.7, 36.7),
    "PP": (40, -7.33, 52.8),
    "PPgp": (38.8, 18.8, 35.7),
    "DF": (37.9, -8.87, 71.4),
    "MF": (34.9, 11.2, 124.5),
}


def standardized_draws(n, layers, correlation, rng):
    common = rng.standard_normal((n, 1))
    independent = rng.standard_normal((n, layers))
    return np.sqrt(correlation) * common + np.sqrt(1 - correlation) * independent


def sample_observations(slab, n, correlation, seed):
    rng = np.random.default_rng(seed)
    samples = {}
    for field in [
        "density_measured",
        "hand_hardness_index",
        "grain_size_avg",
        "thickness",
    ]:
        values = [getattr(layer, field) for layer in slab.layers]
        means = np.array([number(x) for x in values])
        sigma = np.array([float(getattr(x, "std_dev", 0)) for x in values])
        samples[field] = (
            means + standardized_draws(n, len(values), correlation, rng) * sigma
        )
    samples["angle"] = number(slab.angle) + rng.standard_normal(n) * float(
        getattr(slab.angle, "std_dev", 0)
    )
    return samples


def density_vector(method, grain, samples, layer_index):
    from loss_analysis_utils import HARDNESS_RANGES

    n = len(samples["angle"])
    if method == "data_flow":
        return samples["density_measured"][:, layer_index], np.ones(n, bool)
    grain = resolve_grain_form_for_method(grain, method)
    if grain is None:
        return np.full(n, np.nan), np.zeros(n, bool)
    h = samples["hand_hardness_index"][:, layer_index]
    low, high = HARDNESS_RANGES[method][grain]
    valid = (h >= low) & (h <= high)
    with np.errstate(invalid="ignore", over="ignore"):
        if method == "geldsetzer" and grain == "RG":
            rho = 154 + 1.51 * h**3.15
        elif method == "kim_jamieson_table2" and grain == "RG":
            rho = 91.8 * np.exp(0.270 * h)
        elif method == "kim_jamieson_table6":
            a, b, c = MULTI[grain]
            rho = a * h + b * samples["grain_size_avg"][:, layer_index] + c
        else:
            a, b = LINEAR[method][grain]
            rho = a + b * h
    return rho, valid


def elastic_vector(method, grain, rho):
    grain = grain[:2].upper()
    bounds = density_bounds(method, grain)
    if bounds is None:
        return np.full(len(rho), np.nan), np.zeros(len(rho), bool)
    valid = (rho >= bounds[0]) & (rho <= bounds[1])
    with np.errstate(invalid="ignore", over="ignore"):
        if method == "bergfeld":
            value = 6500 * (rho / 917) ** 4.4
        elif method == "wautier":
            value = 10000 * 0.78 * (rho / 917) ** 2.34
        elif method == "kochle":
            value = np.where(
                rho < 250, 0.0061 * np.exp(0.0396 * rho), 6.0457 * np.exp(0.011 * rho)
            )
        else:
            a, exponent = (
                (0.4, 4.6)
                if grain in {"DF", "RG"}
                else (1.8, 5.1) if grain in {"FC", "DH"} else (0.011, 1.7)
            )
            value = 10000 * a * (rho / 917) ** exponent
    return value, valid


def evaluate(slab, target, methods, samples):
    """Return values and mutually exclusive physical/domain/numerical masks."""
    n = len(samples["angle"])
    physical, domain = np.ones(n, bool), np.ones(n, bool)
    values, moduli, ratios = [], [], []
    density_method = methods[0]
    for i, layer in enumerate(slab.layers):
        fields = (
            ["density_measured"]
            if density_method == "data_flow"
            else ["hand_hardness_index"]
        )
        if density_method == "kim_jamieson_table6":
            fields.append("grain_size_avg")
        if target in {"D11", "slab_weight_shear"}:
            fields.append("thickness")
        for field in fields:
            x = samples[field][:, i]
            physical &= np.isfinite(x) & (x > 0)
            if field == "density_measured":
                physical &= x <= 917
            if field == "hand_hardness_index":
                physical &= (x >= 0.67) & (x <= 6.33)
        rho, ok = density_vector(density_method, layer.grain_form or "", samples, i)
        domain &= ok
        # Negative computed density is a numerical/physical output failure,
        # not a negative observed-input draw; retain it in numerical failures.
        values.append(rho)
        if target in {"elastic_modulus", "D11"}:
            E, ok = elastic_vector(methods[1], layer.grain_form or "", rho)
            domain &= ok
            moduli.append(E)
        if target == "D11":
            g = (layer.grain_form or "")[:2].upper()
            nu_map = (
                {"RG": 0.171, "FC": 0.130, "DH": 0.087}
                if methods[2] == "kochle"
                else {"RG": 0.191, "PP": 0.132, "DF": 0.132, "FC": 0.170, "DH": 0.170}
            )
            if g not in nu_map:
                domain[:] = False
            if methods[2] == "srivastava":
                domain &= rho > 200
                if g == "RG":
                    domain &= rho <= 580
            ratios.append(nu_map.get(g, np.nan))
    density = np.stack(values, axis=1)
    if target == "density":
        out = density[:, 0]
    elif target == "elastic_modulus":
        out = moduli[0]
    elif target == "slab_weight_shear":
        angle = samples["angle"]
        physical &= np.isfinite(angle) & (angle >= 0) & (angle <= 90)
        out = (density * samples["thickness"] / 100 * 9.81).sum(axis=1) * np.sin(
            np.deg2rad(angle)
        )
    else:
        thickness = samples["thickness"] * 10
        ref = number(slab.layers[0].depth_top) * 10 + thickness.sum(axis=1) / 2
        out = np.zeros(n)
        for i, layer in enumerate(slab.layers):
            top = ref - number(layer.depth_top) * 10
            bottom = top - thickness[:, i]
            out += moduli[i] / (1 - ratios[i] ** 2) * (top**3 - bottom**3) / 3
    finite = np.isfinite(out) & np.all(np.isfinite(density) & (density > 0), axis=1)
    if target != "slab_weight_shear":
        finite &= out > 0
    return out, {
        "physical_input_failure": ~physical,
        "method_domain_failure": physical & ~domain,
        "numerical_failure": physical & domain & ~finite,
        "success": physical & domain & finite,
    }


def summarize(out, masks):
    values = out[masks["success"]]
    return {
        **{name: int(mask.sum()) for name, mask in masks.items()},
        "draws": len(out),
        "success_fraction": len(values) / len(out),
        "conditional_mean": float(values.mean()) if len(values) else None,
        "conditional_median": float(np.median(values)) if len(values) else None,
        "conditional_std": float(values.std(ddof=1)) if len(values) > 1 else None,
        "conditional_p16": float(np.quantile(values, 0.16)) if len(values) else None,
        "conditional_p84": float(np.quantile(values, 0.84)) if len(values) else None,
    }


def synthetic(grain="RG", rho=250, hardness="1F", size=1, layers=1):
    return Slab(
        layers=[
            Layer(
                depth_top=20 * i,
                thickness=ufloat(20, 1),
                density_measured=ufloat(rho, 0.1 * rho),
                grain_form=grain,
                hand_hardness=hardness,
                grain_size_avg=ufloat(size, 0.48 * size),
            )
            for i in range(layers)
        ],
        angle=ufloat(30, 2),
    )


def controls():
    layered = synthetic(layers=2)
    layered.layers[1].density_measured = ufloat(300, 30)
    cases = [
        ("linear_density", synthetic("FC"), "density", [("geldsetzer", "", "")]),
        (
            "nonlinear_density",
            synthetic(),
            "density",
            [("geldsetzer", "", ""), ("kim_jamieson_table2", "", "")],
        ),
        (
            "kim_t6_grain_size",
            synthetic("FC", size=2),
            "density",
            [("kim_jamieson_table6", "", "")],
        ),
        ("homogeneous_D11", synthetic(), "D11", [("data_flow", "wautier", "kochle")]),
        (
            "layered_D11",
            layered,
            "D11",
            [("data_flow", "wautier", "kochle"), ("data_flow", "bergfeld", "kochle")],
        ),
    ]
    for rho in [249, 250, 251]:
        cases.append(
            (
                f"kochle_breakpoint_{rho}",
                synthetic(rho=rho),
                "elastic_modulus",
                [("data_flow", "kochle", "")],
            )
        )
    for grain, lo, hi in [
        ("SH", 0.074, 0.191),
        ("RG", 0.162, 0.388),
        ("FC", 0.164, 0.505),
    ]:
        for label, fraction in [("lower", lo), ("upper", hi)]:
            cases.append(
                (
                    f"schottner_{grain}_{label}",
                    synthetic(grain, rho=fraction * 916.7),
                    "elastic_modulus",
                    [("data_flow", "schottner", "")],
                )
            )
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=20000)
    args = parser.parse_args()
    warnings.filterwarnings("ignore", message="Using UFloat objects with std_dev==0.*")
    cases = controls()
    summary = json.loads((args.results / "summary.json").read_text())
    records = pd.read_parquet(args.results / "attempts.parquet")
    selected = {row["slab_id"] for row in summary["D11"]["illustrations"]}
    kim = records[
        (records.target == "D11")
        & records.success
        & records.pathway.str.startswith("kim_jamieson_table6")
    ]
    if not kim.empty:
        selected.add(sorted(kim.slab_id)[0])
    manifest = json.loads((args.results / "input_manifest.json").read_text())
    files = {str(row["pit_id"]): row["filename"] for row in manifest}
    for slab_id in sorted(selected):
        pit_id = str(records[records.slab_id == slab_id].pit_id.iloc[0])
        pit = Pit.from_snow_pit(parse_caaml_file(str(args.data / files[pit_id])))
        slab = next(
            s for s in pit.create_slabs("ECTP_failure_layer") if s.slab_id == slab_id
        )
        methods = [
            tuple(p.split(" -> "))
            for p in sorted(
                records[
                    (records.slab_id == slab_id)
                    & (records.target == "D11")
                    & records.success
                ].pathway
            )
        ]
        cases.append((slab_id, slab, "D11", methods))
    results, inputs, paired = [], [], []
    engine = ExecutionEngine()
    for case_id, slab, target, pathways in cases:
        seed = SEED + int(hashlib.sha256(case_id.encode()).hexdigest()[:8], 16)
        inputs.append(
            {
                "case": case_id,
                "target": target,
                "seed": seed,
                "pit_id": slab.pit_id,
                "slab_id": slab.slab_id,
                "slope_degrees": {
                    "nominal": number(slab.angle),
                    "sigma": float(getattr(slab.angle, "std_dev", 0)),
                },
                "paths": pathways,
                "layers": [
                    {
                        "grain_form": layer.grain_form,
                        **{
                            f: {
                                "nominal": number(getattr(layer, f)),
                                "sigma": float(
                                    getattr(getattr(layer, f), "std_dev", 0)
                                ),
                            }
                            for f in [
                                "depth_top",
                                "thickness",
                                "density_measured",
                                "grain_size_avg",
                                "hand_hardness_index",
                            ]
                        },
                    }
                    for layer in slab.layers
                ],
            }
        )
        first = {
            path_key(r.methods_used): r
            for r in engine.execute_all(
                slab, target, config=ExecutionConfig(include_method_uncertainty=False)
            ).pathways.values()
        }
        for correlation in [0, 0.5, 1]:
            samples = sample_observations(slab, args.draws, correlation, seed)
            outputs = []
            for methods in pathways:
                out, masks = evaluate(slab, target, methods, samples)
                counts = summarize(out, masks)
                assert sum(counts[k] for k in masks) == args.draws
                key = " -> ".join(x for x in methods if x)
                ref = first[key]
                trace = next(
                    t
                    for t in ref.computation_trace
                    if t.parameter == target
                    and t.layer_index
                    == (0 if target in {"density", "elastic_modulus"} else None)
                )
                results.append(
                    {
                        "case": case_id,
                        "target": target,
                        "pathway": key,
                        "correlation": correlation,
                        "first_order_nominal": number(trace.output),
                        "first_order_sigma": float(
                            getattr(trace.output, "std_dev", float("nan"))
                        ),
                        "first_order_dependence": "independent layers",
                        **counts,
                    }
                )
                outputs.append((key, out, masks["success"]))
            for i in range(len(outputs)):
                for j in range(i + 1, len(outputs)):
                    a, b = outputs[i], outputs[j]
                    valid = a[2] & b[2]
                    diff = a[1][valid] - b[1][valid]
                    paired.append(
                        {
                            "case": case_id,
                            "correlation": correlation,
                            "pathway_a": a[0],
                            "pathway_b": b[0],
                            "joint_successful_draws": len(diff),
                            "conditional_difference_mean": (
                                float(diff.mean()) if len(diff) else None
                            ),
                            "conditional_difference_std": (
                                float(diff.std(ddof=1)) if len(diff) > 1 else None
                            ),
                        }
                    )
    pd.DataFrame(results).to_csv(args.results / "monte_carlo.csv", index=False)
    pd.DataFrame(paired).to_csv(args.results / "monte_carlo_paired.csv", index=False)
    write_json(args.results / "monte_carlo_cases.json", inputs)
    print(
        f"Monte Carlo: {len(results)} case/path/correlation summaries; {args.draws} draws each"
    )


if __name__ == "__main__":
    main()
