# Plan: Remove Weak Layer Parameters, Add Slab Elasticity Node

## Context
The project is shifting focus from computing weak-layer fracture/strength parameters to analyzing the slab input parameters required for Roch and WEAC stability criteria. Weak-layer parameters (G_c, G_Ic, G_IIc, σ_c, τ_c, σ_comp) are being replaced by a single `weak_layer_info*` placeholder node that signals those inputs are currently unavailable. A new `slab_elasticity_parameters` merge node (E + ν) becomes the primary target for coverage analysis in the updated notebook.

---

## Step 1: Remove `weak_layer_parameters/` directory

Delete all files inside:
- `src/snowpyt_mechparams/weak_layer_parameters/tau_c.py`
- `src/snowpyt_mechparams/weak_layer_parameters/sigma_c.py`
- `src/snowpyt_mechparams/weak_layer_parameters/sigma_comp.py`
- `src/snowpyt_mechparams/weak_layer_parameters/mode_i_fracture_toughness.py`
- `src/snowpyt_mechparams/weak_layer_parameters/mode_ii_fracture_toughness.py`
- `src/snowpyt_mechparams/weak_layer_parameters/fracture_energy.py`
- `src/snowpyt_mechparams/weak_layer_parameters/__init__.py`
- Remove the directory itself

---

## Step 2: Rewrite the parameter graph (`parameter_graph.py`)

**File:** `src/snowpyt_mechparams/graph/parameter_graph.py`

Remove STEP 3b entirely (lines ~311–382):
- All 6 weak-layer parameter nodes (`G_c`, `G_Ic`, `G_IIc`, `sigma_c`, `tau_c`, `sigma_comp`)
- All their method edges (weissgraeber_rosendahl, reiweger, sigrist, mellor)
- `merge_weac_inputs` definition and its 11 flow edges
- `merge_roch_inputs` definition and its 3 flow edges (density, thickness, tau_c)

Add new nodes and edges:

```python
# Placeholder for unavailable weak-layer information
weak_layer_info = build_graph.param("weak_layer_info*", level="weak_layer")
# No method edges — this is a placeholder representing currently unavailable data

# Slab elasticity merge: E + ν (target for coverage analysis)
slab_elasticity_parameters = build_graph.merge("slab_elasticity_parameters")
build_graph.flow(elastic_modulus,  slab_elasticity_parameters)
build_graph.flow(poissons_ratio,   slab_elasticity_parameters)

# WEAC inputs: slab elasticity + density + shear_modulus + thickness + weak layer info
merge_weac_inputs = build_graph.merge("merge_weac_inputs")
build_graph.flow(slab_elasticity_parameters,  merge_weac_inputs)
build_graph.flow(density,                     merge_weac_inputs)
build_graph.flow(shear_modulus,               merge_weac_inputs)
build_graph.flow(measured_layer_thickness,    merge_weac_inputs)
build_graph.flow(weak_layer_info,             merge_weac_inputs)
build_graph.method_edge(merge_weac_inputs, g_delta, "weac_skier")

# Roch inputs: density + thickness + weak layer info (tau_c is part of weak_layer_info*)
merge_roch_inputs = build_graph.merge("merge_roch_inputs")
build_graph.flow(density,                  merge_roch_inputs)
build_graph.flow(measured_layer_thickness, merge_roch_inputs)
build_graph.flow(weak_layer_info,          merge_roch_inputs)
build_graph.method_edge(merge_roch_inputs, s_r, "roch_natural")
```

---

## Step 3: Update `graph/__init__.py`

**File:** `src/snowpyt_mechparams/graph/__init__.py`

- Remove imports/exports of: `G_c`, `G_Ic`, `G_IIc`, `sigma_c`, `tau_c`, `sigma_comp`, `WEAK_LAYER_PARAMS`
- Add exports: `weak_layer_info`, `slab_elasticity_parameters`
- Keep `STABILITY_PARAMS`, `g_delta`, `s_r`

---

## Step 4: Update `execution/dispatcher.py`

**File:** `src/snowpyt_mechparams/execution/dispatcher.py`

Remove all method registrations for weak-layer parameters (~lines 418–517):
- `G_c` / `weissgraeber_rosendahl`
- `G_Ic` / `weissgraeber_rosendahl`
- `G_IIc` / `weissgraeber_rosendahl`
- `sigma_c` / `weissgraeber_rosendahl` and `sigrist`
- `tau_c` / `weissgraeber_rosendahl`
- `sigma_comp` / `reiweger` and `mellor`

Remove the imports of the deleted weak_layer_parameters modules.

Keep: `weac_skier` and `roch_natural` dispatcher entries (stability_criteria/ code retained).

---

## Step 5: Update graph visualizers

**Files:**
- `src/snowpyt_mechparams/graph/visualize.py`
- `src/snowpyt_mechparams/graph/visualize_matplotlib.py`

Update `save_mermaid_stability_detail` / `generate_matplotlib_stability_detail` to:
- Replace the 6 weak-layer parameter nodes with the single `weak_layer_info*` node
- Show `slab_elasticity_parameters` merge node feeding into `merge_weac_inputs`
- Reflect that `weak_layer_info*` feeds both `merge_roch_inputs` and `merge_weac_inputs`

---

## Step 6: Re-run diagram generation

```bash
source venv/bin/activate
python scripts/generate_diagram.py --type all --format both --output docs/diagrams/
```

Verify output PNGs and `.md` files in `docs/diagrams/` reflect the new structure.

---

## Step 7: Update `examples/stability_criteria_inputs.ipynb`

**File:** `examples/stability_criteria_inputs.ipynb`

Remove:
- All code that computes or references `G_c`, `G_Ic`, `G_IIc`, `sigma_c`, `tau_c`, `sigma_comp`
- Any cell that executes the stability criteria (`calculate_weac_skier`, `calculate_roch`)
- The comparison section between Roch and WEAC outputs

Keep and update:
- **Roch section** (simplified): analyze which slabs have `density` + `measured_layer_thickness` computable across the 4 density pathways. Same table/figure format, measuring slab-input coverage only.
- **WEAC section** (updated target): analyze which slabs have `slab_elasticity_parameters` computable across all valid (density × E-mod × ν) pathways. Same table/figure format showing coverage by method combination.

Update the results export (parquet files) to match the new output DataFrames.

---

## Step 8: Delete example notebooks

Remove:
- `examples/roch_skier_all_parameters.ipynb`
- `examples/stability_criteria_outputs.ipynb`
- `examples/weac_skier_all_pathways.ipynb`

---

## Step 9: Update tests

**Remove entirely:**
- `tests/test_weak_layer_parameters.py`
- `tests/test_weak_layer_engine.py`

**Update `tests/test_weac_criterion.py`:**
- Remove graph/engine integration tests that relied on old weak-layer graph wiring
- Keep unit tests for `calculate_weac_skier` (independent of graph)

**Update `tests/test_roch_criterion.py`:**
- Remove engine integration tests that relied on graph wiring with `tau_c`
- Keep unit tests for `calculate_roch` and `calculate_shear_stress`

**Add new graph structure tests** (in `test_integration.py` or a new file):
- `weak_layer_info*` node exists with no computable incoming edges
- `slab_elasticity_parameters` has `elastic_modulus` and `poissons_ratio` as inputs
- `find_parameterizations(graph, slab_elasticity_parameters)` returns 32 pathways (4 density × 4 E-mod × 2 ν)
- `find_parameterizations(graph, g_delta)` returns 0 pathways (placeholder blocks completion)
- `find_parameterizations(graph, s_r)` returns 0 pathways

---

## Step 10: Update `README.md` and `docs/code_description.md`

**`README.md`:**
- Remove "Weak Layer Parameters" from Supported Parameters section
- Remove mentions of 128 g_delta pathways
- Add `slab_elasticity_parameters` merge node to graph description
- Remove deleted notebooks from examples list

**`docs/code_description.md`:**
- Same updates for overlapping content
- Update architecture descriptions that reference weak layer parameter computation

---

## Files to modify

| File | Action |
|------|--------|
| `src/snowpyt_mechparams/weak_layer_parameters/` | Delete directory |
| `src/snowpyt_mechparams/graph/parameter_graph.py` | Remove STEP 3b, add new nodes |
| `src/snowpyt_mechparams/graph/__init__.py` | Update exports |
| `src/snowpyt_mechparams/execution/dispatcher.py` | Remove weak-layer method registrations |
| `src/snowpyt_mechparams/graph/visualize.py` | Update stability diagram |
| `src/snowpyt_mechparams/graph/visualize_matplotlib.py` | Update stability diagram |
| `examples/stability_criteria_inputs.ipynb` | Rewrite per Step 7 |
| `tests/test_weak_layer_parameters.py` | Delete |
| `tests/test_weak_layer_engine.py` | Delete |
| `tests/test_weac_criterion.py` | Remove graph-dependent tests |
| `tests/test_roch_criterion.py` | Remove graph-dependent tests |
| `README.md` | Update documentation |
| `docs/code_description.md` | Update documentation |

**Delete:**
- `examples/roch_skier_all_parameters.ipynb`
- `examples/stability_criteria_outputs.ipynb`
- `examples/weac_skier_all_pathways.ipynb`

---

## Verification

1. **Import check:** `python -c "from snowpyt_mechparams.graph import graph; print(graph)"` — no errors
2. **Pathway count:** `find_parameterizations(graph, slab_elasticity_parameters_node)` returns 32 pathways
3. **Placeholder confirmed:** `find_parameterizations(graph, g_delta_node)` returns 0 pathways
4. **Diagram generation:** `python scripts/generate_diagram.py --type stability --format mermaid` — output shows `weak_layer_info*` and `slab_elasticity_parameters`
5. **Tests pass:** `pytest tests/` — no failures
6. **Notebook runs:** `stability_criteria_inputs.ipynb` executes end-to-end without errors
