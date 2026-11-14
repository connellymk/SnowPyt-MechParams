"""Focused, reproducible Monte Carlo checks for the reviewer response.

Equations are independently written NumPy expressions. These experiments use
RG slabs, for which the 16 selected pathways share grain support. They are a
sensitivity analysis of assigned SDs, not an empirical error calibration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from uncertainties import ufloat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))
from notebook_utils import extract_d11  # noqa: E402
from snowpyt_mechparams.execution import ExecutionConfig, ExecutionEngine  # noqa: E402
from snowpyt_mechparams.models import Layer, Pit, Slab  # noqa: E402
from snowpyt_mechparams.snowpilot import parse_caaml_file  # noqa: E402

SEED = 20261010
E_METHODS = ["bergfeld", "kochle", "wautier", "schottner"]


def value(x):
    return float(getattr(x, "nominal_value", x))


def evaluate(x, depths, density_method, elastic_method, nu_method, nominal_low):
    """Return full equation, nominal-branch equation, physical and domain masks."""
    x = np.atleast_2d(x)
    n = len(depths)
    h, measured = x[:, :n], x[:, n:]
    physical = (h > 0).all(axis=1) & (measured > 0).all(axis=1)
    with np.errstate(invalid="ignore", over="ignore"):
        if density_method == "data_flow":
            rho = measured
            density_ok = np.ones(len(x), dtype=bool)
        elif density_method == "geldsetzer":
            rho = 154 + 1.51 * measured**3.15
            density_ok = ((measured >= 1) & (measured <= 5.33)).all(axis=1)
        else:
            rho = 91.8 * np.exp(0.27 * measured)
            density_ok = ((measured >= 0.67) & (measured <= 5.33)).all(axis=1)
        physical &= ((rho > 0) & (rho < 917)).all(axis=1)
        if elastic_method == "kochle":
            lower, upper = 0.0061 * np.exp(0.0396 * rho), 6.0457 * np.exp(0.011 * rho)
            e = np.where(rho < 250, lower, upper)
            local_e = np.where(nominal_low, lower, upper)
            e_ok = ((rho >= 150) & (rho <= 450)).all(axis=1)
        else:
            a, b, low, high = {
                "bergfeld": (6500, 4.4, 110, 363),
                "wautier": (7800, 2.34, 103, 544),
                "schottner": (4000, 4.6, 0, np.inf),
            }[elastic_method]
            e = local_e = a * (rho / 917) ** b
            e_ok = ((rho >= low) & (rho <= high)).all(axis=1)
        nu = 0.171 if nu_method == "kochle" else 0.191
        nu_ok = (
            np.ones(len(x), dtype=bool)
            if nu_method == "kochle"
            else ((rho > 200) & (rho <= 580)).all(axis=1)
        )
        zref = depths[0] * 10 + h.sum(axis=1, keepdims=True) * 5
        ztop = zref - np.asarray(depths)[None, :] * 10
        zbottom = ztop - h * 10
        geometry = (ztop**3 - zbottom**3) / (3 * (1 - nu**2))
        full = (e * geometry).sum(axis=1)
        local = (local_e * geometry).sum(axis=1)
    valid = physical & density_ok & e_ok & nu_ok
    crossing = (
        ((rho < 250) != nominal_low).any(axis=1)
        if elastic_method == "kochle"
        else np.zeros(len(x), dtype=bool)
    )
    return full, local, physical, valid, crossing


def draw_standard(rng, size, n_layers, distribution, correlation):
    """Exact marginal moments; uniform mixture has Pearson correlation c.

    Variable families (thickness, hardness/density) remain mutually independent.
    Shared-observer correlation is imposed across layers within each family.
    """
    pieces = []
    for _ in range(2):
        if distribution == "normal":
            independent = rng.standard_normal((size, n_layers))
            common = rng.standard_normal((size, 1))
            z = np.sqrt(1 - correlation) * independent + np.sqrt(correlation) * common
        else:
            independent = rng.uniform(-np.sqrt(3), np.sqrt(3), (size, n_layers))
            common = rng.uniform(-np.sqrt(3), np.sqrt(3), (size, 1))
            shared = rng.random((size, 1)) < correlation
            z = np.where(shared, common, independent)
        pieces.append(z)
    return np.concatenate(pieces, axis=1)


def run(output, draws):
    warnings.filterwarnings("ignore", message="Using UFloat objects with std_dev==0.*")
    engine, config = ExecutionEngine(), ExecutionConfig(
        include_method_uncertainty=False
    )
    cases = []
    for pit_id in [1057, 50003, 14909]:
        pit = Pit.from_snow_pit(
            parse_caaml_file(str(ROOT / f"examples/data/snowpits-{pit_id}-caaml.xml"))
        )
        slab = pit.create_slabs("ECTP_failure_layer")[0]
        cases.append(
            (f"observed_{pit_id}", slab, ["geldsetzer", "kim_jamieson_table2"])
        )
    cases.append(
        (
            "synthetic_multilayer",
            Slab(
                layers=[
                    Layer(
                        depth_top=d,
                        thickness=ufloat(h, 0.05 * h),
                        density_measured=ufloat(r, 0.1 * r),
                        grain_form="RG",
                    )
                    for d, h, r in [(0, 15, 210), (15, 20, 280), (35, 25, 350)]
                ],
                angle=35,
            ),
            ["data_flow"],
        )
    )
    for rho in [103, 150, 200, 249, 250, 251, 363, 450, 544]:
        cases.append(
            (
                f"synthetic_density_{rho}",
                Slab(
                    layers=[
                        Layer(
                            depth_top=0,
                            thickness=ufloat(30, 1.5),
                            density_measured=ufloat(rho, 0.1 * rho),
                            grain_form="RG",
                        )
                    ],
                    angle=35,
                ),
                ["data_flow"],
            )
        )
    rng = np.random.default_rng(SEED)
    rows, checks = [], []
    for name, slab, density_methods in cases:
        n = len(slab.layers)
        assert all(layer.grain_form[:2] == "RG" for layer in slab.layers)
        depths = [value(layer.depth_top) for layer in slab.layers]
        standard_draws = {}
        for dm in density_methods:
            inputs = [layer.thickness for layer in slab.layers] + [
                (
                    layer.density_measured
                    if dm == "data_flow"
                    else layer.hand_hardness_index
                )
                for layer in slab.layers
            ]
            mean = np.array([value(v) for v in inputs])
            sd = np.array([v.std_dev for v in inputs])
            r0 = (
                mean[n:]
                if dm == "data_flow"
                else (
                    154 + 1.51 * mean[n:] ** 3.15
                    if dm == "geldsetzer"
                    else 91.8 * np.exp(0.27 * mean[n:])
                )
            )
            for distribution in ["normal", "uniform"]:
                for correlation in [0.0, 0.5, 1.0]:
                    key = (distribution, correlation if n > 1 else 0.0)
                    if key not in standard_draws:
                        standard_draws[key] = draw_standard(
                            rng, draws, n, distribution, correlation if n > 1 else 0.0
                        )
                    samples = mean + sd * standard_draws[key]
                    cov = np.eye(2 * n)
                    for a in [0, n]:
                        cov[a : a + n, a : a + n] = correlation + (
                            1 - correlation
                        ) * np.eye(n)
                    cov *= np.outer(sd, sd)
                    for em in E_METHODS:
                        for nm in ["kochle", "srivastava"]:
                            kwargs = (depths, dm, em, nm, r0 < 250)
                            base, _, _, base_ok, _ = evaluate(mean, *kwargs)
                            # At the Kochle discontinuity, verify the derivative
                            # of the nominally selected branch, as uncertainties does.
                            gradient = []
                            for j in range(2 * n):
                                step = max(abs(mean[j]) * 1e-5, 1e-5)
                                plus, minus = mean.copy(), mean.copy()
                                plus[j] += step
                                minus[j] -= step
                                gradient.append(
                                    (
                                        evaluate(plus, *kwargs)[1][0]
                                        - evaluate(minus, *kwargs)[1][0]
                                    )
                                    / (2 * step)
                                )
                            gradient = np.asarray(gradient)
                            first_sd = float(np.sqrt(gradient @ cov @ gradient))
                            methods = {
                                "density": dm,
                                "elastic_modulus": em,
                                "poissons_ratio": nm,
                            }
                            result = engine.execute_single(
                                slab, "D11", methods, config=config
                            )
                            fw_mean, fw_sd = extract_d11(result)
                            if distribution == "normal" and correlation == 0:
                                assert bool(base_ok[0]) == bool(np.isfinite(fw_mean)), (
                                    name,
                                    methods,
                                )
                                if base_ok[0]:
                                    assert np.isclose(fw_mean, base[0], rtol=1e-10)
                                    assert np.isclose(fw_sd, first_sd, rtol=1e-6), (
                                        name,
                                        methods,
                                        fw_sd,
                                        first_sd,
                                    )
                                    checks.append(
                                        {
                                            "case": name,
                                            **methods,
                                            "framework_nominal": fw_mean,
                                            "independent_nominal": base[0],
                                            "framework_SD": fw_sd,
                                            "independent_SD": first_sd,
                                        }
                                    )
                            full, _, physical, valid, crossing = evaluate(
                                samples, *kwargs
                            )
                            physical &= np.isfinite(full)
                            valid &= np.isfinite(full)
                            y = full[valid]
                            rows.append(
                                {
                                    "case": name,
                                    **methods,
                                    "distribution": distribution,
                                    "interlayer_correlation": correlation,
                                    "draws": draws,
                                    "nominal_available": bool(base_ok[0]),
                                    "nominal_D11": float(base[0]),
                                    "first_order_SD": first_sd,
                                    "physical_draws": int(physical.sum()),
                                    "valid_draws": int(valid.sum()),
                                    "physical_failure_fraction": 1
                                    - float(physical.mean()),
                                    "domain_failure_fraction": float(
                                        (physical & ~valid).mean()
                                    ),
                                    "Kochle_breakpoint_crossing_fraction": float(
                                        (physical & crossing).mean()
                                    ),
                                    "conditional_MC_mean": (
                                        float(np.mean(y)) if len(y) else None
                                    ),
                                    "conditional_MC_SD": (
                                        float(np.std(y, ddof=1)) if len(y) > 1 else None
                                    ),
                                    "conditional_p16": (
                                        float(np.quantile(y, 0.16)) if len(y) else None
                                    ),
                                    "conditional_p50": (
                                        float(np.quantile(y, 0.5)) if len(y) else None
                                    ),
                                    "conditional_p84": (
                                        float(np.quantile(y, 0.84)) if len(y) else None
                                    ),
                                }
                            )
        print(f"Completed {name}", flush=True)
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output / "uncertainty_sensitivity.csv", index=False)
    pd.DataFrame(checks).to_csv(output / "D11_independent_checks.csv", index=False)
    observed = pd.DataFrame(rows)
    observed = observed[
        observed.case.str.startswith("observed")
        & (observed.distribution == "normal")
        & (observed.interlayer_correlation == 0)
    ]
    result = {
        "seed": SEED,
        "draws_per_scenario": draws,
        "scenarios": len(rows),
        "independent_D11_checks": len(checks),
        "observed_independent_normal_domain_failure_fraction_range": [
            float(observed.domain_failure_fraction.min()),
            float(observed.domain_failure_fraction.max()),
        ],
    }
    conditional_ratio = observed.conditional_MC_SD / observed.first_order_SD
    result["observed_independent_normal_conditional_SD_ratio_range"] = [
        float(conditional_ratio.min()),
        float(conditional_ratio.max()),
    ]
    (output / "uncertainty_summary.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--draws", type=int, default=100000)
    args = p.parse_args()
    run(args.output, args.draws)
