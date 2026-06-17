# Visualization Rules

Every explanation should include example input, initial state, key variables, state transitions, why each move is made, final result, and the reusable pattern.

## Array / Sliding Window

Show indexes, array cells, `L`, `R`, current window, current sum/count, answer update, expansion, and contraction.

```text
下标：  0   1   2
数组： [2] [3] [1]
        L       R
窗口：[2, 3, 1]
窗口和：6
```

## Linked List

Show nodes and pointer names such as `prev`, `cur`, `next`. Always show before/after pointer rewiring.

## Tree

Show tree shape, traversal order, and recursive call stack.

## Graph

Show adjacency, queue/stack, visited set, distance/path updates, and layer changes.

## Dynamic Programming

Show DP meaning, initialization, transition source, and table updates.

## Backtracking

Show search tree, choice, recursion, undo, and pruning reason.

## Structured Animation Data

When useful, include JSON-like steps:

```json
{
  "visualization_type": "sliding_window",
  "steps": [
    {
      "step": 1,
      "left": 0,
      "right": 0,
      "window": [2],
      "current_sum": 2,
      "action": "右指针扩张",
      "explanation": "窗口和小于 target，继续扩大窗口"
    }
  ]
}
```
