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
DEFAULT_DATA_PATH = Path("data") / "algorithm_knowledge_graph.json"


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

    previous = data["questions"].get(record_id)
    data["questions"][record_id] = record
    update_progress(data, record, previous)
    save_data(data_path, data)
    print(f"Saved record {record_id} under {record['primary_node']}.")
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
        rows.append([node_id, item["status"], str(item["question_count"]), item["updated_at"]])
    print_table(["node_id", "status", "questions", "updated_at"], rows)
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

    record: dict[str, Any] = {
        "record_id": record_id,
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
        "completion": clean_optional(raw.get("completion")) or "unknown",
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


def update_progress(data: dict[str, Any], record: dict[str, Any], previous: dict[str, Any] | None) -> None:
    if previous and previous.get("primary_node") != record["primary_node"]:
        rebuild_progress(data)
        return

    node_id = record["primary_node"]
    item = data["progress"].setdefault(
        node_id,
        {
            "node_id": node_id,
            "status": "unlearned",
            "question_count": 0,
            "records": [],
            "created_at": now(),
            "updated_at": now(),
        },
    )

    if record["record_id"] not in item["records"]:
        item["records"].append(record["record_id"])
        item["question_count"] += 1

    item["status"] = merge_status(item.get("status", "unlearned"), record["status"])
    item["updated_at"] = now()


def rebuild_progress(data: dict[str, Any]) -> None:
    data["progress"] = {}
    for record in data["questions"].values():
        update_progress(data, record, None)


def merge_status(current: str, incoming: str) -> str:
    rank = {"unlearned": 0, "weak": 1, "learning": 2, "mastered": 3}
    return incoming if rank[incoming] > rank.get(current, 0) else current


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
    data.setdefault("version", 1)
    return data


def save_data(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def empty_data() -> dict[str, Any]:
    return {"version": 1, "questions": {}, "progress": {}}


def make_record_id(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"q_{digest}"


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
