#!/usr/bin/env python3
"""v7互換CLI。component/frame/content/tokensを含むJSONからSDPM slide JSON要素を生成する。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdpm_native_components import build_component, list_components  # noqa: E402


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def build_file(input_path: Path, output_path: Path) -> int:
    source = json.loads(input_path.read_text(encoding="utf-8-sig"))
    result = build_component(
        source["component"],
        source["frame"],
        source.get("content", {}),
        theme=source.get("theme", "base"),
        variant=source.get("variant", "primary"),
        token_overrides=source.get("tokens", {}),
        layout_slot=source.get("layoutSlot"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Native Componentを生成しました: {output_path}")
    return 0


def main() -> int:
    # v7互換: python scripts/native_components.py input.json output.json
    if len(sys.argv) == 3 and sys.argv[1] not in {"build", "list", "-h", "--help"}:
        return build_file(Path(sys.argv[1]), Path(sys.argv[2]))

    parser = argparse.ArgumentParser(description="SDPM Native Component Library v2")
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build", help="componentを生成")
    build_parser.add_argument("input", type=Path)
    build_parser.add_argument("output", type=Path)
    sub.add_parser("list", help="component一覧")
    args = parser.parse_args()
    if args.command == "list":
        print("\n".join(list_components()))
        return 0
    return build_file(args.input, args.output)


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
