"""Execute baseline/corrected methods in isolated Python processes.

The orchestrator sets PYTHONPATH to a pinned source tree for the baseline.
No method overrides or production policy switches are used to emulate old results.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import platform
import time
import warnings
from pathlib import Path

import pandas as pd

from review_metrics import (
    number,
    path_key,
    coverage_summary,
    d11_comparison,
    write_json,
)
from snowpyt_mechparams.execution import ExecutionEngine, ExecutionConfig
from snowpyt_mechparams.models import Pit
from snowpyt_mechparams.snowpilot import parse_caaml_file

TARGETS = ("slab_weight_shear", "slab_weight_shear_with_elasticity", "D11")


def calculate(slabs, progress=False):
    engine = ExecutionEngine()
    config = ExecutionConfig(include_method_uncertainty=False)
    rows = []
    for i, slab in enumerate(slabs):
        for target in TARGETS:
            results = engine.execute_all(slab, target, config=config)
            for result in results.pathways.values():
                trace = next(
                    t
                    for t in result.computation_trace
                    if t.parameter == target and t.layer_index is None
                )
                value = number(trace.output)
                sigma = float(getattr(trace.output, "std_dev", 0))
                success = bool(
                    result.success
                    and pd.notna(value)
                    and abs(value) != float("inf")
                    and pd.notna(sigma)
                    and sigma != float("inf")
                    and (target != "D11" or value > 0)
                )
                rows.append(
                    (
                        target,
                        slab.slab_id,
                        slab.pit_id,
                        path_key(result.methods_used),
                        success,
                        value if success else float("nan"),
                        sigma if success else float("nan"),
                        len(slab.layers),
                        ",".join(
                            sorted(
                                set(
                                    (layer.grain_form or "")[:2]
                                    for layer in slab.layers
                                )
                            )
                        ),
                    )
                )
        if progress and (i + 1) % 1000 == 0:
            print(f"Executed {i + 1:,}/{len(slabs):,} slabs", flush=True)
    return pd.DataFrame(
        rows,
        columns=[
            "target",
            "slab_id",
            "pit_id",
            "pathway",
            "success",
            "value",
            "sigma",
            "n_layers",
            "grain_forms",
        ],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--contained", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore", message="Using UFloat objects with std_dev==0.*")
    started = time.perf_counter()
    pits, failures = [], []
    paths = sorted(args.data.glob("*.xml"))
    if args.limit:
        paths = paths[: args.limit]
    for p in paths:
        try:
            raw = parse_caaml_file(str(p))
            pit = Pit.from_snow_pit(raw)
            if args.contained:
                from review_audit import assign_contained

                assign_contained(raw, pit)
            pits.append(pit)
        except Exception as exc:
            failures.append({"file": p.name, "error": str(exc)})
    slabs = [s for p in pits for s in p.create_slabs("ECTP_failure_layer")]
    if args.limit is None:
        assert (
            len(paths) == len(pits) == 50_278
        ), "Pinned input cohort changed; inspect the manifest."
        assert len(slabs) == 14_776, "Pinned ECTP selection changed."
    assert len({s.slab_id for s in slabs}) == len(slabs), "Slab IDs are not unique."
    parsing_seconds = time.perf_counter() - started
    print(f"Parsed {len(pits):,} pits; {len(slabs):,} slabs", flush=True)
    started = time.perf_counter()
    records = calculate(slabs, progress=True)
    execution_seconds = time.perf_counter() - started
    records.to_parquet(args.output / "attempts.parquet", index=False)
    stats, coverage = coverage_summary(records)
    coverage.to_csv(args.output / "coverage.csv", index=False)
    d11, per_slab, common = d11_comparison(records)
    per_slab.to_csv(args.output / "d11_per_slab.csv", index=False)
    common.to_csv(args.output / "d11_common.csv", index=False)
    write_json(
        args.output / "summary.json",
        {
            "pits": len(pits),
            "slabs": len(slabs),
            "parse_failures": failures,
            "contributing_pits": len({s.pit_id for s in slabs}),
            "coverage": stats,
            "D11": d11,
            "parsing_seconds": parsing_seconds,
            "execution_seconds": execution_seconds,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "dependencies": {
                p: importlib.metadata.version(p)
                for p in ["numpy", "pandas", "scipy", "uncertainties", "snowpylot"]
            },
        },
    )
    pd.DataFrame(
        [
            {
                "slab_id": s.slab_id,
                "pit_id": s.pit_id,
                "test_index": s.test_result_index,
            }
            for s in slabs
        ]
    ).to_csv(args.output / "slabs.csv", index=False)
    if args.benchmark:
        timing = []
        ordered = sorted(slabs, key=lambda s: s.slab_id)
        for n in [100, 1000]:
            for repeat in range(3):
                t = time.perf_counter()
                calculate(ordered[:n])
                timing.append(
                    {
                        "slabs": min(n, len(slabs)),
                        "repeat": repeat + 1,
                        "seconds": time.perf_counter() - t,
                    }
                )
        write_json(
            args.output / "benchmarks.json",
            {
                "runs": timing,
                "cache_policy": "fresh engine per run; execute_all shares branches within slab",
            },
        )
    print(f"Complete: {args.output}", flush=True)


if __name__ == "__main__":
    main()
