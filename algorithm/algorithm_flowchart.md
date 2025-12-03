# Parameterization Algorithm Flowchart

This flowchart shows the key recursive and memoization logic in `parameterization_algorithm.py`.

```mermaid
flowchart TD
    Start(["find_parameterizations(t)"]) --> Backtrack{"backtrack(v)"}
    
    Backtrack --> CheckMemo{v in memo?}
    CheckMemo -->|Yes| Return[Return cached trees]
    CheckMemo -->|No| CheckBase{v == snow_pit?}
    
    CheckBase -->|Yes| BaseCase[Return empty PathTree]
    CheckBase -->|No| CheckType{Node type?}
    
    CheckType -->|parameter| ParamLogic["OR Logic:<br/>Each edge = alternative method"]
    CheckType -->|merge| MergeLogic["AND Logic:<br/>All edges required"]
    
    ParamLogic --> ParamLoop["For each incoming edge:"]
    ParamLoop --> RecurseParam["🔄 trees = backtrack(edge.start)"]
    RecurseParam -.->|recurse| Backtrack
    RecurseParam --> ParamNested["For each returned tree:"]
    ParamNested --> WrapTree["Create new PathTree:<br/>current node → tree"]
    WrapTree --> AddToList["Add to all_trees list"]
    AddToList --> ParamStore[Store all_trees in memo]
    
    MergeLogic --> MergeLoop["For each incoming edge:"]
    MergeLoop --> RecurseMerge["🔄 trees = backtrack(edge.start)"]
    RecurseMerge -.->|recurse| Backtrack
    RecurseMerge --> CollectInputs["Collect into input_trees_list:<br/>[[trees from edge1], [trees from edge2], ...]"]
    CollectInputs --> Cartesian["Cartesian product:<br/>Pick 1 tree from each edge"]
    Cartesian --> MergeNested["For each combination:"]
    MergeNested --> CreateMerge["Create PathTree with<br/>all inputs as branches"]
    CreateMerge --> AddMerge["Add to all_trees list"]
    AddMerge --> MergeStore[Store all_trees in memo]
    
    StoreParam --> End
    StoreMerge --> End
    BaseCase --> End
    Return --> End
    End([Results bubble up<br/>through recursion])
    
    style Start fill:#e1f5e1
    style End fill:#e1f5e1
    style CheckMemo fill:#fff4e1
    style CheckBase fill:#fff4e1
    style CheckType fill:#fff4e1
    style ParamLogic fill:#e1e5ff
    style MergeLogic fill:#ffe1e1
    style RecurseParam fill:#ffeb99
    style RecurseMerge fill:#ffeb99
```

## Key Components

### 1. Memoization Strategy
- **Cache**: `memo: Dict[Node, List[PathTree]]`
- **Purpose**: Avoid recomputing path trees for nodes visited multiple times
- **Check**: First operation in `backtrack()` checks if node is in memo

### 2. Base Case
- **Condition**: `node == snow_pit`
- **Action**: Return PathTree with empty branches (leaf node)

### 3. Parameter Node (OR Logic)
- **Meaning**: Each incoming edge represents a different method to calculate this parameter
- **Example**: If parameter `X` can be calculated by method A OR method B, we explore both
- **Process**: 
  1. For each incoming edge (method):
     - Recursively get all path trees from the predecessor node
     - For each returned tree, wrap it by creating a new PathTree with current node on top
     - Add all wrapped trees to the result list
- **Result**: If edge1 returns 3 trees and edge2 returns 2 trees, we get 5 total trees (3+2)

### 4. Merge Node (AND Logic)
- **Meaning**: All incoming edges must be included (all inputs are required)
- **Example**: If merge node needs input A AND input B, we must have paths for both
- **Process**:
  1. For each incoming edge:
     - Recursively get all path trees from the predecessor node
     - Store in input_trees_list: `[[trees from A], [trees from B], ...]`
  2. Compute Cartesian product: pick one tree from each input
  3. For each combination, create a PathTree with all inputs as branches
- **Result**: If input A has 2 trees and input B has 3 trees, we get 6 combinations (2×3)
- **Why Cartesian?**: Every way to reach A must be paired with every way to reach B

### 5. Recursion Flow
- **Initial call**: `find_parameterizations()` calls `backtrack(target_parameter)`
- **Recursive calls**: Each `backtrack(node)` may call `backtrack()` on predecessor nodes
- **Return path**: 
  - When `backtrack()` returns to another `backtrack()` call (recursive case), the returned trees are used to construct the caller's trees
  - When `backtrack()` returns to `find_parameterizations()` (base of call stack), the recursion is complete
- **Direction**: Works backward from target parameter to snow_pit
- **Memoization**: Prevents redundant computation when the same node is reached via different paths
- **Result**: Returns list of all possible path trees from the given node to snow_pit

## Complexity Notes

- **Memoization**: Each node computed at most once
- **Cartesian Product**: For merge nodes with n inputs, if each has m trees, produces m^n combinations
- **Result**: All possible parameterizations are enumerated

