"""run_pipeline 记账与降级状态机测试：mock 数据源与抓取器，不发真实网络请求。

覆盖：成功/失败源计数、candidate→new/duplicate/rejected 汇总、
failure_count≥3 自动 degraded、status 状态机（success / partial_failure）。
"""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.database import get_all_events, init_db  # noqa: E402
from src.core.models import Source  # noqa: E402
from src.pipeline.engine import run_pipeline  # noqa: E402


def make_source(sid, name):
    return Source(id=sid, name=name, type="event_platform",
                  url="https://example.com", priority=1)


class GoodFetcher:
    """返回两条合法候选。"""
    def __init__(self, source):
        self.source = source

    def fetch_raw_candidates(self):
        return [
            dict(raw_title=f"杭州 AI 沙龙（{self.source.id}）A", raw_location="余杭区梦想小镇",
                 raw_text="杭州 AI 活动", raw_time="11月8日 14:00", price=0.0, price_text="免费",
                 source_id=self.source.id, source_name=self.source.name,
                 source_url="https://example.com/a", organizer="OPC 社区", description="实战工作坊"),
            dict(raw_title=f"杭州 AI 沙龙（{self.source.id}）B", raw_location="余杭区梦想小镇",
                 raw_text="杭州 AI 活动", raw_time="11月9日 14:00", price=0.0, price_text="免费",
                 source_id=self.source.id, source_name=self.source.name,
                 source_url="https://example.com/b", organizer="OPC 社区", description="实战工作坊"),
        ]


class BadFetcher:
    def __init__(self, source):
        self.source = source

    def fetch_raw_candidates(self):
        raise RuntimeError("源挂了")


def setup_sources(sources):
    """patch 源注册表与抓取器映射，隔离真实网络与真实源列表。"""
    import src.pipeline.engine as engine
    return [
        patch.object(engine, "get_active_sources", lambda: sources),
        patch.object(engine, "initialize_source_registry", lambda: None),
        patch.dict(engine.FETCHER_MAP, {s.id: (GoodFetcher if s.id.startswith("good") else BadFetcher)
                                       for s in sources}),
    ]


class TestRunPipelineBookkeeping(unittest.TestCase):

    def setUp(self):
        # 隔离到临时数据库：不写仓库共享开发库（patch 模块常量，不改生产代码）
        self.tmp = TemporaryDirectory()
        import src.core.database as dbmod
        self.db_patcher = patch.object(dbmod, "DB_PATH", str(Path(self.tmp.name) / "events.db"))
        self.db_patcher.start()
        self.addCleanup(self.db_patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        init_db()

    # 1. 全部成功：success_sources 全记，候选入账，status=success
    def test_all_success(self):
        patches = setup_sources([make_source("good_a", "源A"), make_source("good_b", "源B")])
        with patches[0], patches[1], patches[2]:
            run = run_pipeline()
        self.assertEqual(run.scanned_sources, 2)
        self.assertEqual(run.success_sources, 2)
        self.assertEqual(run.failed_sources, 0)
        self.assertEqual(run.candidate_events, 4)
        self.assertGreaterEqual(run.new_events, 2)  # 至少入库（不同标题）
        self.assertEqual(run.status, "success")
        self.assertIn("入库新活动", run.summary)

    # 2. 部分失败：failed 记账 + status=partial_failure，成功源照常入库
    def test_partial_failure(self):
        patches = setup_sources([make_source("good_a", "源A"), make_source("bad_x", "坏源")])
        with patches[0], patches[1], patches[2]:
            run = run_pipeline()
        self.assertEqual(run.success_sources, 1)
        self.assertEqual(run.failed_sources, 1)
        self.assertEqual(run.status, "partial_failure")
        self.assertGreaterEqual(run.new_events, 2)

    # 3. 连续失败 3 次后源降级为 degraded（failure_count 累计语义）
    def test_source_degrades_after_three_failures(self):
        patches = setup_sources([make_source("bad_x", "坏源")])
        with patches[0], patches[1], patches[2]:
            run_pipeline()
            run_pipeline()
            run_pipeline()
        # 第三次运行后该源应已 degraded
        from src.core.database import get_all_sources
        src = next(s for s in get_all_sources() if s.id == "bad_x")
        self.assertGreaterEqual(src.failure_count, 3)
        self.assertEqual(src.status, "degraded")

    # 4. 跨批次重复标题按查重入账（第二次跑同内容 → duplicate）
    def test_cross_batch_dedup(self):
        patches = setup_sources([make_source("good_a", "源A")])
        with patches[0], patches[1], patches[2]:
            first = run_pipeline()
            new_before = first.new_events
            second = run_pipeline()
        self.assertEqual(second.duplicate_events, new_before)  # 同内容全部判重


if __name__ == "__main__":
    unittest.main()
