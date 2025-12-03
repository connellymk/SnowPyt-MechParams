# Parameterization Algorithm Flowchart

This flowchart shows the key recursive and memoization logic in `parameterization_algorithm.py`.

```mermaid
flowchart TD
    Start(["find_parameterizations(t)"]) --> Init[Initialize memo]
    Init --> CallBacktrack["Call backtrack(t)"]
    
    CallBacktrack --> Backtrack{"backtrack(v) function"}
    
    Backtrack --> CheckMemo{v in memo?}
    CheckMemo -->|Yes| ReturnCached[Return cached result]
    CheckMemo -->|No| CheckBase{Node == snow_pit?}
    
    CheckBase -->|Yes| BaseCase[Create PathTree with empty branches]
    BaseCase --> StoreMemo1[Store in memo]
    StoreMemo1 --> Return1[Return PathTree list]
    
    CheckBase -->|No| CheckType{Node type?}
    
    CheckType -->|parameter| ParamLogic[OR Logic: Each incoming edge is independent]
    CheckType -->|merge| MergeLogic[AND Logic: All incoming edges required]
    
    ParamLogic --> LoopEdges[For each incoming edge]
    LoopEdges --> RecurseParam[🔄 RECURSIVE CALL:<br/>backtrack edge.start]
    RecurseParam -.->|recursive call| Backtrack
    RecurseParam --> CreateParamTree[For each returned tree:<br/>Create new PathTree with<br/>single branch]
    CreateParamTree --> CollectParam[Collect all trees]
    CollectParam --> StoreMemo2[Store in memo]
    StoreMemo2 --> Return2[Return all trees]
    
    MergeLogic --> GetInputs[For each incoming edge]
    GetInputs --> RecurseMerge[🔄 RECURSIVE CALL:<br/>backtrack edge.start]
    RecurseMerge -.->|recursive call| Backtrack
    RecurseMerge --> Cartesian[Compute Cartesian product<br/>of all input tree lists]
    Cartesian --> CreateMergeTrees[For each combination:<br/>Create PathTree with<br/>is_merge=True]
    CreateMergeTrees --> StoreMemo3[Store in memo]
    StoreMemo3 --> Return3[Return all trees]
    
    Return1 --> BackToMain
    Return2 --> BackToMain
    Return3 --> BackToMain
    ReturnCached --> BackToMain
    
    BackToMain[Return List of PathTrees<br/>to caller] --> CheckCaller{Is caller another<br/>backtrack call?}
    CheckCaller -->|Yes: recursive| UseInParent[Caller uses returned trees<br/>to build its own trees]
    UseInParent -.->|continues processing| CreateParamTree
    UseInParent -.->|continues processing| Cartesian
    CheckCaller -->|No: initial call| ConvertTrees[Convert PathTrees to<br/>Parameterizations]
    ConvertTrees --> End([Return parameterizations])
    
    style Start fill:#e1f5e1
    style End fill:#e1f5e1
    style CheckMemo fill:#fff4e1
    style CheckBase fill:#fff4e1
    style CheckType fill:#fff4e1
    style CheckComplete fill:#fff4e1
    style ParamLogic fill:#e1e5ff
    style MergeLogic fill:#ffe1e1
    style StoreMemo1 fill:#f0f0f0
    style StoreMemo2 fill:#f0f0f0
    style StoreMemo3 fill:#f0f0f0
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
- **Behavior**: Each incoming edge represents an alternative way to compute the parameter
- **Process**: 
  1. Loop through each incoming edge independently
  2. Recursively get trees from edge source
  3. Create new tree for each source tree
  4. Collect all possibilities

### 4. Merge Node (AND Logic)
- **Behavior**: All incoming edges must be included
- **Process**:
  1. Get trees for each input edge
  2. Compute Cartesian product of all input tree lists
  3. Create tree for each combination
  4. Each combination represents one valid way to satisfy all merge inputs

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

