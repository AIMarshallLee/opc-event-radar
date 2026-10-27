"""process_single_candidate 编排测试：清洗→地域校验→查重→分类→评分→入库的核心单步。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.database import init_db, get_all_events  # noqa: E402
from src.core.models import Event  # noqa: E402
from src.pipeline.engine import process_single_candidate  # noqa: E402


def cand(**over):
    base = dict(
        raw_title="杭州 AI Agent 实战沙龙第 1 期",
        raw_location="余杭区梦想小镇",
        raw_text="杭州 AI 沙龙活动介绍",
        raw_time="11月8日 14:00",
        price=0.0, price_text="免费",
        source_id="luma_hangzhou", source_name="Luma",
        source_url="https://lu.ma/example", signup_url="https://lu.ma/example",
        organizer="OPC 社区", description="面向开发者的 Agent 实战工作坊",
    )
    base.update(over)
    return base


class TestProcessSingleCandidate(unittest.TestCase):

    def setUp(self):
        init_db()
        self._count = len(get_all_events())

    # 1. 空标题直接拒绝
    def test_empty_title_rejected(self):
        res = process_single_candidate(cand(raw_title="  "), [])
        self.assertEqual(res, {"status": "rejected", "reason": "empty_title"})

    # 2. 非支持城市被地域校验拒绝
    def test_unsupported_city_rejected(self):
        res = process_single_candidate(cand(raw_title="南京 AI 开发者大会", raw_location="南京国际博览中心",
                                            raw_text="南京 AI 活动"), [])
        self.assertEqual(res["status"], "rejected")
        self.assertEqual(res["reason"], "unsupported_city")

    # 3. 合法候选入库：new + 事件带城市与评分
    def test_valid_candidate_saved(self):
        res = process_single_candidate(cand(), [])
        self.assertEqual(res["status"], "new")
        ev = res["event"]
        self.assertEqual(ev.city, "杭州")
        self.assertGreater(ev.overall_score, 0)
        self.assertTrue(ev.normalized_title)
        self.assertEqual(len(ev.sources), 1)
        # 已真实落库（仓库 DB 为共享开发库，用增量断言）
        before = self._count
        self.assertEqual(len(get_all_events()), before + 1)

    # 4. 完全同标题 → duplicate 且合并来源
    def test_exact_duplicate_merges(self):
        first = process_single_candidate(cand(), [])
        self.assertEqual(first["status"], "new")
        second = process_single_candidate(cand(source_id="wechat_search", source_name="搜狗微信",
                                               source_url="https://weixin.sogou.com/x"),
                                          get_all_events())  # 与 run_pipeline 一致：传库内快照
        self.assertEqual(second["status"], "duplicate")
        merged = second["event"]
        self.assertEqual(len(merged.sources), 2)  # 两个来源合并进同一事件

    # 5. 标题包含关系也判重（norm 互为子串）
    def test_substring_duplicate(self):
        process_single_candidate(cand(), [])
        res = process_single_candidate(cand(raw_title="杭州 AI Agent 实战沙龙第 1 期报名开启"), get_all_events())
        self.assertEqual(res["status"], "duplicate")

    # 6. 已有事件列表参数生效：不查库也能判重（并发场景的一致性口径）
    def test_existing_events_param(self):
        existing = Event(title="杭州 AI Agent 实战沙龙第 1 期", normalized_title="杭州 ai agent 实战沙龙第 1 期",
                         start_time="近期", source_id="s", source_name="x", source_url="https://x")
        res = process_single_candidate(cand(), [existing])
        self.assertEqual(res["status"], "duplicate")


if __name__ == "__main__":
    unittest.main()
