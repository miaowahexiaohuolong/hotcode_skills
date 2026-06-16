---
name: leetcode-saver
description: Save, query, update, list, and delete LeetCode problem records in a local JSON tracker. Use when the user asks Codex to remember, record, log, save, look up, list, update, mark, or delete solved LeetCode questions, including requests in Chinese such as 保存题目、记录刷题、查询题号、更新状态、标记已掌握、删除题目.
---

# LeetCode Saver

Use this skill to maintain a local LeetCode practice log. Store data in a single UTF-8 JSON file and prefer the bundled script for all read/write operations.

## Data File

Default path: `data/leetcode_problems.json` in the current workspace.

The JSON shape is:

```json
{
  "problems": {
    "3": {
      "id": "3",
      "title": "Longest Substring Without Repeating Characters",
      "title_cn": "无重复字符的最长子串",
      "difficulty": "medium",
      "category": "字符串",
      "topic": "滑动窗口",
      "content": "给定一个字符串 s ，请你找出其中不含有重复字符的最长子串的长度。",
      "examples": [
        "示例 1:\n输入: s = \"abcabcbb\"\n输出: 3\n解释: 因为无重复字符的最长子串是 \"abc\"，所以其长度为 3。"
      ],
      "status": "fuzzy",
      "note": "左边界要跳到 max(left, last_seen[char]+1)",
      "added_at": "2026-06-15 22:20:00"
    }
  }
}
```

## Workflow

1. Identify the requested operation: `add`, `get`, `list`, `update`, or `delete`.
2. Use `scripts/leetcode_saver.py` from this skill directory to perform the operation.
3. When the user pastes LeetCode problem text, extract and save the problem statement as `content`.
4. Extract examples into `examples` when present. If no examples are present, omit `examples`; do not ask for examples.
5. If the user asks to save a problem and omits required fields, ask only for missing required fields: `title`, `difficulty`, `category`, or `topic`.
6. If the user provides enough information, do not ask for confirmation before adding or updating. Use `--yes` when overwriting or deleting only if the user clearly requested that action.
7. Report the result briefly, including the problem id and where the data was saved.

## Commands

Run the script from any workspace:

```bash
python /Volumes/UD210/hotcode_skills/.claude/skills/leetcode-saver/scripts/leetcode_saver.py list
```

Add a problem:

```bash
python /Volumes/UD210/hotcode_skills/.claude/skills/leetcode-saver/scripts/leetcode_saver.py add 3 "Longest Substring Without Repeating Characters" \
  --title-cn "无重复字符的最长子串" \
  --difficulty medium \
  --category "字符串" \
  --topic "滑动窗口" \
  --content "给定一个字符串 s ，请你找出其中不含有重复字符的最长子串的长度。" \
  --example "示例 1:\n输入: s = \"abcabcbb\"\n输出: 3\n解释: 因为无重复字符的最长子串是 \"abc\"，所以其长度为 3。" \
  --status fuzzy \
  --note "左边界要跳到 max(left, last_seen[char]+1)"
```

Query, update, and delete:

```bash
python /Volumes/UD210/hotcode_skills/.claude/skills/leetcode-saver/scripts/leetcode_saver.py get 3
python /Volumes/UD210/hotcode_skills/.claude/skills/leetcode-saver/scripts/leetcode_saver.py update 3 --status mastered --note "已掌握"
python /Volumes/UD210/hotcode_skills/.claude/skills/leetcode-saver/scripts/leetcode_saver.py delete 3
```

Use `--data-path <path>` when the user wants a non-default JSON file.

## Field Rules

- `id`: required string, unique primary key.
- `title`: required English title.
- `title_cn`: optional Chinese title.
- `difficulty`: required; one of `easy`, `medium`, `hard`.
- `category`: required primary category, such as `数组`, `字符串`, `动态规划`.
- `topic`: required focused topic, such as `滑动窗口`, `前缀和`.
- `content`: optional for manual logging, but include it when extracting from pasted LeetCode problem text. Store the actual problem statement and constraints, not site UI labels.
- `examples`: optional list of examples. Include only when examples exist; omit the field when absent.
- `status`: one of `mastered`, `fuzzy`, `weak`; default `fuzzy`.
- `note`: optional, default empty string.
- `added_at`: generated automatically and preserved during updates.

## Problem Text Extraction

When the user provides raw LeetCode page text:

- Extract `id`, `title_cn`, and `difficulty` from heading lines such as `3. 无重复字符的最长子串` and `中等`.
- Map Chinese difficulties: `简单` -> `easy`, `中等` -> `medium`, `困难` -> `hard`.
- Put the actual prompt, requirements,说明, and提示/constraints into `content`.
- Put each `示例 N` block into one `--example` value. Include input, output, explanation, and related code snippets inside that example block.
- Ignore UI noise such as `代码`, `测试用例`, `测试结果`, `相关标签`, `premium lock icon`, `相关企业`, and standalone navigation labels.
- If examples are not present, do not invent examples and do not include `examples`.
- If category or topic is not explicit, infer a concise value from the problem when obvious; otherwise ask the user.

## User Interaction

- For "帮我保存 LeetCode 3..." or "记录第 3 题...", add the problem.
- For pasted full problem statements, save both `content` and any example blocks.
- For "第 3 题我已经掌握了", run `update 3 --status mastered`.
- For "列出我刷过的题", run `list`.
- For "查询 3", run `get 3`.
- For "删除 3", run `delete 3`; confirm with the user if their wording is ambiguous.
