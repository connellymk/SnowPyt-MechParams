# Code Review Report

**Date:** 2026-03-16
**Branch:** mkc/add-stability-criterion → main
**PR:** [#5](https://github.com/connellymk/SnowPyt-MechParams/pull/5) — Implement stability criterion
**Files Changed:** 5 in `src/snowpyt_mechparams/graph/` (+131 / -43), focused review scope

---

## Overall Rating: B

| Metric | Count |
|--------|-------|
| Critical Issues | 0 |
| Required Improvements | 4 |
| Recommendations | 3 |

---

## Required Improvements *(should fix before merge)*

**[REQUIRED] `graph/__init__.py`:49–78** — *New nodes not exported from the public API*
> **What:** `parameter_graph.py` defines and exports 11 new names in its `__all__` (`G_c`, `G_Ic`, `G_IIc`, `sigma_c`, `tau_c`, `sigma_comp`, `g_delta`, `s_r`, `s_sk`, `merge_weac_inputs`, `merge_roch_inputs`, `WEAK_LAYER_PARAMS`, `STABILITY_PARAMS`). None of them are re-exported from `graph/__init__.py`. Any downstream code doing `from snowpyt_mechparams.graph import tau_c` will get an `ImportError`.
> **Why:** The module boundary is the public API. Everything in `parameter_graph.__all__` that isn't accessible via `graph/__init__.py` is silently inaccessible to users and other modules.
> **Fix:** Add all new names to the imports and `__all__` in `graph/__init__.py`, mirroring the pattern used for the existing slab-parameter exports.

---

**[REQUIRED] `graph/visualize.py`:44–68 and 186–348** — *New node levels fall through to wrong category; new stability edges not rendered*
> **What:** `_classify_node` returns `"layer_calc"` as the default for any node that doesn't match root/measured/merge/slab. Nodes with `level="weak_layer"` and `level="stability_model"` (g_delta, s_r, s_sk, G_c, tau_c, …) are silently assigned to `"layer_calc"` and styled green. Additionally, the hard-coded edge filter in `generate_mermaid_diagram` (lines 334–341) lists specific node names for "slab-level calculations"; the stability merge nodes (`merge_weac_inputs`, `merge_roch_inputs`) and their downstream edges are outside both the slab section filter and the categorical sections, so they produce **no rendered edges** in the diagram — the stability output nodes will appear as disconnected singletons.
> **Why:** The Mermaid diagram is used in the README and docs. Disconnected nodes and wrong styling would be misleading to anyone using the diagram to understand the graph structure.
> **Fix:** (1) Add `weak_layer` and `stability_model` branches to `_classify_node`. (2) Add corresponding keys to `node_categories` in `generate_mermaid_diagram`. (3) Replace the hard-coded name-list edge filters with a general edge-rendering pass (iterate all edges, emit each once) rather than per-section name sets that break whenever a new node is added.

---

**[REQUIRED] `graph/structures.py`:216** — *`_node_index` cache field missing `compare=False`*
> **What:** `_node_index` is declared as `field(default_factory=dict, init=False, repr=False)` but without `compare=False`. Python's dataclass-generated `__eq__` includes all fields unless `compare=False` is set. The index is a derived cache of `nodes`; it is not part of the logical identity of a `Graph`.
> **Why:** Two `Graph` instances built from identical nodes/edges but compared before `__post_init__` populates the index (e.g., during pickling round-trips or partial construction) could produce unexpected equality results. More importantly, the field communicates wrong intent to future readers.
> **Fix:** `_node_index: Dict[str, Node] = field(default_factory=dict, init=False, repr=False, compare=False)`

---

**[REQUIRED] `tests/test_graph.py` and `tests/test_graph_visualization.py`** — *No tests for the new node types*
> **What:** `test_graph.py` has zero coverage for the newly added weak-layer and stability-model nodes. The following are completely untested:
> - Weak-layer nodes exist in graph with correct `level="weak_layer"`
> - Stability nodes (`g_delta`, `s_r`, `s_sk`) exist with `level="stability_model"`
> - `WEAK_LAYER_PARAMS` and `STABILITY_PARAMS` frozensets contain the expected members
> - `merge_weac_inputs` has all 10 required inputs; `merge_roch_inputs` has `density` and `tau_c`
> - `graph.weak_layer_params` and `graph.stability_params` properties return non-empty frozensets
> - `_classify_node` handles `weak_layer`/`stability_model` levels (once the fix above is applied)
> **Why:** This is the same level of graph test that exists for layer and slab nodes. Skipping it means the Roch and WEAC graph wiring is only verified implicitly by the smoke tests, which don't exercise graph structure directly.
> **Fix:** Add a `TestWeakLayerNodes` class and a `TestStabilityNodes` class to `test_graph.py` mirroring the existing `TestLayerParameterNodes`/`TestSlabParameterNodes` pattern. Update `test_graph_visualization.py` to assert that `_classify_node` returns the right category for the new levels once fixed.

---

## Recommendations *(worth doing, not blocking)*

**[REC] `tests/test_graph.py`:289,311,337** — *Stale references to `definitions.py`*
> Three strings in `TestGraphDispatcherConsistency` still say "graph/definitions.py". Update to "graph/parameter_graph.py" so the error messages point developers to the right file.

---

**[REC] `graph/visualize.py`:218–222, 238–239** — *Hard-coded merge-node name sets will drift again*
> The layer/slab merge bucketing uses an explicit `set` of node parameter strings. It already broke implicitly for the new nodes (see Required #2). Even after fixing the stability categories, the slab-merge bucket is `node_categories["merge"] - layer_merges`, which silently includes anything that isn't explicitly listed as a layer merge. Consider driving this from node-level metadata instead: a merge node's "group" could be inferred from its downstream consumers' levels, or the `GraphBuilder` could accept an optional `group` tag at construction time.

---

**[REC] `graph/structures.py`:305–322** — *`add_node` membership check is O(n)*
> `if node not in self.nodes` scans the list linearly. Now that `_node_index` exists, the check could be `if node.parameter not in self._node_index`. Minor for graphs of this size but trivially fixable.

---

## Summary

The core structural work here is clean and well-motivated. Renaming `definitions.py` to `parameter_graph.py` is the right call and all the reference updates are complete. The `Graph._node_index` addition improves `get_node` from O(n) to O(1) and is implemented correctly in `__post_init__` and `add_node`. The two new `NodeLevel` values are properly threaded through the `NodeLevel` type alias, `Node.__post_init__` validation, and the `Graph` property accessors — that's a correct, self-consistent extension of the type system.

The main gap is that the graph module's **public surface** (the `__init__.py`) wasn't updated to expose the new nodes, and the **visualization** (which was presumably working before) breaks silently for the new types — new nodes appear with wrong styling and no edges. These are both Required fixes before merge, not because they'd cause a calculation error, but because they leave the module in an internally inconsistent state that will confuse the next person touching this code. The missing tests follow directly from the same oversight.
