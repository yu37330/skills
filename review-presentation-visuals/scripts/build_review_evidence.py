#!/usr/bin/env python3
"""Review v6〜v8に必要な機械証跡を一括生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml


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


def run(command: list[str], allowed: set[int] = {0}) -> int:
    result = subprocess.run(command, check=False)
    if result.returncode not in allowed:
        raise RuntimeError(f"コマンドに失敗しました: {command} exit={result.returncode}")
    return result.returncode


def relative(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def main() -> int:
    parser = argparse.ArgumentParser(description="Review v6〜v8の機械証跡を一括生成します")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("png_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--renderer", required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--visual-plan", type=Path, help="指定時はReview v7/v8のDesign System監査を追加します")
    parser.add_argument("--repetition-policy", choices=["strict", "balanced", "consistent"], default="strict")
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parent
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    audit = output / "pptx-audit.json"
    lint = output / "japanese-lint.json"
    metrics = output / "visual-metrics.json"
    manifest = output / "render-manifest.json"
    diff = output / "content-diff.json"
    design_system = output / "design-system-audit.json"

    run([sys.executable, str(scripts / "audit_pptx.py"), str(args.pptx), str(audit)])
    lint_exit = run([sys.executable, str(scripts / "lint_japanese_pptx.py"), str(args.pptx), str(lint)], {0, 1})
    run([sys.executable, str(scripts / "extract_visual_metrics.py"), str(args.pptx), str(args.png_dir), str(metrics)])
    audit_data = json.loads(audit.read_text(encoding="utf-8"))
    slide_count = audit_data["slide_count"]
    run([
        sys.executable, str(scripts / "build_render_manifest.py"), str(args.png_dir), str(manifest),
        "--renderer", args.renderer, "--pptx", str(args.pptx), "--expected-slides", str(slide_count),
    ])
    diff_exit = 0
    if args.baseline:
        diff_exit = run([sys.executable, str(scripts / "diff_pptx.py"), str(args.baseline), str(args.pptx), str(diff)], {0, 1})
    design_exit = 0
    visual_plan_version = None
    if args.visual_plan:
        visual_plan_data = yaml.safe_load(args.visual_plan.resolve().read_text(encoding="utf-8-sig"))
        visual_plan_version = visual_plan_data.get("version") if isinstance(visual_plan_data, dict) else None
        design_exit = run([
            sys.executable, str(scripts / "audit_design_system.py"), str(args.pptx),
            str(args.visual_plan), str(design_system), "--min-token-match-ratio", "0.7",
        ], {0, 1})

    reviewed = list(range(1, slide_count + 1))
    strict_similarity = 0.4 if slide_count >= 6 else 0.67 if slide_count >= 3 else 1.0
    similarity_limit = strict_similarity if args.repetition_policy == "strict" else max(
        strict_similarity, 0.6 if args.repetition_policy == "balanced" else 0.8
    )
    bundle = {
        "version": 3 if visual_plan_version == 8 else 2 if args.visual_plan else 1,
        "render_evidence": {
            "manifest": relative(manifest, output),
            "renderer": args.renderer,
            "full_size_reviewed_slides": reviewed,
            "edge_reviewed_slides": reviewed,
        },
        "machine_evidence": {
            "audit_report": {"path": relative(audit, output), "sha256": sha256(audit)},
            "visual_metrics_report": {"path": relative(metrics, output), "sha256": sha256(metrics)},
            "japanese_lint_report": {"path": relative(lint, output), "sha256": sha256(lint)},
            "content_diff_report": (
                {"required": True, "path": relative(diff, output), "sha256": sha256(diff)}
                if args.baseline else {"required": False}
            ),
            **({"design_system_report": {"path": relative(design_system, output), "sha256": sha256(design_system)}} if args.visual_plan else {}),
            "thresholds": {
                "min_average_native_element_ratio": 0.8,
                "max_high_similarity_cluster_ratio": similarity_limit,
                **({"min_design_token_match_ratio": 0.7} if args.visual_plan else {}),
                **({"max_gradient_fill_count": 0, "max_glow_effect_count": 0} if visual_plan_version == 8 else {}),
            },
        },
    }
    bundle_path = output / "review-evidence-bundle.json"
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    review_version = "8" if visual_plan_version == 8 else "7" if args.visual_plan else "6"
    print(f"Review v{review_version}証跡を作成しました: {bundle_path}")
    return 0 if lint_exit == 0 and diff_exit == 0 and design_exit == 0 else 1


if __name__ == "__main__":
    configure_utf8_console()
    raise SystemExit(main())
