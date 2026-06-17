# Classification Rules

Use these as routing heuristics, not as a closed taxonomy.

## Sliding Window

Choose `array.sliding_window.variable` when the problem asks for a longest/shortest continuous subarray or substring and the window condition can be maintained while moving left/right pointers. Positive numbers plus sum constraints strongly indicate a variable window.

Use alternatives carefully:

- Prefix sum is useful for interval sums, but enumerating all intervals can still be O(n^2).
- Monotonic queue is needed when negative numbers break ordinary window monotonicity.
- Dynamic programming is not preferred when the state is simply a maintained window condition.

## Prefix Sum

Choose `array.prefix_sum` when repeated range-sum queries, count of subarrays with exact sum, or negative values make direct window contraction invalid.

## Hashing

Choose `hash.table` or `hash.frequency` when the core operation is membership lookup, index lookup, frequency counting, duplicate detection, or complement search.

## Stack / Queue

Choose `stack.monotonic` for nearest greater/smaller element and one-pass comparison against a monotonic boundary. Choose `queue.monotonic` for sliding-window maximum/minimum or shortest subarray with negative values and prefix sums.

## Linked List

Choose linked-list nodes when pointer rewiring, dummy head, fast/slow pointer, cycle detection, midpoint, or in-place reversal is central.

## Tree / Graph

Choose tree DFS/BFS when hierarchical parent-child traversal is central. Choose graph BFS for shortest unweighted step count, connected components, or layer expansion. Choose Dijkstra when weighted non-negative shortest paths are central.

## Dynamic Programming

Choose DP when there are overlapping subproblems, optimal substructure, and a state definition is necessary to avoid repeated computation.

## Backtracking

Choose backtracking when the problem asks for all combinations, permutations, paths, partitions, or valid configurations and requires choose-recursive-undo exploration.

## Insufficient Information

If the statement lacks decisive constraints, still give candidates:

- Missing whether values can be negative: sliding window vs prefix sum / monotonic queue may be undecidable.
- Missing continuity requirement: subarray/substr vs subsequence may be undecidable.
- Missing graph edge weights: BFS vs Dijkstra may be undecidable.
