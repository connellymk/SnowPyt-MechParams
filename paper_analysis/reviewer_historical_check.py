"""Identify the source of stale D11 counts without changing production policy.

The October 2026 dispatcher fix removed fallback to a measured density after an
empirical density method failed. Temporarily reconstruct that historical behavior
only in this diagnostic process and report the affected records explicitly.
"""

from pathlib import Path
import json
import sys
import warnings

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))
from notebook_utils import extract_d11, finite_positive, pathway_key  # noqa: E402
from snowpyt_mechparams.execution import ExecutionConfig, ExecutionEngine  # noqa: E402
import snowpyt_mechparams.execution.dispatcher as dispatcher  # noqa: E402
from snowpyt_mechparams.models import Pit  # noqa: E402
from snowpyt_mechparams.snowpilot import parse_caaml_file  # noqa: E402


def run(out):
    warnings.filterwarnings("ignore", message="Using UFloat objects with std_dev==0.*")
    matching = pd.read_csv(out / "density_matching.csv.gz", dtype={"pit_id": str})
    ids = set(matching.loc[matching.exact_density, "pit_id"])
    manifest = pd.read_csv(out / "input_manifest.csv.gz", dtype={"pit_id": str})
    rows = []
    original = dispatcher._resolve_density
    config = ExecutionConfig(include_method_uncertainty=False)
    engine = ExecutionEngine()
    try:
        for file in manifest.loc[manifest.pit_id.isin(ids), "file"]:
            pit = Pit.from_snow_pit(
                parse_caaml_file(str(ROOT / "examples/data" / file))
            )
            for slab in pit.create_slabs("ECTP_failure_layer"):
                dispatcher._resolve_density = original
                current = engine.execute_all(slab, "D11", config=config)
                dispatcher._resolve_density = lambda layer: (
                    layer.density_calculated
                    if layer.density_calculated is not None
                    else layer.density_measured
                )
                historical = engine.execute_all(slab, "D11", config=config)
                for key, old in historical.pathways.items():
                    new = current.pathways[key]
                    ov, _ = extract_d11(old)
                    nv, _ = extract_d11(new)
                    if finite_positive(ov) and not finite_positive(nv):
                        rows.append(
                            {
                                "slab_id": slab.slab_id,
                                "pit_id": slab.pit_id,
                                "pathway": pathway_key(old.methods_used),
                                "historical_D11": ov,
                                "grain_parents": ",".join(
                                    sorted(
                                        {
                                            (layer.grain_form or "")[:2]
                                            for layer in slab.layers
                                        }
                                    )
                                ),
                            }
                        )
    finally:
        dispatcher._resolve_density = original
    changed = pd.DataFrame(rows)
    changed.to_csv(out / "historical_density_fallback.csv", index=False)
    df = pd.read_csv(out / "D11_attempts.csv.gz")
    reconstructed = df.copy()
    affected = set(zip(changed.slab_id, changed.pathway))
    restored = pd.Series(
        [(s, p) in affected for s, p in zip(df.slab_id, df.pathway)], index=df.index
    )
    reconstructed.loc[restored, "success"] = True
    # Reconstruct the pre-PP notebook as well as the old density fallback.
    reconstructed.loc[
        (reconstructed.emod_method == "wautier")
        & reconstructed.grain_parents.str.contains("PP"),
        "success",
    ] = False
    top = pd.read_csv(out / "D11_coverage.csv").head(16).pathway
    count = (
        reconstructed[reconstructed.pathway.isin(top)]
        .groupby("slab_index")
        .success.sum()
    )
    summary = {
        "fallback_only_added_attempts": len(changed),
        "affected_slabs": changed.slab_id.nunique(),
        "reconstructed_saved_notebook_successful_D11_attempts": int(
            reconstructed.success.sum()
        ),
        "reconstructed_saved_notebook_D11_union_slabs": int(
            (reconstructed.groupby("slab_index").success.sum() > 0).sum()
        ),
        "reconstructed_saved_notebook_common_slabs": int((count == 16).sum()),
    }
    (out / "historical_check.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run(Path(sys.argv[1]))
