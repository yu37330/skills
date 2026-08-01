#!/usr/bin/env python3
"""比較成果物をランダムな候補名へ複製し、Blind Review用セットを作る。"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Blind Review用候補セットを作成します")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("artifacts", nargs="+", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    if len(args.artifacts) < 2:
        print("比較対象を2件以上指定してください。")
        return 1
    for artifact in args.artifacts:
        if not artifact.is_file():
            print(f"ファイルが見つかりません: {artifact}")
            return 1
    rng = random.Random(args.seed)
    shuffled = list(args.artifacts)
    rng.shuffle(shuffled)
    review_dir = args.output_dir / "review-set"
    review_dir.mkdir(parents=True, exist_ok=True)
    key: list[dict] = []
    public: list[dict] = []
    for index, source in enumerate(shuffled):
        label = chr(ord("A") + index)
        destination = review_dir / f"candidate-{label}{source.suffix.lower()}"
        shutil.copy2(source, destination)
        digest = sha256(destination)
        public.append({"candidate": label, "file": destination.name, "sha256": digest})
        key.append({"candidate": label, "source": str(source.resolve()), "source_sha256": sha256(source)})
    (review_dir / "manifest.json").write_text(json.dumps({"version": 1, "candidates": public}, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "blind-key.json").write_text(json.dumps({"version": 1, "seed": args.seed, "mapping": key}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Blind Reviewセットを作成しました: {review_dir}")
    return 0


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
