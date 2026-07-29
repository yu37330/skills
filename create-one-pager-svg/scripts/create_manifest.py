#!/usr/bin/env python3
"""成果物のサイズとSHA-256を記録したManifestを生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="成果物Manifestを生成します。")
    parser.add_argument("directory", type=Path, help="成果物フォルダ")
    parser.add_argument("--output", type=Path, default=Path("manifest.json"), help="出力先。相対パスは成果物フォルダ基準")
    args = parser.parse_args()

    directory = args.directory.resolve()
    if not directory.is_dir():
        parser.error(f"成果物フォルダが見つかりません: {directory}")
    output = args.output if args.output.is_absolute() else directory / args.output
    output = output.resolve()
    files = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and path.resolve() != output:
            files.append({
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "manifest_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "directory": str(directory),
        "files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(output), "files": len(files)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

