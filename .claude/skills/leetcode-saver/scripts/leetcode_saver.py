#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


DIFFICULTIES = {"easy", "medium", "hard"}
STATUSES = {"mastered", "fuzzy", "weak"}
DEFAULT_DATA_PATH = Path("data") / "leetcode_problems.json"


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
    parser = argparse.ArgumentParser(prog="leetcode-saver")
    parser.add_argument("--data-path", default=str(DEFAULT_DATA_PATH), help="JSON data file path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("id")
    add_parser.add_argument("title")
    add_common_options(add_parser)
    add_parser.add_argument("--yes", action="store_true", help="Overwrite without prompting")
    add_parser.set_defaults(handler=handle_add)

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("id")
    get_parser.set_defaults(handler=handle_get)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(handler=handle_list)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("id")
    update_parser.add_argument("--title")
    add_common_options(update_parser)
    update_parser.set_defaults(handler=handle_update)

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id")
    delete_parser.add_argument("--yes", action="store_true", help="Delete without prompting")
    delete_parser.set_defaults(handler=handle_delete)

    return parser


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title-cn", dest="title_cn")
    parser.add_argument("--difficulty", choices=sorted(DIFFICULTIES))
    parser.add_argument("--category")
    parser.add_argument("--topic")
    parser.add_argument("--content", help="Problem statement content")
    parser.add_argument("--example", dest="examples", action="append", help="Problem example; repeat for multiple examples")
    parser.add_argument("--status", choices=sorted(STATUSES), default=None)
    parser.add_argument("--note")


def handle_add(args: argparse.Namespace) -> int:
    problem = normalize_problem(
        {
            "id": args.id,
            "title": args.title,
            "title_cn": args.title_cn,
            "difficulty": required_arg(args.difficulty, "difficulty"),
            "category": required_arg(args.category, "category"),
            "topic": required_arg(args.topic, "topic"),
            "content": args.content,
            "examples": args.examples,
            "status": args.status or "fuzzy",
            "note": args.note or "",
            "added_at": now(),
        }
    )
    data = load_data(Path(args.data_path))
    exists = problem["id"] in data["problems"]
    if exists and not args.yes and not confirm(f"Problem {problem['id']} already exists. Overwrite?"):
        print(f"Skipped problem {problem['id']}.")
        return 1
    data["problems"][problem["id"]] = problem
    save_data(Path(args.data_path), data)
    print(f"Saved problem {problem['id']}: {problem['title']}")
    return 0


def handle_get(args: argparse.Namespace) -> int:
    problem = load_data(Path(args.data_path))["problems"].get(str(args.id))
    if problem is None:
        print(f"Problem {args.id} was not found.")
        return 1
    for key in ("id", "title", "title_cn", "difficulty", "category", "topic", "status", "note", "added_at"):
        print(f"{key}: {'' if problem.get(key) is None else problem.get(key)}")
    if problem.get("content"):
        print(f"content:\n{problem['content']}")
    if problem.get("examples"):
        print("examples:")
        for index, example in enumerate(problem["examples"], start=1):
            print(f"[{index}]\n{example}")
    return 0


def handle_list(args: argparse.Namespace) -> int:
    problems = load_data(Path(args.data_path))["problems"]
    if not problems:
        print("No problems saved yet.")
        return 0
    rows = [
        [item["id"], item["title"], item["difficulty"], item["status"]]
        for item in sorted(problems.values(), key=lambda item: sort_key(str(item.get("id", ""))))
    ]
    print_table(["id", "title", "difficulty", "status"], rows)
    return 0


def handle_update(args: argparse.Namespace) -> int:
    data_path = Path(args.data_path)
    data = load_data(data_path)
    problem_id = str(args.id)
    existing = data["problems"].get(problem_id)
    if existing is None:
        print(f"Problem {problem_id} was not found.")
        return 1

    updates: dict[str, Any] = {}
    for key in ("title", "title_cn", "difficulty", "category", "topic", "content", "examples", "status", "note"):
        value = getattr(args, key)
        if value is not None:
            updates[key] = value
    if not updates:
        print("Nothing to update.")
        return 1

    merged = normalize_problem({**existing, **updates, "id": problem_id})
    data["problems"][problem_id] = merged
    save_data(data_path, data)
    print(f"Updated problem {problem_id}.")
    return 0


def handle_delete(args: argparse.Namespace) -> int:
    data_path = Path(args.data_path)
    data = load_data(data_path)
    problem_id = str(args.id)
    if problem_id not in data["problems"]:
        print(f"Problem {problem_id} was not found.")
        return 1
    if not args.yes and not confirm(f"Delete problem {problem_id}?"):
        print("Delete cancelled.")
        return 1
    del data["problems"][problem_id]
    save_data(data_path, data)
    print(f"Deleted problem {problem_id}.")
    return 0


def normalize_problem(problem: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "id": str(problem.get("id", "")).strip(),
        "title": str(problem.get("title", "")).strip(),
        "title_cn": clean_optional(problem.get("title_cn")),
        "difficulty": str(problem.get("difficulty", "")).strip().lower(),
        "category": str(problem.get("category", "")).strip(),
        "topic": str(problem.get("topic", "")).strip(),
        "status": str(problem.get("status", "fuzzy")).strip().lower(),
        "note": str(problem.get("note", "")),
        "added_at": str(problem.get("added_at", "")).strip() or now(),
    }
    content = clean_optional(problem.get("content"))
    examples = clean_examples(problem.get("examples"))
    if content is not None:
        normalized["content"] = content
    if examples:
        normalized["examples"] = examples
    validate_problem(normalized)
    return normalized


def validate_problem(problem: dict[str, Any]) -> None:
    if not problem["id"]:
        raise ValidationError("id is required.")
    if not problem["title"]:
        raise ValidationError("title is required.")
    if problem["difficulty"] not in DIFFICULTIES:
        raise ValidationError("difficulty must be one of: easy, medium, hard.")
    if not problem["category"]:
        raise ValidationError("category is required.")
    if not problem["topic"]:
        raise ValidationError("topic is required.")
    if problem["status"] not in STATUSES:
        raise ValidationError("status must be one of: mastered, fuzzy, weak.")


def load_data(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        save_data(path, {"problems": {}})
        return {"problems": {}}
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        data = {"problems": {}}
        save_data(path, data)
        return data
    if not isinstance(data, dict) or not isinstance(data.get("problems"), dict):
        data = {"problems": {}}
        save_data(path, data)
    return data


def save_data(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def clean_examples(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def required_arg(value: str | None, name: str) -> str:
    if value is None or not value.strip():
        raise ValidationError(f"{name} is required.")
    return value


def confirm(message: str) -> bool:
    answer = input(message + " [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sort_key(value: str) -> tuple[int, int | str]:
    return (0, int(value)) if value.isdigit() else (1, value)


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    all_rows = [headers, *rows]
    widths = [max(len(str(row[index])) for row in all_rows) for index in range(len(headers))]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))


if __name__ == "__main__":
    raise SystemExit(main())
