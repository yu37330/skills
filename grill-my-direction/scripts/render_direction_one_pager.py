#!/usr/bin/env python3
"""Direction Specから日本語の1ページSVGを生成する。"""

import argparse
import json
import unicodedata
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


WIDTH = 1600
HEIGHT = 1000
FONT = "'Yu Gothic UI','Noto Sans JP',sans-serif"


def text_units(value: str) -> int:
    """全角を2、半角を1として表示幅を概算する。"""
    return sum(2 if unicodedata.east_asian_width(char) in "WFA" else 1 for char in value)


def wrap_text(value: Any, max_units: int, max_lines: int) -> List[str]:
    """日本語を含む文字列を概算幅で折り返す。"""
    text = " ".join(str(value or "").split())
    if not text:
        return ["—"]

    lines: List[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and text_units(candidate) > max_units:
            lines.append(current.rstrip())
            current = char.lstrip()
            if len(lines) == max_lines:
                break
        else:
            current = candidate
    if len(lines) < max_lines and current:
        lines.append(current.rstrip())

    consumed = "".join(lines)
    if len(consumed) < len(text) and lines:
        last = lines[-1]
        lines[-1] = (last[:-1] if len(last) > 1 else last) + "…"
    return lines or ["—"]


class Svg:
    """SVG要素を順番に組み立てる。"""

    def __init__(self) -> None:
        self.parts: List[str] = []

    def rect(self, x: int, y: int, w: int, h: int, fill: str, stroke: str = "#26334A", radius: int = 18) -> None:
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        )

    def line(self, x1: int, y1: int, x2: int, y2: int, stroke: str = "#334155", width: int = 2) -> None:
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"/>')

    def text(self, x: int, y: int, value: Any, size: int = 22, color: str = "#E5E7EB", weight: int = 400, anchor: str = "start") -> None:
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>'
        )

    def block(self, x: int, y: int, value: Any, max_units: int, max_lines: int, size: int = 20, color: str = "#CBD5E1", weight: int = 400, line_height: int = 29) -> int:
        lines = wrap_text(value, max_units, max_lines)
        for index, line in enumerate(lines):
            self.text(x, y + index * line_height, line, size=size, color=color, weight=weight)
        return y + len(lines) * line_height

    def pill(self, x: int, y: int, label: str, fill: str, color: str = "#F8FAFC", min_width: int = 72) -> int:
        width = max(min_width, 22 + text_units(label) * 9)
        self.rect(x, y, width, 30, fill, stroke=fill, radius=15)
        self.text(x + width // 2, y + 21, label, size=14, color=color, weight=700, anchor="middle")
        return width

    def render(self) -> str:
        body = "\n".join(self.parts)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">\n'
            '<rect width="1600" height="1000" fill="#08111F"/>\n'
            '<defs><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#020617" flood-opacity="0.35"/></filter></defs>\n'
            f'{body}\n</svg>\n'
        )


def list_items(svg: Svg, items: Iterable[Any], x: int, y: int, width_units: int, max_items: int, color: str = "#CBD5E1", lines_each: int = 2, gap: int = 10) -> int:
    """箇条書きを描画して次のY座標を返す。"""
    current = y
    for item in list(items or [])[:max_items]:
        svg.text(x, current, "•", size=22, color="#38BDF8", weight=700)
        end = svg.block(x + 20, current, item, width_units, lines_each, size=17, color=color, line_height=23)
        current = end + gap
    return current


def section_title(svg: Svg, x: int, y: int, number: str, title: str, accent: str = "#38BDF8") -> None:
    svg.pill(x, y - 23, number, accent, "#06111D", min_width=40)
    svg.text(x + 55, y, title, size=22, color="#F8FAFC", weight=700)


def require_mapping(value: Any, name: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} はオブジェクトで指定してください。")
    return value


def mapping_list(value: Any) -> List[Dict[str, Any]]:
    """辞書だけを残した配列を返す。"""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_list(value: Any) -> List[str]:
    """空でない文字列だけを残した配列を返す。"""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def build_direction_graph(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Direction Specからレイアウト非依存の意味グラフを作る。"""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []
    node_ids = set()
    edge_keys = set()

    def add_node(node_id: str, node_type: str, label: Any, **metadata: Any) -> str:
        base_id = str(node_id or node_type).strip()
        unique_id = base_id
        suffix = 2
        while unique_id in node_ids:
            unique_id = f"{base_id}-{suffix}"
            suffix += 1
        node_ids.add(unique_id)
        node = {"id": unique_id, "type": node_type, "label": str(label or "—")}
        node.update({key: value for key, value in metadata.items() if value not in (None, "", [])})
        nodes.append(node)
        return unique_id

    def add_edge(source: str, target: str, relation: str) -> None:
        key = (source, target, relation)
        if source in node_ids and target in node_ids and key not in edge_keys:
            edge_keys.add(key)
            edges.append({"source": source, "target": target, "relation": relation})

    desired_change = spec.get("desired_change") if isinstance(spec.get("desired_change"), dict) else {}
    core_tension = spec.get("core_tension") if isinstance(spec.get("core_tension"), dict) else {}
    current_label = desired_change.get("from") or spec.get("problem") or "現在の状態"
    tension_label = core_tension.get("statement") or spec.get("key_question") or spec.get("problem") or "中心的な葛藤"
    current_id = add_node("current-state", "current_state", current_label)
    tension_id = add_node("core-tension", "tension", tension_label)
    add_edge(current_id, tension_id, "creates")

    cause_ids: List[str] = []
    root_causes = mapping_list(spec.get("root_causes"))
    if root_causes:
        for index, cause in enumerate(root_causes, start=1):
            cause_id = add_node(
                f"root-cause-{index}",
                "root_cause",
                cause.get("cause"),
                evidence=cause.get("evidence"),
                confidence=cause.get("confidence"),
                evidence_type=cause.get("evidence_type"),
            )
            cause_ids.append(cause_id)
            add_edge(cause_id, tension_id, "explains")
    else:
        for index, issue in enumerate(mapping_list(spec.get("issues")), start=1):
            cause_id = add_node(
                f"root-cause-{index}",
                "root_cause",
                issue.get("title"),
                evidence=issue.get("detail"),
                evidence_type=issue.get("kind"),
            )
            cause_ids.append(cause_id)
            add_edge(cause_id, tension_id, "explains")

    opportunity_ids: Dict[str, str] = {}
    for index, opportunity in enumerate(mapping_list(spec.get("opportunities")), start=1):
        source_id = str(opportunity.get("id") or f"opportunity-{index}")
        opportunity_id = add_node(
            source_id,
            "opportunity",
            opportunity.get("opportunity"),
            affected_people=opportunity.get("affected_people"),
            importance=opportunity.get("importance"),
        )
        opportunity_ids[source_id] = opportunity_id
        add_edge(tension_id, opportunity_id, "reveals")

    candidate_ids: Dict[str, str] = {}
    candidates = mapping_list(spec.get("direction_candidates"))
    for index, candidate in enumerate(candidates, start=1):
        source_id = str(candidate.get("id") or f"direction-{index}")
        candidate_id = add_node(
            source_id,
            "direction_candidate",
            candidate.get("direction"),
            solves=string_list(candidate.get("solves")),
            does_not_solve=string_list(candidate.get("does_not_solve")),
            risks=string_list(candidate.get("risks")),
            assumptions=string_list(candidate.get("assumptions")),
            leverage=string_list(candidate.get("leverage")),
            minimum_experiment=candidate.get("minimum_experiment"),
        )
        candidate_ids[source_id] = candidate_id
        for opportunity_source_id in string_list(candidate.get("opportunity_ids")):
            opportunity_id = opportunity_ids.get(opportunity_source_id)
            if opportunity_id:
                add_edge(candidate_id, opportunity_id, "addresses")

    selected = spec.get("selected_direction") if isinstance(spec.get("selected_direction"), dict) else {}
    selected_source_id = str(selected.get("id") or "")
    selected_candidate = next(
        (candidate for candidate in candidates if str(candidate.get("id")) == selected_source_id),
        candidates[0] if candidates else {},
    )
    legacy_direction = spec.get("direction") if isinstance(spec.get("direction"), dict) else {}
    selected_label = selected_candidate.get("direction") or legacy_direction.get("headline")
    selected_id = ""
    if selected_label:
        selected_id = add_node(
            "selected-direction",
            "selected_direction",
            selected_label,
            rationale=selected.get("rationale") or legacy_direction.get("summary"),
        )
        source_candidate_id = candidate_ids.get(selected_source_id)
        if not source_candidate_id and selected_candidate:
            source_candidate_id = candidate_ids.get(str(selected_candidate.get("id")))
        if source_candidate_id:
            add_edge(source_candidate_id, selected_id, "selected_as")

    experiments = mapping_list(spec.get("next_experiments"))
    if experiments:
        for index, experiment in enumerate(experiments, start=1):
            experiment_id = add_node(
                f"experiment-{index}",
                "experiment",
                experiment.get("smallest_action"),
                hypothesis=experiment.get("hypothesis"),
                success_signal=experiment.get("success_signal"),
            )
            if selected_id:
                add_edge(experiment_id, selected_id, "tests")
    else:
        for index, action in enumerate(mapping_list(spec.get("next_actions")), start=1):
            experiment_id = add_node(
                f"experiment-{index}",
                "experiment",
                action.get("action"),
                timing=action.get("timing"),
                success_signal=action.get("success"),
            )
            if selected_id:
                add_edge(experiment_id, selected_id, "tests")

    unresolved = mapping_list(spec.get("unresolved_branches"))
    if unresolved:
        for index, branch in enumerate(unresolved, start=1):
            branch_id = add_node(
                str(branch.get("branch_id") or f"unresolved-{index}"),
                "unresolved_branch",
                branch.get("reason"),
                revisit_trigger=branch.get("revisit_trigger"),
            )
            if selected_id:
                relation = str(branch.get("relation") or "informs")
                if relation not in {"blocks", "required_before", "informs"}:
                    relation = "informs"
                add_edge(branch_id, selected_id, relation)
    else:
        for index, question in enumerate(string_list(spec.get("open_questions")), start=1):
            branch_id = add_node(f"unresolved-{index}", "unresolved_branch", question)
            if selected_id:
                add_edge(branch_id, selected_id, "informs")

    return {
        "version": "1.0",
        "focusing_question": str(spec.get("key_question") or tension_label),
        "nodes": nodes,
        "edges": edges,
    }


def normalize_render_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """v2の意味構造から、既存SVG描画用フィールドを不足分だけ補う。"""
    normalized = json.loads(json.dumps(spec, ensure_ascii=False))
    desired_change = normalized.get("desired_change") if isinstance(normalized.get("desired_change"), dict) else {}
    core_tension = normalized.get("core_tension") if isinstance(normalized.get("core_tension"), dict) else {}
    root_causes = mapping_list(normalized.get("root_causes"))
    candidates = mapping_list(normalized.get("direction_candidates"))
    selected = normalized.get("selected_direction") if isinstance(normalized.get("selected_direction"), dict) else {}
    selected_id = str(selected.get("id") or "")
    selected_candidate = next(
        (candidate for candidate in candidates if str(candidate.get("id")) == selected_id),
        candidates[0] if candidates else {},
    )

    headline = selected_candidate.get("direction") or "検証する方向性"
    normalized.setdefault("title", headline)
    normalized.setdefault("subtitle", desired_change.get("to") or "対話から整理した方向性と次の検証")
    normalized.setdefault("status", "提案")
    normalized.setdefault("problem", desired_change.get("from") or core_tension.get("statement") or "中心課題を確認中")
    normalized.setdefault("key_question", core_tension.get("statement") or normalized.get("problem"))

    if not isinstance(normalized.get("issues"), list):
        kind_by_type = {
            "observed": "事実",
            "reported": "認識",
            "forecast": "予測",
            "assumption": "仮説",
            "unknown": "未確認",
        }
        normalized["issues"] = [
            {
                "title": cause.get("cause") or "原因仮説",
                "detail": cause.get("evidence") or "根拠を要確認",
                "kind": kind_by_type.get(str(cause.get("evidence_type")), "仮説"),
                "evidence_type": cause.get("evidence_type") or "assumption",
            }
            for cause in root_causes[:4]
        ]
    else:
        kind_by_type = {
            "observed": "事実",
            "reported": "認識",
            "forecast": "予測",
            "assumption": "仮説",
            "unknown": "未確認",
        }
        for issue in normalized["issues"]:
            if isinstance(issue, dict) and issue.get("evidence_type") in kind_by_type:
                issue["kind"] = kind_by_type[str(issue["evidence_type"])]

    if not isinstance(normalized.get("direction"), dict):
        principles = string_list(selected_candidate.get("leverage")) + string_list(selected_candidate.get("assumptions"))
        normalized["direction"] = {
            "headline": headline,
            "summary": selected.get("rationale") or "最小実験で成立条件を確かめながら進める。",
            "principles": principles[:3],
        }

    if not isinstance(normalized.get("decisions"), dict):
        normalized["decisions"] = {
            "continue": string_list(selected_candidate.get("leverage"))[:3],
            "change": string_list(selected_candidate.get("solves"))[:3] or [headline],
            "stop": string_list(selected_candidate.get("does_not_solve"))[:3],
        }

    if not isinstance(normalized.get("next_actions"), list):
        normalized["next_actions"] = [
            {
                "action": experiment.get("smallest_action") or "検証行動を定める",
                "timing": "次の検証",
                "success": experiment.get("success_signal") or "判定条件を定める",
            }
            for experiment in mapping_list(normalized.get("next_experiments"))[:4]
        ]

    if not isinstance(normalized.get("risks"), list):
        normalized["risks"] = [
            {"risk": risk, "response": "最小実験で早期に検証する"}
            for risk in string_list(selected_candidate.get("risks"))[:3]
        ]

    if not isinstance(normalized.get("open_questions"), list):
        normalized["open_questions"] = [
            str(branch.get("reason") or branch.get("branch_id") or "未解決事項")
            for branch in mapping_list(normalized.get("unresolved_branches"))[:3]
        ]

    if not isinstance(normalized.get("evidence"), list):
        normalized["evidence"] = [
            str(cause.get("evidence")) for cause in root_causes[:4] if cause.get("evidence")
        ]
    return normalized


def draw(spec: Dict[str, Any]) -> str:
    """Direction SpecをSVG文字列へ変換する。"""
    spec = normalize_render_spec(spec)
    direction = require_mapping(spec.get("direction"), "direction")
    decisions = require_mapping(spec.get("decisions"), "decisions")
    svg = Svg()

    # ヘッダー
    svg.text(54, 58, "DIRECTION ONE-PAGER", size=15, color="#38BDF8", weight=800)
    svg.block(54, 102, spec.get("title"), 54, 2, size=36, color="#F8FAFC", weight=800, line_height=44)
    svg.block(54, 158, spec.get("subtitle"), 85, 2, size=18, color="#94A3B8", line_height=25)
    status = str(spec.get("status") or "提案")
    status_color = {"確定": "#16A34A", "仮決定": "#D97706", "提案": "#2563EB"}.get(status, "#2563EB")
    svg.pill(1450, 45, status, status_color)
    svg.line(54, 200, 1546, 200, "#26334A")

    # 左列: 課題
    x1, y0, w1 = 54, 230, 430
    svg.rect(x1, y0, w1, 522, "#0D1829")
    section_title(svg, x1 + 22, y0 + 48, "01", "課題の構造")
    svg.text(x1 + 22, y0 + 87, "中心課題", size=15, color="#94A3B8", weight=700)
    next_y = svg.block(x1 + 22, y0 + 118, spec.get("problem"), 34, 4, size=22, color="#F8FAFC", weight=700, line_height=31)
    next_y += 14
    for issue in list(spec.get("issues") or [])[:4]:
        if not isinstance(issue, dict):
            continue
        kind = str(issue.get("kind") or "仮説")
        kind_color = {"事実": "#15803D", "認識": "#0369A1", "予測": "#9A3412", "仮説": "#B45309", "未確認": "#7C3AED"}.get(kind, "#475569")
        pill_width = svg.pill(x1 + 22, next_y - 19, kind, kind_color)
        svg.block(x1 + 34 + pill_width, next_y + 2, issue.get("title"), 22, 1, size=17, color="#E2E8F0", weight=700, line_height=22)
        next_y = svg.block(x1 + 22, next_y + 33, issue.get("detail"), 38, 2, size=15, color="#94A3B8", line_height=21) + 8

    svg.rect(x1, 770, w1, 166, "#101D32", stroke="#334155")
    svg.text(x1 + 22, 804, "KEY QUESTION", size=13, color="#F59E0B", weight=800)
    svg.block(x1 + 22, 842, spec.get("key_question"), 38, 3, size=21, color="#F8FAFC", weight=700, line_height=29)

    # 中央列: 方向性
    x2, w2 = 508, 586
    svg.rect(x2, y0, w2, 390, "#0B2430", stroke="#0E7490")
    section_title(svg, x2 + 24, y0 + 48, "02", "推奨する方向性", "#22D3EE")
    svg.block(x2 + 24, y0 + 102, direction.get("headline"), 43, 2, size=29, color="#ECFEFF", weight=800, line_height=38)
    svg.block(x2 + 24, y0 + 200, direction.get("summary"), 48, 3, size=18, color="#BAE6FD", line_height=26)
    principles = list(direction.get("principles") or [])[:3]
    py = y0 + 296
    for index, principle in enumerate(principles, start=1):
        svg.pill(x2 + 24, py - 21, f"P{index}", "#0E7490")
        svg.block(x2 + 82, py, principle, 40, 1, size=16, color="#E0F2FE", weight=700, line_height=20)
        py += 38

    svg.rect(x2, 644, w2, 292, "#0D1829")
    section_title(svg, x2 + 24, 692, "03", "継続・変更・停止")
    columns: Sequence[Tuple[str, str, str]] = (
        ("継続", "continue", "#16A34A"),
        ("変更", "change", "#D97706"),
        ("停止・後回し", "stop", "#DC2626"),
    )
    col_w = 174
    for index, (label, key, color) in enumerate(columns):
        cx = x2 + 24 + index * 184
        svg.pill(cx, 718, label, color)
        list_items(svg, decisions.get(key, []), cx, 779, 14, 3, color="#CBD5E1", lines_each=2, gap=8)

    # 右列: 実行
    x3, w3 = 1118, 428
    svg.rect(x3, y0, w3, 430, "#0D1829")
    section_title(svg, x3 + 22, y0 + 48, "04", "次のアクション", "#A3E635")
    ay = y0 + 92
    for index, action in enumerate(list(spec.get("next_actions") or [])[:4], start=1):
        if not isinstance(action, dict):
            continue
        svg.pill(x3 + 22, ay - 23, str(index), "#4D7C0F", min_width=36)
        svg.block(x3 + 70, ay, action.get("action"), 30, 1, size=18, color="#F7FEE7", weight=700, line_height=24)
        meta = f"{action.get('timing', '時期未定')}｜完了条件: {action.get('success', '要定義')}"
        ay = svg.block(x3 + 70, ay + 31, meta, 31, 2, size=14, color="#A3B18A", line_height=20) + 12

    svg.rect(x3, 684, w3, 252, "#0D1829")
    svg.text(x3 + 22, 721, "リスクと未解決", size=21, color="#F8FAFC", weight=700)
    ry = 755
    for risk in list(spec.get("risks") or [])[:2]:
        if not isinstance(risk, dict):
            continue
        svg.text(x3 + 22, ry, "△", size=18, color="#FB7185", weight=800)
        ry = svg.block(x3 + 48, ry, f"{risk.get('risk')} → {risk.get('response')}", 34, 2, size=15, color="#FECACA", line_height=21) + 8
    open_questions = list(spec.get("open_questions") or [])[:3]
    if open_questions:
        svg.text(x3 + 22, ry + 8, "OPEN", size=12, color="#A78BFA", weight=800)
        list_items(svg, open_questions, x3 + 22, ry + 36, 34, 3, color="#C4B5FD", lines_each=1, gap=5)

    # フッター
    evidence = "  /  ".join(str(item) for item in list(spec.get("evidence") or [])[:4]) or "根拠未記載"
    svg.text(54, 975, "EVIDENCE", size=12, color="#64748B", weight=800)
    svg.block(142, 975, evidence, 125, 1, size=13, color="#64748B", line_height=18)
    return svg.render()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Direction Spec JSONから1ページSVGを生成します。")
    parser.add_argument("input", type=Path, help="入力するDirection Spec JSON")
    parser.add_argument("output", type=Path, help="出力するSVG")
    parser.add_argument("--graph-output", type=Path, help="Direction Graph JSONの出力先")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.input.open("r", encoding="utf-8-sig") as handle:
        spec = json.load(handle)
    if not isinstance(spec, dict):
        raise ValueError("Direction Specのルートはオブジェクトで指定してください。")
    graph = build_direction_graph(spec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(draw(spec), encoding="utf-8")
    if args.graph_output:
        args.graph_output.parent.mkdir(parents=True, exist_ok=True)
        args.graph_output.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Direction Graphを生成しました: {args.graph_output.resolve()}")
    print(f"SVGを生成しました: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
