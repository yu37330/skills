from __future__ import annotations

import unittest

from sdpm_native_components import build_component, list_components


SAMPLES = {
    "headline.fact": {"text": "AIは58.0%の企業で導入・試験利用されている"},
    "headline.insight": {"text": "導入量ではなく、変える業務と測る価値が次の論点である"},
    "headline.recommendation": {"text": "成果指標を先に置き、AIテーマを選定する"},
    "headline.decision": {"text": "本日決めること：90日PoCを開始するか"},
    "label.fact_tag": {}, "label.interpretation_tag": {}, "label.proposal_tag": {}, "label.section": {"text": "Executive summary"},
    "metric.big_number": {"value": "58.0%", "label": "AI導入・試験利用"},
    "metric.delta": {"before": "22.6%", "after": "44.0%", "delta": "+21.4pt", "label": "生成AI導入率"},
    "metric.before_after": {"before": {"value": "22.6%", "label": "2024"}, "after": {"value": "44.0%", "label": "2025"}},
    "metric_pair.gap": {"left": {"value": "91.6%", "label": "効率化"}, "right": {"value": "3.9%", "label": "売上・利益"}, "implication": "効果は内向きに偏る"},
    "kpi.row": {"items": [{"value": "98.7%", "label": "大企業"}, {"value": "41.6%", "label": "中小企業"}, {"value": "23.9%", "label": "成果指標"}]},
    "kpi.tiles": {"items": [{"value": "7.0%", "label": "データ整備"}, {"value": "50.1%", "label": "人材不足"}, {"value": "39.7%", "label": "ルール"}]},
    "evidence_footer.full": {"claim_type": "事実", "source": "IPA『DX動向2026』", "page": "p.35", "figure": "図表3-14", "sample": "n=853", "response_type": "複数回答"},
    "evidence_footer.compact": {"text": "出典：IPA『DX動向2026』p.35"},
    "annotation.so_what": {"text": "AI導入だけでは、企業価値への接続は保証されない。"},
    "annotation.caveat": {"text": "年度ごとに回答企業が異なり、同一企業の追跡比較ではない。"},
    "annotation.chart_callout": {"label": "2025年度に急増", "anchor": {"x": 700, "y": 500}},
    "comparison.gap": {"left": "個人利用・試験利用が中心", "right": "業務プロセスへの組込みは11.9%", "separator": "差"},
    "comparison.before_after": {"left": "ツール単位の導入", "right": "業務と成果指標を一体設計"},
    "comparison.current_future": {"left": "効率化中心", "right": "顧客価値・収益へ接続"},
    "comparison.pro_con": {"left": "短期間で試せる", "right": "局所最適に陥りやすい"},
    "process.stage_flow": {"stages": [{"title": "課題", "body": "経営課題を定義"}, {"title": "仮説", "body": "価値仮説を置く"}, {"title": "検証", "body": "90日で判断"}]},
    "process.gate": {"before": "PoC完了", "question": "価値仮説を検証できたか", "yes": "拡大", "no": "修正・撤退"},
    "timeline.milestone": {"items": [{"date": "0日", "title": "テーマ選定"}, {"date": "30日", "title": "中間評価"}, {"date": "90日", "title": "継続判断"}]},
    "synthesis.causal_spine": {"cause": "成果指標がない", "phenomenon": "効率化に偏る", "interpretation": "価値接続が弱い", "action": "業務とKPIを同時設計"},
    "decision.choice": {"question": "90日PoCを開始するか", "options": [{"label": "GO", "description": "開始する"}, {"label": "HOLD", "description": "条件を整える"}], "selected": "GO"},
    "decision.criteria": {"rows": [["価値", "成果指標が明確", "○"], ["実行性", "責任者とデータがある", "△"]]},
    "matrix.quadrant": {"items": [{"label": "候補A", "x": 0.3, "y": 0.8, "highlight": True}, {"label": "候補B", "x": 0.7, "y": 0.5}]},
    "action.form": {"fields": [{"label": "対象課題", "value": ""}, {"label": "成果指標", "value": ""}, {"label": "必要データ", "value": ""}, {"label": "判断条件", "value": ""}]},
    "action.owner_due": {"owner": "責任者：AI推進部", "due": "期限：8月31日", "status": "準備中"},
    "chart.progress_rows": {"items": [{"label": "業務効率化", "value": "91.6%"}, {"label": "企画品質", "value": "48.9%"}, {"label": "売上・利益", "value": "3.9%", "color_key": "danger"}]},
    "chart.stacked_bar": {"items": [{"label": "全社", "value": "35.6"}, {"label": "一部", "value": "21.0"}, {"label": "部署", "value": "19.1"}, {"label": "未取組", "value": "20.5"}]},
    "chart.slope": {"left_label": "2024", "right_label": "2025", "items": [{"label": "生成AI", "left": "22.6", "right": "44.0"}, {"label": "業務組込み", "left": "8.2", "right": "11.9"}]},
    "chart.waterfall": {"items": [{"label": "現状", "value": "100", "total": True}, {"label": "効率化", "value": "20"}, {"label": "投資", "value": "-8"}, {"label": "将来", "value": "112", "total": True}]},
    "insight.summary_strip": {"items": [{"value": "75.7%", "text": "DX取組率"}, {"value": "44.0%", "text": "生成AI導入率"}, {"value": "91.6%", "text": "効率化効果"}, {"value": "23.9%", "text": "成果指標設定"}]},
    "quote.editorial": {"text": "AI導入の次に検討すべきは、価値を生む業務と成果指標への接続である。", "attribution": "DX動向2026を踏まえた本資料の解釈"},
    "framework.layers": {"items": [{"title": "経営課題", "body": "価値を定義"}, {"title": "業務プロセス", "body": "変える対象"}, {"title": "データ・AI", "body": "実装基盤"}]},
    "framework.hub_spoke": {"center": {"label": "AIテーマ"}, "items": [{"label": "顧客価値"}, {"label": "業務"}, {"label": "KPI"}, {"label": "データ"}]},
}

CONSULTING_SAMPLES = {
    "narrative.key_message_evidence": {"message": "市場成長は続くが、自社シェア回復には重点顧客への集中が必要", "evidence": [{"value": "+8%", "label": "市場成長", "note": "年平均"}, {"value": "-3.6pt", "label": "自社シェア", "note": "3年累計"}, {"value": "34%", "label": "市場A粗利率", "note": "全市場で最高"}], "implication": "市場Aへ資源を集中する"},
    "chart.insight": {"items": [{"label": "市場A", "value": "82", "highlight": True}, {"label": "市場B", "value": "63"}, {"label": "市場C", "value": "41"}, {"label": "市場D", "value": "27"}], "insight": "市場Aは魅力度と収益性の両面で最優先", "support": "資源配分を市場Aへ寄せる"},
    "strategy.portfolio_matrix": {"x_label": "実行容易性", "y_label": "利益インパクト", "quadrant_labels": ["低優先", "Quick wins", "再設計", "Strategic bets"], "items": [{"label": "A", "x": .78, "y": .82, "highlight": True, "size": 58}, {"label": "B", "x": .35, "y": .68}, {"label": "C", "x": .65, "y": .28}]},
    "strategy.initiative_portfolio": {"items": [{"title": "オンボーディング再設計", "value": "高", "effort": "中", "owner": "CX責任者", "status": "優先", "description": "導入90日以内の定着を改善"}, {"title": "価格・契約モデル変更", "value": "高", "effort": "高", "owner": "事業責任者", "status": "設計中"}, {"title": "顧客データ基盤", "value": "中", "effort": "高", "owner": "IT責任者", "status": "準備"}]},

    "narrative.executive_summary": {"items": [{"title": "市場成長は継続", "body": "重点顧客への投資を優先する"}, {"title": "収益性に差", "body": "高収益セグメントへ資源を移す"}, {"title": "実行基盤が不足", "body": "責任者とKPIを明確にする"}]},
    "narrative.findings_implications": {"items": [{"finding": "顧客離反は導入90日以内に集中", "implication": "オンボーディングを最優先で改善"}, {"finding": "高収益顧客の利用頻度が低下", "implication": "利用定着施策を重点化"}]},
    "narrative.scr": {"situation": "市場は成長している", "complication": "自社シェアは低下している", "resolution": "高収益セグメントへ投資を集中する"},
    "narrative.recommendation_actions": {"recommendation": "重点顧客向けの価値提案を再設計する", "actions": [{"text": "顧客課題を再定義"}, {"text": "提供価値と価格を再設計"}, {"text": "90日で検証"}]},
    "strategy.house": {"aspiration": "顧客価値で選ばれる事業へ", "choices": [{"title": "重点市場", "body": "高成長×高収益"}, {"title": "価値提案", "body": "業務成果を保証"}, {"title": "競争優位", "body": "データと現場力"}], "initiatives": ["商品再設計", "営業変革", "データ基盤"], "enablers": ["人材", "ガバナンス"], "foundation": "組織文化・財務基盤"},
    "strategy.issue_tree": {"root": "利益成長をどう実現するか", "branches": [{"title": "売上", "children": ["数量", "単価"]}, {"title": "粗利", "children": ["商品構成", "原価"]}, {"title": "販管費", "children": ["生産性", "固定費"]}]},
    "strategy.prioritization_matrix": {"x_label": "実行容易性", "y_label": "期待効果", "items": [{"label": "A", "x": .78, "y": .82, "highlight": True, "size": 58}, {"label": "B", "x": .35, "y": .68}, {"label": "C", "x": .65, "y": .28}]},
    "strategy.value_driver_tree": {"root": "企業価値", "drivers": [{"title": "売上成長", "subdrivers": ["顧客数", "単価"]}, {"title": "利益率", "subdrivers": ["粗利率", "生産性"]}, {"title": "資本効率", "subdrivers": ["在庫", "設備"]}]},
    "strategy.capability_map": {"groups": [{"title": "顧客", "items": [{"label": "顧客洞察", "maturity": "2"}, {"label": "価値提案", "maturity": "3"}]}, {"title": "実行", "items": [{"label": "営業", "maturity": "2"}, {"label": "オペレーション", "maturity": "1"}]}, {"title": "基盤", "items": [{"label": "データ", "maturity": "1"}, {"label": "人材", "maturity": "2"}]}]},
    "execution.roadmap": {"phases": [{"title": "設計", "period": "0-30日", "items": ["課題定義", "KPI設定"]}, {"title": "実装", "period": "31-60日", "items": ["業務実装", "データ整備"]}, {"title": "検証", "period": "61-90日", "items": ["効果測定", "継続判断"]}]},
    "execution.gantt": {"periods": ["Q1", "Q2", "Q3", "Q4"], "tasks": [{"label": "戦略設計", "start": 0, "end": 1}, {"label": "パイロット", "start": 1, "end": 3, "milestone": 2}, {"label": "展開", "start": 2, "end": 4}]},
    "execution.workstream_plan": {"workstreams": [{"title": "顧客", "owner": "営業部", "items": ["顧客分析", "提案再設計"], "status": "進行中"}, {"title": "業務", "owner": "業務改革部", "items": ["プロセス設計", "KPI運用"], "status": "準備中"}, {"title": "基盤", "owner": "IT部", "items": ["データ整備", "権限設計"], "status": "未着手"}]},
    "execution.governance": {"levels": [{"title": "Steering Committee", "detail": "月次・重要判断"}, {"title": "Program Office", "detail": "週次・横断管理"}, {"title": "Workstreams", "detail": "日次・実行"}]},
    "execution.raci": {"roles": ["経営", "事業", "IT", "現場"], "rows": [{"activity": "戦略承認", "values": ["A", "R", "C", "I"]}, {"activity": "業務設計", "values": ["I", "A", "C", "R"]}, {"activity": "システム実装", "values": ["I", "C", "A", "R"]}]},
    "execution.initiative_card": {"title": "重点顧客オンボーディング再設計", "owner": "OWNER: CX改革責任者", "description": "導入90日以内の離反を抑制するため、利用開始から定着までの体験を再設計する。", "metrics": [{"value": "-20%", "label": "離反率"}, {"value": "+15pt", "label": "利用定着"}]},
    "execution.kpi_cascade": {"top": {"value": "+10%", "label": "営業利益"}, "levels": [{"items": [{"value": "+8%", "label": "売上"}, {"value": "+2pt", "label": "粗利率"}]}, {"items": [{"value": "+5%", "label": "顧客数"}, {"value": "+3%", "label": "単価"}, {"value": "-5%", "label": "原価"}]}]},
    "process.swimlane": {"stages": ["設計", "承認", "実装", "評価"], "lanes": [{"name": "事業", "activities": [{"label": "課題定義", "start": 0, "end": 1}, {"label": "価値評価", "start": 3, "end": 4}]}, {"name": "IT", "activities": [{"label": "実装設計", "start": 0, "end": 2}, {"label": "開発", "start": 2, "end": 3}]}, {"name": "経営", "activities": [{"label": "承認", "start": 1, "end": 2}]}]},
    "process.customer_journey": {"stages": [{"title": "認知", "action": "情報収集", "need": "違いを理解", "pain": "情報が分散", "moment": "比較表"}, {"title": "検討", "action": "候補比較", "need": "効果を確信", "pain": "ROIが不明", "moment": "試算"}, {"title": "導入", "action": "利用開始", "need": "早く定着", "pain": "設定が複雑", "moment": "支援"}]},
    "chart.horizontal_bar": {"items": [{"label": "市場A", "value": "82", "highlight": True}, {"label": "市場B", "value": "63"}, {"label": "市場C", "value": "41"}]},
    "chart.line_forecast": {"actual": [{"label": "2023", "value": "100"}, {"label": "2024", "value": "112"}, {"label": "2025", "value": "128"}], "forecast": [{"label": "2026", "value": "145"}, {"label": "2027", "value": "168"}], "callout": "重点施策で成長率を加速"},
    "chart.heatmap": {"rows": ["市場A", "市場B", "市場C"], "columns": ["成長", "収益", "競争", "実行性"], "values": [[3,3,1,2],[2,3,2,3],[1,2,3,1]]},
    "chart.scatter_bubble": {"x_label": "市場魅力度", "y_label": "自社競争力", "items": [{"label": "A", "x": .8, "y": .75, "size": 70, "highlight": True}, {"label": "B", "x": .45, "y": .62, "size": 50}, {"label": "C", "x": .65, "y": .28, "size": 40}]},
    "chart.bullet": {"items": [{"label": "売上", "actual": "82", "target": "90", "max": 100}, {"label": "粗利率", "actual": "74", "target": "80", "max": 100}, {"label": "NPS", "actual": "61", "target": "70", "max": 100}]},
    "chart.sensitivity_matrix": {"rows": ["価格 -5%", "Base", "価格 +5%"], "columns": ["数量 -10%", "Base", "数量 +10%"], "values": [[-1.8,-1.1,-.4],[-.8,0,.9],[.2,1.2,2.1]]},
}
SAMPLES.update(CONSULTING_SAMPLES)
for legacy_id, target_id in {
    "chart.highlight_bar": "chart.insight",
    "chart.trend_line": "chart.line_forecast",
    "process.stage": "process.stage_flow",
    "synthesis.spine": "synthesis.causal_spine",
    "synthesis.system_map": "framework.hub_spoke",
}.items():
    SAMPLES[legacy_id] = SAMPLES[target_id]


class ComponentSmokeTest(unittest.TestCase):
    def test_all_components_build(self) -> None:
        self.assertEqual(set(SAMPLES), set(list_components()))
        for component_id in list_components():
            with self.subTest(component_id=component_id):
                result = build_component(
                    component_id,
                    {"x": 120, "y": 120, "width": 1200, "height": 360},
                    SAMPLES[component_id],
                    theme="executive",
                    variant="primary",
                )
                self.assertTrue(result.elements)
                self.assertTrue(all(element.get("componentId") == component_id for element in result.elements))
                self.assertTrue(all(element.get("componentRole") for element in result.elements))

    def test_all_declared_variants_and_themes(self) -> None:
        import json
        from pathlib import Path
        registry = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "assets" / "design-system" / "components" / "contracts.json"
            ).read_text(encoding="utf-8-sig")
        )
        themes = ["base", "executive", "editorial", "technical", "data_report"]
        for item in registry["components"]:
            for variant in item["variants"]:
                for theme in themes:
                    with self.subTest(component_id=item["id"], variant=variant, theme=theme):
                        result = build_component(
                            item["id"],
                            {"x": 120, "y": 120, "width": 1200, "height": 360},
                            SAMPLES[item["id"]],
                            theme=theme,
                            variant=variant,
                        )
                        self.assertTrue(result.elements)

    def test_theme_and_variant(self) -> None:
        for theme in ["base", "executive", "editorial", "technical", "data_report"]:
            result = build_component("metric.big_number", {"x": 0, "y": 0, "width": 500, "height": 260}, SAMPLES["metric.big_number"], theme=theme, variant="alternate")
            self.assertTrue(result.elements)


if __name__ == "__main__":
    unittest.main()
