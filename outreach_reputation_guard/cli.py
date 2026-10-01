"""Local CLI; no network access or sending capability."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from .core import GuardError, evaluate, fields
from .fixtures import generate
from .report import render


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GuardError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc
    except (OSError, UnicodeError) as exc:
        raise GuardError(f"InputError: {path}: line 1: {exc}") from exc


def load_input(directory):
    path = Path(directory)
    if not path.is_dir():
        raise GuardError(f"MissingInput: {path}; use org fixtures --out demo")
    files = list(path.iterdir())
    if not files:
        return evaluate({"synthetic": False, "as_of": "2000-01-01", "daily_limit": 0, "already_sent": 0, "min_score": 0}, [])
    for name in ("policy.json", "records.json"):
        if not (path / name).is_file():
            raise GuardError(f"MissingInput: {path / name}; use org fixtures --out demo")
    policy = read_json(path / "policy.json")
    payload = read_json(path / "records.json")
    fields(payload, {"synthetic", "label", "records"}, "records.json")
    if type(payload["synthetic"]) is not bool or not isinstance(payload["label"], str):
        raise GuardError("SchemaError: records.json.synthetic/label: expected boolean/string")
    if not isinstance(payload["records"], list):
        raise GuardError("SchemaError: records.json.records: expected array")
    if payload["synthetic"] and any(isinstance(row, dict) and row.get("synthetic") is False for row in payload["records"]):
        raise GuardError("SchemaError: records.json.synthetic: synthetic container has real record")
    try:
        return evaluate(policy, payload["records"])
    except GuardError as exc:
        raise GuardError(f"{path}: {exc}") from exc


def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(text)
        os.replace(temporary, path)
    except OSError as exc:
        raise GuardError(f"WriteError: {path}: {exc}") from exc
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="org", description="Compute local outreach decisions from explicit facts. Never sends messages.")
    sub = parser.add_subparsers(dest="command", required=True)
    fixture = sub.add_parser("fixtures", help="Generate labelled synthetic ground truth", epilog="Example: org fixtures --out demo")
    fixture.add_argument("--out", required=True)
    for command, description in (("run", "Compute and save all decisions"), ("screen", "Show per-record qualification and suppression decisions"), ("budget", "Show remaining daily capacity from supplied counts")):
        child = sub.add_parser(command, help=description, description=description, epilog=f"Example: org {command} --input demo")
        child.add_argument("--input", required=True)
        child.add_argument("--state", default=".org/results.json")
    report = sub.add_parser("report", help="Render results with declared provenance", epilog="Example: org report --format md")
    report.add_argument("--format", choices=("md", "json"), default="md")
    report.add_argument("--state", default=".org/results.json")
    report.add_argument("--input", help="Compute directly from an input directory")
    report.add_argument("--out", help="Atomically write a report instead of stdout")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            output = "SYNTHETIC: generated 200 labelled records and hand-computed expectations.\n"
        elif args.command == "report":
            result = load_input(args.input) if args.input else read_json(Path(args.state))
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
                output = f"Report written: {args.out}\n"
        else:
            result = load_input(args.input)
            if args.command == "run":
                atomic_write(args.state, render(result, "json"))
                output = render(result, "json")
            elif args.command == "screen":
                output = render(result, "json")
            else:
                remaining = max(0, result["policy"]["daily_limit"] - result["policy"]["already_sent"] - result["totals"]["allowed"])
                output = render(result, "json") + f"Computed remaining daily slots after approved queue: {remaining}\n"
        sys.stdout.write(output.replace(chr(0x2014), "-"))
        return 0
    except (KeyError, TypeError, AttributeError) as exc:
        sys.stderr.write(f"SchemaError: saved report state: {str(exc).replace(chr(0x2014), '-')}\n")
        return 2
    except (GuardError, OSError) as exc:
        message = str(exc).replace(chr(0x2014), "-")
        sys.stderr.write(message + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
