from __future__ import annotations
import unittest
from sdpm_native_components import build_component

class TextStressTest(unittest.TestCase):
    def test_long_japanese_headline(self):
        result=build_component('headline.insight',{'x':100,'y':100,'width':900,'height':180},{'text':'生成AIの導入量を競うのではなく、顧客価値を生む業務プロセスと成果指標を一体で設計することが次の競争力になる'},theme='executive',variant='dense')
        self.assertTrue(result.elements)
        fonts=[e.get('fontSize') for e in result.elements if e.get('componentRole')=='headline']
        self.assertTrue(fonts and all(f>=20 for f in fonts))
    def test_narrow_metric_does_not_use_extreme_font(self):
        result=build_component('metric.big_number',{'x':100,'y':100,'width':250,'height':260},{'value':'98.7%','label':'大企業のDX取組率'},theme='executive',variant='dense')
        values=[e for e in result.elements if e.get('componentRole')=='value']
        self.assertEqual(len(values),1)
        self.assertLessEqual(values[0]['fontSize'],48)
        self.assertGreaterEqual(values[0]['fontSize'],30)
    def test_summary_strip_long_pair(self):
        result=build_component('insight.summary_strip',{'x':100,'y':100,'width':1600,'height':320},{'items':[{'value':'98.7% vs 41.6%','text':'従業員規模別のDX取組率の差'},{'value':'44.0%','text':'生成AI導入率'},{'value':'23.9%','text':'成果指標設定'}]},theme='executive',variant='primary')
        self.assertTrue(result.elements)

if __name__=='__main__': unittest.main()
