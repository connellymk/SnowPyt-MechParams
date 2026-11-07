"""Check separate statement/branch thresholds per method module AND function.

Run pytest with --cov-branch --cov-report=json:coverage.json first, then:
    .venv/bin/python tools/check_method_coverage.py coverage.json
Requires a coverage.py JSON report with function detail (verified with 7.13.4).
"""

import argparse
import json
from pathlib import Path


def check_report(report, root):
    if not report["meta"].get("branch_coverage"):
        raise ValueError("Branch coverage must be enabled")
    sources = sorted((root / "src/snowpyt_mechparams/methods").rglob("*.py"))
    sources.append(root / "src/snowpyt_mechparams/execution/dispatcher.py")
    failures = []
    functions_checked = 0
    for source in sources:
        relative = source.relative_to(root).as_posix()
        entry = report["files"].get(relative) or report["files"].get(str(source))
        if entry is None:
            failures.append(f"{relative}: absent from coverage report")
            continue
        if "functions" not in entry:
            failures.append(f"{relative}: no function detail; upgrade coverage.py")
            continue
        scopes = [(relative, entry["summary"])]
        for name, function in entry["functions"].items():
            if name:
                scopes.append((f"{relative}:{name}", function["summary"]))
                functions_checked += 1
        for label, summary in scopes:
            for kind, hit, total in [
                ("statement", "covered_lines", "num_statements"),
                ("branch", "covered_branches", "num_branches"),
            ]:
                # Integer comparison enforces strictly >98%, without rounding.
                if summary[total] and 100 * summary[hit] <= 98 * summary[total]:
                    failures.append(
                        f"{label}: {kind} {summary[hit]}/{summary[total]} <=98%"
                    )
        summary = entry["summary"]
        print(
            f"{relative}: statements {summary['covered_lines']}/{summary['num_statements']}; "
            f"branches {summary['covered_branches']}/{summary['num_branches']}"
        )
    return failures, len(sources), functions_checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    failures, modules, functions = check_report(
        report, Path(__file__).resolve().parents[1]
    )
    if failures:
        raise SystemExit("\n".join(failures))
    print(
        f"PASS: {modules} modules and {functions} named functions each exceed 98% "
        "statement and branch coverage (zero-branch functions are vacuous)."
    )


if __name__ == "__main__":
    main()
