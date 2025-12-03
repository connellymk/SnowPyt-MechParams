# Step-by-Step Walkthrough: Finding Parameterizations for Density

This document walks through how the algorithm finds all parameterizations for the `density` parameter. Follow along with the flowchart in `algorithm_flowchart.md`.

## Graph Structure for Density

From `definitions.py`, the density node has the following incoming edges:

```
density has 3 incoming edges:
  1. measured_density --data_flow--> density
  2. merge_hh_gf --geldsetzer--> density
  3. merge_hh_gf --kim_jamieson_table2--> density
  4. merge_hh_gf_gs --kim_jamieson_table5--> density

Where:
  - merge_hh_gf = merge of (measured_hand_hardness, measured_grain_form)
  - merge_hh_gf_gs = merge of (measured_hand_hardness, measured_grain_form, measured_grain_size)
```

## Algorithm Execution

### Initial Call

```
find_parameterizations(graph, density)
  └─> Initialize memo = {}
  └─> Call backtrack(density)
```

---

## Call 1: `backtrack(density)`

**Node**: `density` (parameter node)

**Step 1**: Check memo
- `density` not in memo ❌
- Continue...

**Step 2**: Check base case
- `density ≠ snow_pit` ❌
- Continue...

**Step 3**: Check node type
- Type: `parameter` ✓
- Use **OR Logic**

**Step 4**: Process each incoming edge independently

### Edge 1.1: `measured_density --data_flow--> density`

```
🔄 Recursive call: backtrack(measured_density)
```

Go to **Call 2** ⬇️

---

## Call 2: `backtrack(measured_density)`

**Node**: `measured_density` (parameter node)

**Step 1**: Check memo
- `measured_density` not in memo ❌

**Step 2**: Check base case
- `measured_density ≠ snow_pit` ❌

**Step 3**: Check node type
- Type: `parameter` ✓
- Use **OR Logic**

**Step 4**: Process incoming edge

### Edge 2.1: `snow_pit --data_flow--> measured_density`

```
🔄 Recursive call: backtrack(snow_pit)
```

Go to **Call 3** ⬇️

---

## Call 3: `backtrack(snow_pit)`

**Node**: `snow_pit`

**Step 1**: Check memo
- `snow_pit` not in memo ❌

**Step 2**: Check base case
- `snow_pit == snow_pit` ✅
- **BASE CASE REACHED!**

**Step 3**: Return
```python
Return: [PathTree(node_name="snow_pit", branches=[])]
```

Store in memo: `memo[snow_pit] = [PathTree("snow_pit", [])]`

Return to **Call 2** ⬆️

---

## Call 2 (continued): `backtrack(measured_density)`

**Returned from Call 3**: `[PathTree("snow_pit", [])]`

**Step 5**: Extend each returned tree
```python
For tree in [PathTree("snow_pit", [])]:
    Create new PathTree:
        node_name = "measured_density"
        branches = [(tree, "data_flow")]
```

**Result**: `[PathTree("measured_density", [(PathTree("snow_pit", []), "data_flow")])]`

**Step 6**: Store in memo and return
```python
memo[measured_density] = [PathTree("measured_density", ...)]
Return: [PathTree("measured_density", ...)]
```

Return to **Call 1** ⬆️

---

## Call 1 (continued): `backtrack(density)` - Edge 1.1 complete

**Returned from Call 2**: `[PathTree("measured_density", ...)]`

**Step 5**: Extend the returned tree
```python
Create PathTree:
    node_name = "density"
    branches = [(PathTree("measured_density", ...), "data_flow")]
```

**Collected so far**: 1 tree representing:
```
snow_pit → measured_density → density
```

---

### Edge 1.2: `merge_hh_gf --geldsetzer--> density`

```
🔄 Recursive call: backtrack(merge_hh_gf)
```

Go to **Call 4** ⬇️

---

## Call 4: `backtrack(merge_hh_gf)`

**Node**: `merge_hh_gf` (merge node)

**Step 1**: Check memo
- `merge_hh_gf` not in memo ❌

**Step 2**: Check base case
- `merge_hh_gf ≠ snow_pit` ❌

**Step 3**: Check node type
- Type: `merge` ✓
- Use **AND Logic**

**Step 4**: Get trees for each incoming edge

### Input A: `measured_hand_hardness --data_flow--> merge_hh_gf`

```
🔄 Recursive call: backtrack(measured_hand_hardness)
```

This follows the same pattern as `measured_density`:
- Calls `backtrack(snow_pit)` (already in memo! Returns cached result)
- Returns: `[PathTree("measured_hand_hardness", [(PathTree("snow_pit", []), "data_flow")])]`

### Input B: `measured_grain_form --data_flow--> merge_hh_gf`

```
🔄 Recursive call: backtrack(measured_grain_form)
```

Similarly returns:
- Returns: `[PathTree("measured_grain_form", [(PathTree("snow_pit", []), "data_flow")])]`

**Step 5**: Collect results (keep grouped!)
```python
input_list = [
    [PathTree("measured_hand_hardness", ...)],  # 1 tree from input A
    [PathTree("measured_grain_form", ...)]      # 1 tree from input B
]
```

**Step 6**: Cartesian product
```
Combinations: 1 × 1 = 1 combination
  (tree_A1, tree_B1)
```

**Step 7**: Create merged PathTree for each combination
```python
PathTree(
    node_name = "merge_hh_gf",
    branches = [
        (PathTree("measured_hand_hardness", ...), "data_flow"),
        (PathTree("measured_grain_form", ...), "data_flow")
    ],
    is_merge = True
)
```

**Step 8**: Store and return
```python
memo[merge_hh_gf] = [PathTree("merge_hh_gf", ...)]
Return: [PathTree("merge_hh_gf", ...)]
```

Return to **Call 1** ⬆️

---

## Call 1 (continued): `backtrack(density)` - Edge 1.2 complete

**Returned from Call 4**: `[PathTree("merge_hh_gf", ...)]`

**Step 5**: Extend the returned tree
```python
Create PathTree:
    node_name = "density"
    branches = [(PathTree("merge_hh_gf", ...), "geldsetzer")]
```

**Collected so far**: 2 trees representing:
1. `snow_pit → measured_density → density`
2. `snow_pit → measured_hand_hardness → merge_hh_gf → density`
   `snow_pit → measured_grain_form → merge_hh_gf → density`

---

### Edge 1.3: `merge_hh_gf --kim_jamieson_table2--> density`

```
🔄 Recursive call: backtrack(merge_hh_gf)
```

**Already in memo!** ✅ Return cached result immediately.

**Step 5**: Extend the returned tree
```python
Create PathTree:
    node_name = "density"
    branches = [(PathTree("merge_hh_gf", ...), "kim_jamieson_table2")]
```

**Collected so far**: 3 trees (same structure as #2, but different method name)

---

### Edge 1.4: `merge_hh_gf_gs --kim_jamieson_table5--> density`

```
🔄 Recursive call: backtrack(merge_hh_gf_gs)
```

This merge node has **3 inputs**:
- `measured_hand_hardness` → returns 1 tree
- `measured_grain_form` → returns 1 tree (from memo)
- `measured_grain_size` → returns 1 tree (follows same pattern)

**Cartesian product**: 1 × 1 × 1 = 1 combination

Returns: `[PathTree("merge_hh_gf_gs", ...)]` with 3 branches

**Step 5**: Extend the returned tree

**Collected so far**: 4 trees total

---

## Call 1 (final): `backtrack(density)` complete

**Step 6**: Store all trees in memo
```python
memo[density] = [tree1, tree2, tree3, tree4]
```

**Step 7**: Return all 4 trees

Return to `find_parameterizations()` ⬆️

---

## Final Step: Convert to Parameterizations

`find_parameterizations()` receives 4 PathTrees and converts each to a Parameterization:

### Parameterization 1 (Simple path - no merge)
```
branch 1: snow_pit -- data_flow --> measured_density -- data_flow --> density
```

### Parameterization 2 (Merge with 2 inputs)
```
branch 1: snow_pit -- data_flow --> measured_hand_hardness -- data_flow --> merge_hh_gf
branch 2: snow_pit -- data_flow --> measured_grain_form -- data_flow --> merge_hh_gf
merge branch 1, branch 2: merge_hh_gf -- geldsetzer --> density
```

### Parameterization 3 (Same merge, different method)
```
branch 1: snow_pit -- data_flow --> measured_hand_hardness -- data_flow --> merge_hh_gf
branch 2: snow_pit -- data_flow --> measured_grain_form -- data_flow --> merge_hh_gf
merge branch 1, branch 2: merge_hh_gf -- kim_jamieson_table2 --> density
```

### Parameterization 4 (Merge with 3 inputs)
```
branch 1: snow_pit -- data_flow --> measured_hand_hardness -- data_flow --> merge_hh_gf_gs
branch 2: snow_pit -- data_flow --> measured_grain_form -- data_flow --> merge_hh_gf_gs
branch 3: snow_pit -- data_flow --> measured_grain_size -- data_flow --> merge_hh_gf_gs
merge branch 1, branch 2, branch 3: merge_hh_gf_gs -- kim_jamieson_table5 --> density
```

---

## Key Observations

### Memoization in Action
- `snow_pit` was computed once and reused 4+ times
- `merge_hh_gf` was computed once and reused for both `geldsetzer` and `kim_jamieson_table2` methods
- This dramatically reduces computation time!

### OR Logic (Parameter nodes)
- `density` has 4 incoming edges → try each independently
- Results are **added**: 1 + 1 + 1 + 1 = **4 parameterizations**

### AND Logic (Merge nodes)
- `merge_hh_gf` has 2 inputs → must combine both
- Results are **multiplied**: 1 × 1 = **1 combination**
- `merge_hh_gf_gs` has 3 inputs → must combine all three
- Results are **multiplied**: 1 × 1 × 1 = **1 combination**

### Recursion Pattern
- Algorithm works **backward** from target to `snow_pit`
- Each recursive call builds on results from deeper calls
- Trees are extended one node at a time as recursion unwinds

---

## Call Stack Visualization

```
find_parameterizations(density)
  └─> backtrack(density)                    [parameter node - OR logic]
       ├─> backtrack(measured_density)      [parameter node - OR logic]
       │    └─> backtrack(snow_pit)         [BASE CASE] ✓
       │
       ├─> backtrack(merge_hh_gf)           [merge node - AND logic]
       │    ├─> backtrack(measured_hand_hardness)
       │    │    └─> backtrack(snow_pit)    [from memo] ✓
       │    └─> backtrack(measured_grain_form)
       │         └─> backtrack(snow_pit)    [from memo] ✓
       │
       ├─> backtrack(merge_hh_gf)           [from memo] ✓
       │
       └─> backtrack(merge_hh_gf_gs)        [merge node - AND logic]
            ├─> backtrack(measured_hand_hardness)  [from memo] ✓
            ├─> backtrack(measured_grain_form)     [from memo] ✓
            └─> backtrack(measured_grain_size)
                 └─> backtrack(snow_pit)    [from memo] ✓
```

**Total unique nodes computed**: 6 (snow_pit, measured_density, measured_hand_hardness, measured_grain_form, measured_grain_size, merge_hh_gf, merge_hh_gf_gs)

**Total recursive calls avoided by memoization**: 5+ calls to `snow_pit`, 2+ calls to other nodes

---

## Summary

The algorithm found **4 parameterizations** for density:
1. Direct measurement
2. Calculate from hand hardness + grain form (method: geldsetzer)
3. Calculate from hand hardness + grain form (method: kim_jamieson_table2)
4. Calculate from hand hardness + grain form + grain size (method: kim_jamieson_table5)

Each parameterization represents a complete, valid path from `snow_pit` to `density`.

