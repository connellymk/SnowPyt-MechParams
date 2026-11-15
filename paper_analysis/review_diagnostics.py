"""Reconstruct raw provenance and export reproducible coverage diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import math
import time
import warnings

import pandas as pd

from review_audit import audit_profile, assign_contained
from review_metrics import write_json, number
from snowpyt_mechparams.models import Pit
from snowpyt_mechparams.snowpilot import parse_caaml_file
from loss_analysis_utils import analyze_losses, LossAnalysis


def load_diagnostics(folder, target):
    """Present the canonical runner's results, including raw-processing provenance."""
    folder = Path(folder)
    histogram = pd.read_csv(folder / f"{target}_histogram.csv", index_col=0).iloc[:, 0]
    tables = {
        name: pd.read_csv(folder / f"{target}_{name}.csv", keep_default_na=False)
        for name in ["stages", "reasons", "method_summary", "coverage"]
    }
    for column in ["lower", "upper", "observed_min", "observed_max"]:
        tables["reasons"][column] = pd.to_numeric(
            tables["reasons"][column], errors="coerce"
        )
    return LossAnalysis(
        target=target,
        n_slabs=int(histogram.sum()),
        n_pathways=len(tables["coverage"]),
        histogram=histogram,
        attempts=pd.read_parquet(folder / f"{target}_loss_attempts.parquet"),
        **tables,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--limit", type=int)
    p.add_argument("--contained", action="store_true")
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore", message="Using UFloat objects with std_dev==0.*")
    started = time.perf_counter()
    manifests, profiles, observations, layer_rows, failures, slabs = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    provenance = []
    paths = sorted(args.data.glob("*.xml"))
    if args.limit:
        paths = paths[: args.limit]
    for path in paths:
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = {"filename": path.name, "sha256": checksum, "pit_id": None}
        manifests.append(manifest)
        try:
            raw = parse_caaml_file(str(path))
            pit = Pit.from_snow_pit(raw)
            manifest["pit_id"] = pit.pit_id
        except Exception as exc:
            failures.append({"filename": path.name, "error": str(exc)})
            continue
        profile, obs, layers = audit_profile(raw, pit, path.name, checksum)
        profiles.append(profile)
        if args.contained:
            assign_contained(raw, pit)
        pit_slabs = pit.create_slabs("ECTP_failure_layer")
        layer_indices = {id(layer): i for i, layer in enumerate(pit.layers)}
        for slab in pit_slabs:
            keys = [f"{path.name}:{layer_indices[id(layer)]}" for layer in slab.layers]
            provenance.append(
                {
                    "slab_id": slab.slab_id,
                    "pit_id": slab.pit_id,
                    "source_layers": keys,
                    "stratigraphy": "|".join(keys),
                }
            )
        member_ids = {id(layer) for slab in pit_slabs for layer in slab.layers}
        for layer, row in zip(pit.layers, layers, strict=True):
            layer._review_density_processing_excluded = row["processing_excluded"]
            row.update(
                pit_id=pit.pit_id,
                filename=path.name,
                in_ectp_slab=id(layer) in member_ids,
            )
            row["primary_density_available"] = layer.density_measured is not None
            rho = number(layer.density_measured)
            row["positive_finite_density"] = math.isfinite(rho) and rho > 0
            layer_rows.append(row)
        for row in obs:
            row.update(pit_id=pit.pit_id, filename=path.name)
            observations.append(row)
        slabs.extend(pit_slabs)
    write_json(args.output / "input_manifest.json", manifests)
    write_json(args.output / "profile_audit.json", profiles)
    layer_df, obs_df = pd.DataFrame(layer_rows), pd.DataFrame(observations)
    pd.DataFrame(provenance).to_parquet(
        args.output / "slab_provenance.parquet", index=False
    )
    layer_df.to_parquet(args.output / "layer_audit.parquet", index=False)
    obs_df.to_parquet(args.output / "density_observation_audit.parquet", index=False)
    issues, exclusions = Counter(), Counter()
    for row in profiles:
        issues.update(row["issues"])
        exclusions.update(row["exclusions"])
    pit_counts = Counter(s.pit_id for s in slabs)
    excluded = layer_df[layer_df.processing_excluded]
    affected_layer_ids = {
        (r.filename, int(r.layer_index)) for r in excluded.itertuples()
    }
    affected_slabs = sum(
        any(
            getattr(layer, "_review_density_processing_excluded", False)
            and layer.density_measured is None
            for layer in s.layers
        )
        for s in slabs
    )
    source_ids = Counter(r["pit_id"] for r in profiles)
    checksums = Counter(r["sha256"] for r in manifests)
    summary = {
        "files": len(paths),
        "parsed_pits": len(profiles),
        "parse_failures": failures,
        "duplicate_file_content_excess": sum(n - 1 for n in checksums.values()),
        "duplicate_pit_id_excess": sum(n - 1 for n in source_ids.values()),
        "layers": len(layer_df),
        "density_observations": len(obs_df),
        "pits_with_density_observations": obs_df.pit_id.nunique(),
        "layers_with_density_present": int(layer_df.primary_density_available.sum()),
        "layers_with_positive_finite_density": int(
            layer_df.positive_finite_density.sum()
        ),
        "pits_with_positive_finite_density": layer_df.loc[
            layer_df.positive_finite_density, "pit_id"
        ].nunique(),
        "slabs_with_all_positive_finite_density": sum(
            all(
                math.isfinite(number(layer.density_measured))
                and number(layer.density_measured) > 0
                for layer in s.layers
            )
            for s in slabs
        ),
        "slabs_with_any_positive_finite_density": sum(
            any(
                math.isfinite(number(layer.density_measured))
                and number(layer.density_measured) > 0
                for layer in s.layers
            )
            for s in slabs
        ),
        "partial_layer_assignments": int(
            ((layer_df.sampled_fraction > 0) & (layer_df.sampled_fraction < 1)).sum()
        ),
        "slabs": len(slabs),
        "contributing_pits": len(pit_counts),
        "pits_with_multiple_slabs": sum(n > 1 for n in pit_counts.values()),
        "slabs_per_pit_distribution": dict(Counter(pit_counts.values())),
        "repeated_stratigraphies_within_pit": sum(
            r["repeated_stratigraphies_within_pit"] for r in profiles
        ),
        "issues": dict(issues),
        "slab_exclusions": dict(exclusions),
        "layer_assignment_policy_counts": layer_df.policy.value_counts().to_dict(),
        "multiple_exact_layers": int((layer_df.raw_exact_count > 1).sum()),
        "processing_excluded_layers": len(affected_layer_ids),
        "processing_excluded_pits": excluded.pit_id.nunique(),
        "slabs_with_unavailable_processed_density": affected_slabs,
        "density_observations_exact": sum(
            bool(r["exact_layers"]) for r in observations
        ),
        "density_observations_contained": sum(
            bool(r["containers"]) for r in observations
        ),
        "density_observations_crossing": sum(
            r["boundary_crossing"] for r in observations
        ),
        "density_observations_ambiguous": sum(r["ambiguous"] for r in observations),
        "invalid_density_observations": sum(not r["valid"] for r in observations),
        "observations_with_unusable_interval": sum(
            r["invalid_interval"] for r in observations
        ),
        "observations_with_invalid_density_value": sum(
            r["invalid_density"] for r in observations
        ),
        "point_observations_located_in_layer": sum(
            bool(r["point_layers"]) for r in observations
        ),
        "density_observations_without_overlap": sum(
            not r["overlap_layers"] for r in observations
        ),
        "audit_seconds": time.perf_counter() - started,
    }
    write_json(args.output / "audit_summary.json", summary)
    # Categories above overlap; only policy counts are a partition of layers.
    for target in ["slab_weight_shear", "slab_weight_shear_with_elasticity", "D11"]:
        started = time.perf_counter()
        result = analyze_losses(slabs, target, progress=True)
        calculated = pd.read_csv(args.output / "coverage.csv")
        expected = (
            calculated[calculated.target == target]
            .set_index("pathway")
            .successful_slabs.to_dict()
        )
        actual = {
            " -> ".join(
                str(x) for x in (r.density_method, r.emod_method, r.nu_method) if x
            ): int(r.successful_slabs)
            for r in result.coverage.itertuples()
        }
        assert (
            actual == expected
        ), "Diagnostics disagree with independently executed coverage."
        assert result.histogram.sum() == len(slabs)
        for name in ["stages", "reasons", "method_summary", "coverage"]:
            getattr(result, name).to_csv(
                args.output / f"{target}_{name}.csv", index=False
            )
        result.histogram.to_csv(args.output / f"{target}_histogram.csv")
        result.attempts.to_parquet(
            args.output / f"{target}_loss_attempts.parquet", index=False
        )
        partition = (
            result.attempts[~result.attempts.success]
            .groupby(["pathway", "first_failed_step", "failure_reason_classes"])
            .size()
            .reset_index(name="lost_attempts")
        )
        assert partition.lost_attempts.sum() + result.attempts.success.sum() == len(
            result.attempts
        )
        partition.to_csv(
            args.output / f"{target}_first_failure_classes.csv", index=False
        )
        summary[f"{target}_diagnostics_seconds"] = time.perf_counter() - started
    write_json(args.output / "audit_summary.json", summary)


if __name__ == "__main__":
    main()
