"""Reproduce reviewer evidence without writing outside this repository.

Usage: .venv/bin/python paper_analysis/run_review.py [--smoke]
The full run is sequential so benchmark phases do not contend with each other.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import tempfile
import time

from review_metrics import write_json

BASELINE = "c8b712e93fe219c9c5dd71e6a5a8a3a6d947866c"
ROOT = Path(__file__).resolve().parents[1]


def hardware_summary():
    hardware = {
        "machine": platform.machine(),
        "logical_cpus": os.cpu_count(),
        "platform": platform.platform(),
    }
    if platform.system() == "Darwin":
        try:
            raw = json.loads(
                subprocess.check_output(
                    ["system_profiler", "SPHardwareDataType", "-json"], timeout=15
                )
            )["SPHardwareDataType"][0]
            # Whitelist performance-relevant fields; exclude serial and account identifiers.
            hardware.update(
                {
                    k: raw.get(k)
                    for k in [
                        "machine_name",
                        "machine_model",
                        "chip_type",
                        "number_processors",
                        "physical_memory",
                    ]
                }
            )
        except (OSError, subprocess.SubprocessError, ValueError, KeyError):
            hardware["details"] = "unavailable"
    return hardware


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="First 1,000 files and 1,000 Monte Carlo draws; separate outputs",
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=["compute", "diagnostics", "mc", "render"],
        default=["compute", "diagnostics", "mc", "render"],
    )
    args = parser.parse_args()
    output = ROOT / "paper_analysis/results" / ("smoke" if args.smoke else "")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(ROOT / ".matplotlib")
    limit = ["--limit", "1000"] if args.smoke else []
    timings = {}

    def run(script, arguments, source=None):
        child_env = env.copy()
        if source:
            child_env["PYTHONPATH"] = str(source / "src")
        started = time.perf_counter()
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "paper_analysis" / script),
                *map(str, arguments),
            ],
            cwd=ROOT,
            env=child_env,
            check=True,
        )
        timings[script + " " + " ".join(map(str, arguments))] = (
            time.perf_counter() - started
        )

    if "compute" in args.steps:
        archive = subprocess.check_output(["git", "archive", BASELINE, "src"], cwd=ROOT)
        with tempfile.TemporaryDirectory(prefix="snowpyt-review-baseline-") as tmp:
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                # Trusted, pinned git tree; use modern safe extraction when available.
                tar.extractall(tmp, filter="data")
            run(
                "review_compute.py",
                [
                    "--data",
                    ROOT / "examples/data",
                    "--output",
                    output / "baseline",
                    *limit,
                ],
                Path(tmp),
            )
        for label in ["corrected", "contained"]:
            extra = ["--benchmark"] if label == "corrected" else ["--contained"]
            run(
                "review_compute.py",
                [
                    "--data",
                    ROOT / "examples/data",
                    "--output",
                    output / label,
                    *limit,
                    *extra,
                ],
            )
    if "diagnostics" in args.steps:
        archive = subprocess.check_output(["git", "archive", BASELINE, "src"], cwd=ROOT)
        with tempfile.TemporaryDirectory(prefix="snowpyt-review-baseline-") as tmp:
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(tmp, filter="data")
            run(
                "review_diagnostics.py",
                [
                    "--data",
                    ROOT / "examples/data",
                    "--output",
                    output / "baseline",
                    *limit,
                ],
                Path(tmp),
            )
        for label in ["corrected", "contained"]:
            run(
                "review_diagnostics.py",
                [
                    "--data",
                    ROOT / "examples/data",
                    "--output",
                    output / label,
                    *limit,
                    *(["--contained"] if label == "contained" else []),
                ],
            )
        manifest = (output / "corrected/input_manifest.json").read_bytes()
        (output / "input_manifest.json.gz").write_bytes(
            gzip.compress(manifest, mtime=0)
        )
    if "mc" in args.steps:
        run(
            "review_monte_carlo.py",
            [
                "--data",
                ROOT / "examples/data",
                "--results",
                output / "corrected",
                "--draws",
                1000 if args.smoke else 20000,
            ],
        )
    if "render" in args.steps:
        run("review_report.py", ["--results", output])
    files = sorted(
        set((ROOT / "src").rglob("*.py"))
        | set((ROOT / "paper_analysis").glob("*.py"))
        | set((ROOT / "examples").glob("*.py"))
    )
    metadata = {
        "baseline_revision": BASELINE,
        "working_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_modified": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            )
        ),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files
        },
        "steps": args.steps,
        "hardware": hardware_summary(),
        "dependency_versions": {
            d.metadata["Name"]: d.version
            for d in importlib.metadata.distributions()
            if d.metadata["Name"]
        },
        "cache_conditions": "Fresh compute processes and engine per benchmark repeat; OS file cache uncontrolled and warmed by prior runs; no cache flush.",
        "smoke": args.smoke,
        "step_seconds": timings,
        "measurement_uncertainty_only": True,
        "grain_size_sd_fraction": 0.48,
        "random_seed": 20261114,
        "draws": 1000 if args.smoke else 20000,
        "correlations": [0, 0.5, 1],
        "correlation_scope": "multilayer D11 cases only; single-layer cases use 0",
        "monte_carlo_scope": "limited propagation assessment; production engine unchanged",
        "data_selection": "all sorted examples/data/*.xml; no new quality or wetness filtering",
        "figure_export": "repository local; no implicit external copying",
    }
    # Preserve metadata for partial reruns without concealing which stages ran.
    previous = output / "run_metadata.json"
    if previous.exists():
        old = json.loads(previous.read_text())
        metadata["step_seconds"] = {**old.get("step_seconds", {}), **timings}
    write_json(previous, metadata)
    print(f"Reviewer evidence written to {output}")


if __name__ == "__main__":
    main()
