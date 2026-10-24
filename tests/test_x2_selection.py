"""纯选择器的词面、Unicode 和来源边界。"""
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from test_x2_runtime import request
from x2_selection import validate_query, select_recall, _select_highlights, RecallQueryError
from life_engine.domain import SourceType


class SelectionTests(unittest.TestCase):
    def record(self, bullet):
        return SimpleNamespace(content='[角色扮演回忆]\n期间记得的事：\n- '+bullet+'\n这是一次角色扮演经历，不是真实发生过的事实。',
            subjects=(), created_at=datetime.now(timezone.utc), memory_id=request()['request'])

    def test_lexical_and_no_semantic_claim(self):
        r = self.record('蓝灯书店找到地图')
        for query in ('蓝灯书店', '「书店」', ''):
            self.assertEqual(select_recall([r], validate_query(query, 6, 6), 6), [r])
        self.assertEqual(select_recall([r], validate_query('购买咖啡', 6, 6), 6), [])
        self.assertEqual(select_recall([r], '蓝灯书店', 0), [])

    def test_query_limits_and_normalization(self):
        self.assertEqual(validate_query('ＡＢＣ', 6, 6), 'abc')
        for query in ('字'*1366, '\ud800', 123):
            with self.assertRaises(RecallQueryError):
                validate_query(query, 0, 6)
        for limit in (-1, 7, True):
            with self.assertRaises(RecallQueryError):
                validate_query('', limit, 6)

    def test_highlights_bounded_stable_anchor(self):
        records = [SimpleNamespace(content='字'*100+str(i), provenance=SimpleNamespace(source_type=
                    SourceType.USER_REPORT if i%2==0 else SourceType.MODEL)) for i in range(8)]
        result = _select_highlights(records)
        self.assertEqual(result, _select_highlights(records))
        self.assertLessEqual(len(result), 6)
        self.assertTrue(all(len(x.encode()) <= 180 for x in result))
