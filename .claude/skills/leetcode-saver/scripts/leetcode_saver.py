#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


STATUSES = {"unlearned", "weak", "learning", "mastered"}
STATUS_RANK = {"unlearned": 0, "weak": 1, "learning": 2, "mastered": 3}
STATUS_COLOR = {
    "unlearned": "gray",
    "weak": "red",
    "learning": "orange",
    "mastered": "green",
}
DEFAULT_DATA_PATH = Path("data") / "algorithm_knowledge_graph.json"


KNOWLEDGE_NODES: dict[str, dict[str, Any]] = {
    "root": {"name": "数据结构与算法", "parent_id": None, "category": "root"},
    "array": {"name": "数组", "parent_id": "root", "category": "数组"},
    "array.operation": {"name": "数组操作", "parent_id": "array", "category": "数组"},
    "array.prefix_sum": {"name": "前缀和", "parent_id": "array.operation", "category": "数组"},
    "array.diff": {"name": "差分数组", "parent_id": "array.operation", "category": "数组"},
    "array.matrix": {"name": "二维数组", "parent_id": "array.operation", "category": "数组"},
    "array.two_pointers": {"name": "双指针技巧", "parent_id": "array", "category": "数组"},
    "array.subarray": {"name": "连续子数组", "parent_id": "array.two_pointers", "category": "数组"},
    "array.interval_sum": {"name": "区间和维护", "parent_id": "array.two_pointers", "category": "数组"},
    "array.sliding_window": {"name": "滑动窗口", "parent_id": "array.two_pointers", "category": "数组"},
    "array.sliding_window.fixed": {"name": "固定长度滑动窗口", "parent_id": "array.sliding_window", "category": "数组"},
    "array.sliding_window.variable": {"name": "可变长度滑动窗口", "parent_id": "array.sliding_window", "category": "数组"},
    "array.binary_search": {"name": "二分查找", "parent_id": "array.two_pointers", "category": "数组"},
    "hash.table": {"name": "哈希表", "parent_id": "root", "category": "哈希表"},
    "hash.frequency": {"name": "频率统计", "parent_id": "hash.table", "category": "哈希表"},
    "stack_queue": {"name": "栈与队列", "parent_id": "root", "category": "栈与队列"},
    "stack.monotonic": {"name": "单调栈", "parent_id": "stack_queue", "category": "栈与队列"},
    "queue.monotonic": {"name": "单调队列", "parent_id": "stack_queue", "category": "栈与队列"},
    "linked_list": {"name": "链表", "parent_id": "root", "category": "链表"},
    "linked_list.fast_slow_pointer": {"name": "链表双指针", "parent_id": "linked_list", "category": "链表"},
    "linked_list.reverse": {"name": "链表反转", "parent_id": "linked_list", "category": "链表"},
    "tree": {"name": "二叉树", "parent_id": "root", "category": "二叉树"},
    "tree.binary_tree.dfs": {"name": "递归遍历", "parent_id": "tree", "category": "二叉树"},
    "tree.binary_tree.bfs": {"name": "层序遍历", "parent_id": "tree", "category": "二叉树"},
    "graph": {"name": "图", "parent_id": "root", "category": "图"},
    "graph.bfs": {"name": "图广度优先搜索", "parent_id": "graph", "category": "图"},
    "graph.dfs": {"name": "图深度优先搜索", "parent_id": "graph", "category": "图"},
    "graph.shortest_path": {"name": "最短路径", "parent_id": "graph", "category": "图"},
    "graph.shortest_path.dijkstra": {"name": "Dijkstra 最短路径", "parent_id": "graph.shortest_path", "category": "图"},
    "dp": {"name": "动态规划", "parent_id": "root", "category": "动态规划"},
    "dp.linear": {"name": "线性 DP", "parent_id": "dp", "category": "动态规划"},
    "dp.knapsack": {"name": "背包 DP", "parent_id": "dp", "category": "动态规划"},
    "backtracking": {"name": "回溯算法", "parent_id": "root", "category": "回溯算法"},
    "backtracking.subsets": {"name": "子集型回溯", "parent_id": "backtracking", "category": "回溯算法"},
    "backtracking.permutation": {"name": "排列型回溯", "parent_id": "backtracking", "category": "回溯算法"},
    "greedy": {"name": "贪心算法", "parent_id": "root", "category": "贪心算法"},
}


class ValidationError(ValueError):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except ValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="algorithm-knowledge-saver")
    parser.add_argument("--data-path", default=str(DEFAULT_DATA_PATH), help="JSON data file path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record", help="Save a classified algorithm problem")
    record_parser.add_argument("--question-id")
    record_parser.add_argument("--title")
    record_parser.add_argument("--source")
    record_parser.add_argument("--difficulty")
    record_parser.add_argument("--content")
    record_parser.add_argument("--example", dest="examples", action="append")
    record_parser.add_argument("--user-code")
    record_parser.add_argument("--user-idea")
    record_parser.add_argument("--summary", required=True)
    record_parser.add_argument("--primary-node", required=True)
    record_parser.add_argument("--primary-knowledge", required=True)
    record_parser.add_argument("--graph-path", required=True)
    record_parser.add_argument("--secondary-node", dest="secondary_nodes", action="append")
    record_parser.add_argument("--tag", dest="tags", action="append")
    record_parser.add_argument("--confidence", type=int)
    record_parser.add_argument("--candidate-algorithm", dest="candidate_algorithms", action="append")
    record_parser.add_argument("--recommended-algorithm")
    record_parser.add_argument("--time-complexity")
    record_parser.add_argument("--space-complexity")
    record_parser.add_argument("--visualization-type")
    record_parser.add_argument("--visualization-step", dest="visualization_steps", action="append")
    record_parser.add_argument("--status", choices=sorted(STATUSES), default="learning")
    record_parser.add_argument("--completion", help="independent, hinted, answer_read, code_reviewed, unknown, etc.")
    record_parser.add_argument("--correct", action="store_true")
    record_parser.add_argument("--independent", action="store_true")
    record_parser.add_argument("--mistake", dest="mistakes", action="append")
    record_parser.add_argument("--review-count", type=int, default=0)
    record_parser.add_argument("--mastery-delta", type=int)
    record_parser.add_argument("--note")
    record_parser.add_argument("--yes", action="store_true", help="Overwrite without prompting")
    record_parser.set_defaults(handler=handle_record)

    get_parser = subparsers.add_parser("get", help="Get a saved question record")
    get_parser.add_argument("record_id")
    get_parser.set_defaults(handler=handle_get)

    list_parser = subparsers.add_parser("list", help="List saved questions")
    list_parser.set_defaults(handler=handle_list)

    progress_parser = subparsers.add_parser("progress", help="Show knowledge-node progress")
    progress_parser.set_defaults(handler=handle_progress)

    graph_parser = subparsers.add_parser("graph", help="Export renderable graph JSON")
    graph_parser.add_argument("--view", choices=["all", "current", "weak", "learning", "mastered", "unlearned", "recent", "progress"], default="all")
    graph_parser.add_argument("--highlight-node")
    graph_parser.add_argument("--include-problems", action="store_true")
    graph_parser.add_argument("--limit", type=int, default=20)
    graph_parser.set_defaults(handler=handle_graph)

    delete_parser = subparsers.add_parser("delete", help="Delete a saved question record")
    delete_parser.add_argument("record_id")
    delete_parser.add_argument("--yes", action="store_true", help="Delete without prompting")
    delete_parser.set_defaults(handler=handle_delete)

    return parser


def handle_record(args: argparse.Namespace) -> int:
    data_path = Path(args.data_path)
    data = load_data(data_path)
    record = normalize_record(vars(args))
    record_id = record["record_id"]
    exists = record_id in data["questions"]

    if exists and not args.yes and not confirm(f"Record {record_id} already exists. Overwrite?"):
        print(f"Skipped record {record_id}.")
        return 1

    previous_record = data["questions"].get(record_id)
    previous_progress = snapshot_progress(data)
    data["questions"][record_id] = record
    rebuild_progress(data)
    graph_update = build_graph_update(data, record, previous_progress)
    save_data(data_path, data)
    print(json.dumps(graph_update, ensure_ascii=False, indent=2))
    return 0


def handle_get(args: argparse.Namespace) -> int:
    record = load_data(Path(args.data_path))["questions"].get(args.record_id)
    if record is None:
        print(f"Record {args.record_id} was not found.")
        return 1
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def handle_list(args: argparse.Namespace) -> int:
    questions = load_data(Path(args.data_path))["questions"]
    if not questions:
        print("No questions saved yet.")
        return 0
    rows = []
    for record in sorted(questions.values(), key=lambda item: item.get("created_at", "")):
        rows.append(
            [
                record["record_id"],
                record.get("title") or "(untitled)",
                record["primary_node"],
                record.get("status", "learning"),
            ]
        )
    print_table(["record_id", "title", "primary_node", "status"], rows)
    return 0


def handle_progress(args: argparse.Namespace) -> int:
    progress = load_data(Path(args.data_path))["progress"]
    if not progress:
        print("No progress recorded yet.")
        return 0
    rows = []
    for node_id, item in sorted(progress.items()):
        rows.append([node_id, item["status"], str(item["problem_count"]), str(item["mastery_score"]), item["updated_at"]])
    print_table(["node_id", "status", "problems", "score", "updated_at"], rows)
    return 0


def handle_graph(args: argparse.Namespace) -> int:
    data = load_data(Path(args.data_path))
    graph = build_graph_payload(
        data,
        view=args.view,
        highlight_node=args.highlight_node,
        include_problems=args.include_problems,
        limit=args.limit,
    )
    print(json.dumps(graph, ensure_ascii=False, indent=2))
    return 0


def handle_delete(args: argparse.Namespace) -> int:
    data_path = Path(args.data_path)
    data = load_data(data_path)
    if args.record_id not in data["questions"]:
        print(f"Record {args.record_id} was not found.")
        return 1
    if not args.yes and not confirm(f"Delete record {args.record_id}?"):
        print("Delete cancelled.")
        return 1
    del data["questions"][args.record_id]
    rebuild_progress(data)
    save_data(data_path, data)
    print(f"Deleted record {args.record_id}.")
    return 0


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    content = clean_optional(raw.get("content"))
    user_code = clean_optional(raw.get("user_code"))
    summary = required_text(raw.get("summary"), "summary")
    primary_node = required_text(raw.get("primary_node"), "primary_node")
    primary_knowledge = required_text(raw.get("primary_knowledge"), "primary_knowledge")
    graph_path = required_text(raw.get("graph_path"), "graph_path")
    status = required_text(raw.get("status") or "learning", "status")

    if status not in STATUSES:
        raise ValidationError("status must be one of: unlearned, weak, learning, mastered.")

    base = raw.get("question_id") or content or user_code or summary
    record_id = clean_optional(raw.get("question_id")) or make_record_id(str(base))
    mastery_delta = raw.get("mastery_delta")
    if mastery_delta is None:
        mastery_delta = default_mastery_delta(status, raw)

    record: dict[str, Any] = {
        "record_id": record_id,
        "type": "problem",
        "question_id": clean_optional(raw.get("question_id")),
        "title": clean_optional(raw.get("title")),
        "source": clean_optional(raw.get("source")),
        "difficulty": clean_optional(raw.get("difficulty")),
        "summary": summary,
        "primary_node": primary_node,
        "primary_knowledge": primary_knowledge,
        "graph_path": graph_path,
        "secondary_nodes": clean_list(raw.get("secondary_nodes")),
        "tags": clean_list(raw.get("tags")),
        "confidence": normalize_confidence(raw.get("confidence")),
        "candidate_algorithms": clean_list(raw.get("candidate_algorithms")),
        "recommended_algorithm": clean_optional(raw.get("recommended_algorithm")),
        "time_complexity": clean_optional(raw.get("time_complexity")),
        "space_complexity": clean_optional(raw.get("space_complexity")),
        "status": status,
        "completion_status": clean_optional(raw.get("completion")) or "unknown",
        "is_correct": bool(raw.get("correct")),
        "is_independent": bool(raw.get("independent")),
        "mistakes": clean_list(raw.get("mistakes")),
        "review_count": max(0, int(raw.get("review_count") or 0)),
        "mastery_delta": int(mastery_delta),
        "note": clean_optional(raw.get("note")),
        "created_at": now(),
        "updated_at": now(),
    }

    optional_fields = {
        "content": content,
        "examples": clean_list(raw.get("examples")),
        "user_code": user_code,
        "user_idea": clean_optional(raw.get("user_idea")),
        "visualization": normalize_visualization(raw),
    }
    for key, value in optional_fields.items():
        if value:
            record[key] = value

    return {key: value for key, value in record.items() if value is not None and value != []}


def normalize_visualization(raw: dict[str, Any]) -> dict[str, Any]:
    steps = []
    for item in clean_list(raw.get("visualization_steps")):
        try:
            parsed = json.loads(item)
        except json.JSONDecodeError:
            parsed = {"text": item}
        steps.append(parsed)
    visual_type = clean_optional(raw.get("visualization_type"))
    if not visual_type and not steps:
        return {}
    return {"type": visual_type or "text", "steps": steps}


def default_mastery_delta(status: str, raw: dict[str, Any]) -> int:
    if status == "weak":
        return 0
    if status == "mastered":
        return 15 if raw.get("independent") and raw.get("correct") else 8
    if status == "learning":
        return 8 if raw.get("independent") or raw.get("correct") else 5
    return 0


def snapshot_progress(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return json.loads(json.dumps(data.get("progress", {}), ensure_ascii=False))


def rebuild_progress(data: dict[str, Any]) -> None:
    data["progress"] = {}
    for record in data["questions"].values():
        apply_record_to_progress(data, record)


def apply_record_to_progress(data: dict[str, Any], record: dict[str, Any]) -> None:
    node_roles: dict[str, str] = {}
    for node_id in path_to_root(record["primary_node"]):
        if node_id != "root":
            node_roles[node_id] = "ancestor"
    for node_id in record.get("secondary_nodes", []):
        node_roles[node_id] = "secondary"
    node_roles[record["primary_node"]] = "primary"

    for node_id, role in node_roles.items():
        node = KNOWLEDGE_NODES.get(node_id, {"name": node_id, "parent_id": None, "category": "custom"})
        item = data["progress"].setdefault(
            node_id,
            {
                "node_id": node_id,
                "name": node["name"],
                "status": "unlearned",
                "mastery_score": 0,
                "problem_count": 0,
                "correct_count": 0,
                "independent_count": 0,
                "review_count": 0,
                "mistake_count": 0,
                "records": [],
                "mistakes": [],
                "created_at": now(),
                "updated_at": now(),
            },
        )
        if record["record_id"] not in item["records"]:
            item["records"].append(record["record_id"])
            item["problem_count"] += 1
            item["review_count"] += int(record.get("review_count", 0))
            item["correct_count"] += 1 if record.get("is_correct") else 0
            item["independent_count"] += 1 if record.get("is_independent") else 0
            mistakes = record.get("mistakes", [])
            item["mistake_count"] += len(mistakes)
            item["mistakes"].extend(mistakes)
            if role == "primary":
                item["mastery_score"] = clamp(item["mastery_score"] + int(record.get("mastery_delta", 0)), 0, 100)
            elif role == "secondary":
                item["mastery_score"] = clamp(item["mastery_score"] + max(1, int(record.get("mastery_delta", 0)) // 3), 0, 100)
            else:
                item["mastery_score"] = clamp(item["mastery_score"] + max(1, int(record.get("mastery_delta", 0)) // 4), 0, 100)
        item["status"] = derive_status(item, record.get("status", "learning"))
        item["updated_at"] = now()


def derive_status(progress: dict[str, Any], incoming_status: str) -> str:
    if incoming_status == "weak" or progress["mistake_count"] > progress["correct_count"] + progress["independent_count"]:
        return "weak"
    if incoming_status == "mastered" and progress["independent_count"] >= 3 and progress["correct_count"] >= 3 and progress["mastery_score"] >= 80:
        return "mastered"
    if progress["problem_count"] > 0:
        return "learning"
    return "unlearned"


def build_graph_update(data: dict[str, Any], record: dict[str, Any], previous_progress: dict[str, dict[str, Any]]) -> dict[str, Any]:
    primary_node = record["primary_node"]
    highlight_path = path_to_root(primary_node)
    graph = build_graph_payload(data, view="current", highlight_node=primary_node, include_problems=True)
    return {
        "classification": {
            "primary_node_id": primary_node,
            "secondary_node_ids": record.get("secondary_nodes", []),
            "confidence": None if record.get("confidence") is None else record["confidence"] / 100,
        },
        "highlight_path": highlight_path,
        "node_updates": build_node_updates(data, previous_progress, highlight_path, record),
        "problem_node": build_problem_node(record, highlighted=True),
        "nodes": graph["nodes"],
        "edges": graph["edges"],
        "view": graph["view"],
        "status_colors": STATUS_COLOR,
    }


def build_node_updates(
    data: dict[str, Any],
    previous_progress: dict[str, dict[str, Any]],
    highlight_path: list[str],
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    changed_ids = set(highlight_path) | set(record.get("secondary_nodes", []))
    changed_ids.discard("root")
    updates = []
    for node_id in sorted(changed_ids, key=node_depth):
        current = data["progress"].get(node_id, {})
        old = previous_progress.get(node_id, {})
        updates.append(
            {
                "id": node_id,
                "old_status": old.get("status", "unlearned"),
                "new_status": current.get("status", "unlearned"),
                "old_score": old.get("mastery_score", 0),
                "new_score": current.get("mastery_score", 0),
                "problem_count_delta": current.get("problem_count", 0) - old.get("problem_count", 0),
            }
        )
    return updates


def build_graph_payload(
    data: dict[str, Any],
    *,
    view: str,
    highlight_node: str | None,
    include_problems: bool,
    limit: int = 20,
) -> dict[str, Any]:
    highlight_path = path_to_root(highlight_node) if highlight_node else []
    visible_knowledge_ids = visible_node_ids(data, view, highlight_path, limit)
    nodes = [build_knowledge_node(data, node_id, highlight_path) for node_id in sorted(visible_knowledge_ids, key=node_depth)]
    edges = build_knowledge_edges(visible_knowledge_ids, highlight_path)

    if include_problems:
        problem_nodes, problem_edges = build_problem_nodes_and_edges(data, visible_knowledge_ids, highlight_node, limit)
        nodes.extend(problem_nodes)
        edges.extend(problem_edges)

    return {
        "view": view,
        "highlight_path": highlight_path,
        "status_colors": STATUS_COLOR,
        "nodes": nodes,
        "edges": edges,
        "interactions": {
            "expand_collapse": True,
            "node_detail": True,
            "status_filter": ["unlearned", "weak", "learning", "mastered"],
            "views": ["all", "current", "weak", "learning", "mastered", "unlearned", "recent", "progress"],
            "zoom": True,
            "pan": True,
            "auto_center_current": True,
        },
        "recommended_renderer": "React Flow + Dagre",
        "fallback_renderer": "Mermaid",
    }


def visible_node_ids(data: dict[str, Any], view: str, highlight_path: list[str], limit: int) -> set[str]:
    if view == "all":
        return set(KNOWLEDGE_NODES)
    if view == "current":
        ids = set(highlight_path or ["root"])
        for node_id in list(ids):
            ids.update(children_of(node_id))
        return ids
    if view in STATUSES:
        ids = {"root"}
        for node_id, progress in data["progress"].items():
            if progress.get("status") == view:
                ids.update(path_to_root(node_id))
                ids.update(children_of(node_id))
        return ids
    if view == "recent":
        ids = {"root"}
        recent = sorted(data["questions"].values(), key=lambda item: item.get("created_at", ""), reverse=True)[:limit]
        for record in recent:
            ids.update(path_to_root(record["primary_node"]))
        return ids
    if view == "progress":
        ids = {"root"}
        for node_id in data["progress"]:
            ids.update(path_to_root(node_id))
        return ids
    return set(KNOWLEDGE_NODES)


def build_knowledge_node(data: dict[str, Any], node_id: str, highlight_path: list[str]) -> dict[str, Any]:
    base = KNOWLEDGE_NODES[node_id]
    progress = data["progress"].get(node_id, {})
    status = progress.get("status", "unlearned")
    return {
        "id": node_id,
        "type": "knowledge",
        "name": base["name"],
        "parent_id": base["parent_id"],
        "category": base["category"],
        "level": node_depth(node_id),
        "status": status,
        "status_color": STATUS_COLOR[status],
        "mastery_score": progress.get("mastery_score", 0),
        "problem_count": progress.get("problem_count", 0),
        "correct_count": progress.get("correct_count", 0),
        "independent_count": progress.get("independent_count", 0),
        "review_count": progress.get("review_count", 0),
        "mistake_count": progress.get("mistake_count", 0),
        "mistakes": progress.get("mistakes", []),
        "records": progress.get("records", []),
        "is_highlighted": node_id in highlight_path,
        "is_expanded": node_id in highlight_path or node_depth(node_id) <= 2,
    }


def build_knowledge_edges(visible_ids: set[str], highlight_path: list[str]) -> list[dict[str, Any]]:
    edges = []
    for node_id in visible_ids:
        parent_id = KNOWLEDGE_NODES[node_id]["parent_id"]
        if parent_id and parent_id in visible_ids:
            edges.append(
                {
                    "source": parent_id,
                    "target": node_id,
                    "relation": "contains",
                    "highlighted": parent_id in highlight_path and node_id in highlight_path,
                }
            )
    return edges


def build_problem_nodes_and_edges(
    data: dict[str, Any],
    visible_ids: set[str],
    highlight_node: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = []
    edges = []
    records = sorted(data["questions"].values(), key=lambda item: item.get("created_at", ""), reverse=True)
    count = 0
    for record in records:
        primary = record["primary_node"]
        if primary not in visible_ids:
            continue
        if count >= limit:
            break
        highlighted = bool(highlight_node and primary == highlight_node)
        nodes.append(build_problem_node(record, highlighted=highlighted))
        edges.append({"source": primary, "target": record["record_id"], "relation": "solved_by", "highlighted": highlighted})
        for secondary in record.get("secondary_nodes", []):
            if secondary in visible_ids:
                edges.append({"source": record["record_id"], "target": secondary, "relation": "uses", "highlighted": False})
        count += 1
    return nodes, edges


def build_problem_node(record: dict[str, Any], *, highlighted: bool) -> dict[str, Any]:
    return {
        "id": record["record_id"],
        "type": "problem",
        "title": record.get("title") or record["summary"],
        "summary": record["summary"],
        "primary_node": record["primary_node"],
        "secondary_nodes": record.get("secondary_nodes", []),
        "difficulty": record.get("difficulty"),
        "completion_status": record.get("completion_status", "unknown"),
        "mastery_delta": record.get("mastery_delta", 0),
        "is_highlighted": highlighted,
        "is_collapsed": True,
    }


def path_to_root(node_id: str | None) -> list[str]:
    if not node_id or node_id not in KNOWLEDGE_NODES:
        return []
    path = []
    current = node_id
    while current:
        path.append(current)
        current = KNOWLEDGE_NODES[current]["parent_id"]
    return list(reversed(path))


def children_of(node_id: str) -> set[str]:
    return {child_id for child_id, item in KNOWLEDGE_NODES.items() if item["parent_id"] == node_id}


def node_depth(node_id: str) -> int:
    return max(0, len(path_to_root(node_id)) - 1)


def load_data(path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        data = empty_data()
        save_data(path, data)
        return data
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        data = empty_data()
        save_data(path, data)
        return data
    if not isinstance(data, dict):
        data = empty_data()
    data.setdefault("questions", {})
    data.setdefault("progress", {})
    data.setdefault("version", 2)
    return data


def save_data(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def empty_data() -> dict[str, Any]:
    return {"version": 2, "questions": {}, "progress": {}}


def make_record_id(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"problem_{digest}"


def normalize_confidence(value: Any) -> int | None:
    if value is None:
        return None
    confidence = int(value)
    if confidence < 0 or confidence > 100:
        raise ValidationError("confidence must be between 0 and 100.")
    return confidence


def clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def required_text(value: Any, name: str) -> str:
    text = clean_optional(value)
    if text is None:
        raise ValidationError(f"{name} is required.")
    return text


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def confirm(message: str) -> bool:
    answer = input(message + " [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    all_rows = [headers, *rows]
    widths = [max(len(str(row[index])) for row in all_rows) for index in range(len(headers))]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))


if __name__ == "__main__":
    raise SystemExit(main())
