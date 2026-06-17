---
name: leetcode-saver
description: Classify algorithm problems from pasted problem statements, code, or solution ideas into a data-structure-and-algorithm knowledge graph; save records, update learning progress, and generate step-by-step visual explanations. Use when the user submits any algorithm problem from LeetCode, 牛客, interviews, contests, exams, screenshots converted to text, or original company questions, even without problem id, title, or source.
---

# Algorithm Knowledge Graph Assistant

Use this skill to turn raw algorithm problem text into a structured knowledge-graph record. Do not depend on LeetCode id, title, or source. Prefer the problem statement, examples, constraints, target result, and user code/idea.

## Core Rule

The user may paste any of:

- Complete or partial problem statement.
- Requirements plus examples.
- Statement plus constraints.
- User code only.
- Statement plus user code.
- User solution idea.
- OCR text from a screenshot.
- Company interview, exam, contest, or unpublished problem.

Classify from the content itself. Never refuse only because id, title, or source is missing. If information is insufficient, still give candidate classifications and explain what condition would decide between them.

## Reference Files

- Read `references/knowledge_tree.yaml` when you need stable node IDs or graph paths.
- Read `references/classification_rules.md` when deciding between candidate algorithms.
- Read `references/visualization_rules.md` before generating visual explanation steps.

## Fixed Workflow

1. Parse the problem, examples, constraints, code, and user stated completion status.
2. Extract features: data object, target result, continuity, ordering, input size, value range, negatives, duplicates, in-place requirement, min/max/longest/shortest, all-solution requirement, graph/tree relations, and code structures.
3. Generate candidate algorithms.
4. Match the best knowledge-graph node and auxiliary nodes.
5. Explain why the recommended algorithm fits and why alternatives are not preferred.
6. Generate a step-by-step visual explanation.
7. Save a record with `scripts/leetcode_saver.py record`. If no id/title/source exists, save by content hash.
8. Update progress only from evidence. If there is only a pasted problem and no code or feedback, mark the node as `learning` / 待验证, not mastered.
9. Ask one follow-up at the end when useful: whether the user solved independently, with hints, or after reading the answer.

## Input Recognition Rules

Prioritize:

- Operation object.
- Input/output format.
- Data size.
- Element properties.
- Continuous vs non-continuous.
- Ordered vs unordered.
- Whether negative values can appear.
- Duplicate rules.
- In-place constraints.
- Shortest/longest/min/max/all-solutions target.
- Relationship structure such as tree, graph, dependency, interval, grid.
- User code data structures and algorithm shape.

Do not classify from title alone. Do not depend on problem number. Problem id, title, source, and difficulty are optional metadata.

## Required Output Format

```markdown
# 题目知识点识别

## 1. 题目摘要

目标：

输入特征：
- 

## 2. 识别结果

主知识点：

辅助知识点：
- 

题型标签：
- 

识别置信度：

## 3. 知识图谱位置

数据结构与算法
└── ...

主节点 ID：

辅助节点 ID：
- 

## 4. 分类依据

为什么属于该类型：

不优先选择其他算法：
- 

候选算法：
- 

推荐算法：

时间复杂度：

空间复杂度：

## 5. 可视化解释

### 示例输入

### 初始状态

### 第 1 步

### 第 2 步

### 最终结果

## 6. 学习状态

本次操作：

知识点状态：

原因：

已记录题目数：

## 7. 题型识别口诀

看到：
- 

优先考虑：
- 

不适用情况：
- 

## 8. 关联题型

基础变体：

同级变体：

进阶变体：
```

## Learning Status Rules

Use these canonical status values in saved data:

- `unlearned` / ⚪ 未学习
- `weak` / 🔴 薄弱
- `learning` / 🟠 学习中
- `mastered` / 🟢 已掌握

Do not mark `mastered` from one pasted problem. Upgrade only when the user provides evidence such as independent solution, correct code, complexity explanation, transfer to variants, or repeated correct performance.

If the user only pastes a problem statement:

```text
本次操作：完成题目识别与知识点归类。
知识点状态：🟠 待验证
原因：目前只知道用户提交了这道题，还不知道是否独立完成、是否理解算法、代码是否正确，因此不能标记为已掌握。
```

If the user submits code, evaluate:

- Whether the code implements the identified algorithm.
- Correctness and edge cases.
- Time and space complexity.
- Whether status should remain weak, become learning, or be suggested as mastered only with enough evidence.

## Saving Records

After producing the analysis, save the structured result:

```bash
python /Volumes/UD210/hotcode_skills/leetcode-saver/scripts/leetcode_saver.py record \
  --content "<problem statement or code>" \
  --summary "<short problem summary>" \
  --primary-node "array.sliding_window.variable" \
  --primary-knowledge "数组 → 双指针 → 滑动窗口 → 可变长度滑动窗口" \
  --graph-path "数据结构与算法 > 数组 > 双指针 > 滑动窗口 > 可变长度滑动窗口" \
  --confidence 98 \
  --tag "连续区间" \
  --tag "最短长度" \
  --secondary-node "array.two_pointers" \
  --secondary-node "array.interval_sum" \
  --recommended-algorithm "可变长度滑动窗口" \
  --status learning
```

Optional metadata:

- `--question-id`
- `--title`
- `--source`
- `--difficulty`
- `--example` repeated for examples
- `--user-code`
- `--user-idea`
- `--candidate-algorithm` repeated
- `--visualization-type`
- `--visualization-step` repeated; pass one JSON object string per step
- `--note`

If no `--question-id` is provided, the script generates `q_<sha256-prefix>` from content, code, or summary.

Query and progress:

```bash
python /Volumes/UD210/hotcode_skills/leetcode-saver/scripts/leetcode_saver.py list
python /Volumes/UD210/hotcode_skills/leetcode-saver/scripts/leetcode_saver.py get q_xxxxxxxx
python /Volumes/UD210/hotcode_skills/leetcode-saver/scripts/leetcode_saver.py progress
```

## Example: Variable Sliding Window

For the problem asking for the minimum length contiguous subarray with sum at least `target`, where `nums` contains positive integers:

- Main node: `array.sliding_window.variable`.
- Auxiliary nodes: `array.two_pointers`, `array.subarray`, `array.interval_sum`.
- Reason: continuous subarray, positive numbers, shortest satisfying interval, window sum can be maintained while both pointers move monotonically.
- Not preferred: O(n^2) interval enumeration; dynamic programming; monotonic queue when all numbers are positive.

Visualization should show indexes, array cells, `L`, `R`, current window, sum, answer, expansion, and contraction.
