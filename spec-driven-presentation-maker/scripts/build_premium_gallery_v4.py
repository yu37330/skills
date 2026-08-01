#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sdpm_native_components import build_component
from sdpm_native_components.theme import load_theme

THEMES=[
    ("executive","Consulting Classic"),
    ("editorial","Editorial Premium"),
    ("technical","Technical / Data"),
]
COMPONENTS=[
    ("narrative.executive_summary", "Executive Summary", {"headline":"市場選択・価値提案・実行基盤の3点を同時に変える", "items":[{"title":"市場を選ぶ","body":"高成長・高収益の法人顧客に集中"},{"title":"価値提案を変える","body":"製品販売から業務成果の提供へ"},{"title":"実行基盤を整える","body":"営業・CS・データを横断運用"},{"title":"90日で検証する","body":"離反率、利用定着、粗利で継続判断"}]}),
    ("narrative.key_message_evidence", "Key Message + Evidence", {"message":"市場成長は続くが、シェア回復には重点顧客への集中が必要", "evidence":[{"value":"+8%","label":"市場成長","note":"年平均成長率"},{"value":"-3.6pt","label":"自社シェア","note":"3年間の低下幅"},{"value":"34%","label":"市場A粗利率","note":"全市場で最高"}], "implication":"市場Aへ営業・開発・CS資源を集中する"}),
    ("chart.insight", "Chart + Insight", {"items":[{"label":"市場A","value":"82","highlight":True},{"label":"市場B","value":"63"},{"label":"市場C","value":"41"},{"label":"市場D","value":"27"}], "insight":"市場Aは魅力度と収益性の両面で最優先", "support":"資源配分を市場Aへ寄せる"}),
    ("narrative.findings_implications", "Findings + Implications", {"items":[{"finding":"離反の62%が導入90日以内に発生","implication":"オンボーディングを最優先で改善"},{"finding":"高収益顧客ほど利用部門が限定","implication":"部門展開を契約・支援に組み込む"},{"finding":"価格不満より効果不明が多い","implication":"成果KPIを顧客と共同定義"}]}),
    ("strategy.house", "Strategy House", {"aspiration":"市場Aで顧客成果を最も再現できるパートナーへ","choices":[{"title":"Where to play","body":"市場Aの中堅・大企業"},{"title":"How to win","body":"成果連動型の価値提案"},{"title":"Right to win","body":"現場知見×利用データ"}],"initiatives":["オンボーディング再設計","価格・契約変更","部門展開モデル"],"enablers":["CX人材","顧客データ","ガバナンス"],"foundation":"顧客中心文化・収益管理"}),
    ("strategy.issue_tree", "Issue Tree", {"root":"利益成長をどう実現するか","branches":[{"title":"売上","children":["顧客数","単価"]},{"title":"粗利","children":["商品構成","原価"]},{"title":"販管費","children":["生産性","固定費"]}]}),
    ("strategy.portfolio_matrix", "Portfolio Matrix", {"x_label":"実行容易性","y_label":"利益インパクト","quadrant_labels":["低優先","Quick wins","再設計","Strategic bets"],"items":[{"label":"オンボーディング","x":.78,"y":.82,"highlight":True,"size":70},{"label":"価格・契約","x":.55,"y":.76,"size":54},{"label":"顧客データ","x":.42,"y":.68,"size":50},{"label":"新規市場","x":.28,"y":.35,"size":38}]}),
    ("strategy.capability_map", "Capability Map", {"groups":[{"title":"顧客","items":[{"label":"顧客洞察","maturity":"2"},{"label":"成果設計","maturity":"1"},{"label":"CX運用","maturity":"2"}]},{"title":"商業","items":[{"label":"提案営業","maturity":"2"},{"label":"価格設計","maturity":"1"},{"label":"部門展開","maturity":"2"}]},{"title":"基盤","items":[{"label":"利用データ","maturity":"1"},{"label":"人材","maturity":"2"},{"label":"ガバナンス","maturity":"2"}]}]}),
    ("strategy.value_driver_tree", "Value Driver Tree", {"root":"営業利益 +10%","drivers":[{"title":"売上 +8%","subdrivers":["顧客数 +5%","単価 +3%"]},{"title":"粗利率 +2pt","subdrivers":["価格 +1pt","原価 -1pt"]},{"title":"販管費 横ばい","subdrivers":["営業生産性","CS自動化"]}]}),
    ("strategy.initiative_portfolio", "Initiative Portfolio", {"items":[{"title":"オンボーディング再設計","value":"高","effort":"中","owner":"CX責任者","status":"優先","description":"導入90日以内の定着を改善"},{"title":"価格・契約モデル変更","value":"高","effort":"高","owner":"事業責任者","status":"設計中"},{"title":"顧客データ基盤","value":"中","effort":"高","owner":"IT責任者","status":"準備"},{"title":"部門展開プレイブック","value":"中","effort":"中","owner":"営業責任者","status":"候補"}]}),
    ("execution.roadmap", "Roadmap", {"phases":[{"title":"設計","period":"0-30日","items":["顧客課題定義","成果KPI設定"]},{"title":"パイロット","period":"31-90日","items":["重点顧客で実装","効果測定"]},{"title":"標準化","period":"4-6か月","items":["業務標準化","教育・データ整備"]},{"title":"展開","period":"7-12か月","items":["全社展開","収益モデル更新"]}]}),
    ("execution.gantt", "Gantt", {"periods":["Q1","Q2","Q3","Q4"],"tasks":[{"label":"オンボーディング","start":0,"end":2,"milestone":1},{"label":"価格・契約","start":0,"end":3},{"label":"顧客データ","start":1,"end":4},{"label":"全社展開","start":2,"end":4,"milestone":3}]}),
    ("execution.governance", "Governance", {"levels":[{"title":"Steering Committee","detail":"月次・投資判断"},{"title":"Program Office","detail":"週次・横断課題"},{"title":"Workstreams","detail":"日次・実行"}]}),
    ("execution.kpi_cascade", "KPI Cascade", {"top":{"value":"+10%","label":"営業利益"},"levels":[{"items":[{"value":"+8%","label":"売上"},{"value":"+2pt","label":"粗利率"}]},{"items":[{"value":"+5%","label":"顧客数"},{"value":"+3%","label":"単価"},{"value":"-5%","label":"離反率"}]}]}),
    ("narrative.recommendation_actions", "Decision / Recommendation", {"recommendation":"市場Aの重点顧客に集中し、成果連動型の価値提案とオンボーディングを90日で検証する","actions":[{"text":"対象顧客10社と責任者を確定"},{"text":"成果KPI・価格・契約条件を設計"},{"text":"90日後に継続・拡大を判断"}],"decision":"本日の判断：90日パイロットを承認するか"}),
]

def tx(x,y,w,h,text,size,color,bold=False,align="left",font="Yu Gothic UI"):
    return {"type":"textbox","x":x,"y":y,"width":w,"height":h,"text":text,"fontSize":size,"fontFamily":font,"fontColor":color,"bold":bold,"align":align,"verticalAlign":"middle","marginLeft":0,"marginRight":0,"marginTop":0,"marginBottom":0}

def ln(x1,y1,x2,y2,color,width=1): return {"type":"line","x1":x1,"y1":y1,"x2":x2,"y2":y2,"color":color,"lineWidth":width}

slides=[]; n=0
for theme, theme_label in THEMES:
    tok=load_theme(theme)
    bg=tok['colors']['background']; text=tok['colors']['text']; muted=tok['colors']['muted']; accent=tok['colors']['accent']; primary=tok['colors']['primary']; font=tok['fonts']['ja']
    for cid,title,content in COMPONENTS:
        n+=1; e=[]
        e.append(tx(100,38,700,26,theme_label.upper(),12,accent,True,font=font))
        e.append(tx(100,78,1720,104,title,34,primary,True,font=font))
        e.append(tx(100,173,1000,22,cid,12,muted,True,font=font))
        e.append(ln(100,207,1820,207,tok['colors']['line'],1))
        r=build_component(cid,{"x":100,"y":240,"width":1720,"height":680},content,theme=theme,variant="primary")
        e.extend(r.elements)
        e.append(tx(100,1018,1300,20,f"{theme_label} — composition, typography and reading path are theme-specific",12,muted,False,font=font))
        e.append(tx(1740,1016,80,22,f"{n} / {len(THEMES)*len(COMPONENTS)}",12,muted,True,"right",font))
        slides.append({"layout":"Title Only","placeholders":{"0":""},"background":bg,"elements":e})

deck={"template":"blank-light.pptx","fonts":{"fullwidth":"Yu Gothic UI","halfwidth":"Aptos"},"defaultTextColor":"#123039","slides":slides}
out_dir=ROOT/'references'/'examples'/'native-components-v4'; out_dir.mkdir(parents=True,exist_ok=True)
out=out_dir/'premium-components-gallery-v4.json'; out.write_text(json.dumps(deck,ensure_ascii=False,indent=2),encoding='utf-8'); print(out)
