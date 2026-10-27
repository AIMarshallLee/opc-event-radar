"""FETCHER_MAP 覆盖测试：注册表中的源必须有抓取器映射，否则 run_pipeline 静默跳过。

run_pipeline 对无映射的源直接 continue（不计数、不告警），配置错误会无声丢失
整个源。本测试把该静默路径变成显式失败。
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline.engine import FETCHER_MAP  # noqa: E402
from src.sources.registry import get_active_sources  # noqa: E402


class TestFetcherMapCoverage(unittest.TestCase):

    def setUp(self):
        init_ok = True
        try:
            from src.core.database import init_db
            init_db()
        except Exception:
            init_ok = False
        self.init_ok = init_ok

    # 1. 当前数据库的 active 源必须全部有抓取器映射
    def test_active_sources_have_fetchers(self):
        if not self.init_ok:
            self.skipTest("数据库不可用")
        missing = [s.id for s in get_active_sources() if s.id not in FETCHER_MAP]
        self.assertEqual(missing, [], f"以下启用中的源没有抓取器映射，run_pipeline 会静默跳过：{missing}")

    # 2. FETCHER_MAP 的值必须是可实例化类（带 fetch_raw_candidates 方法）
    def test_map_values_are_fetcher_classes(self):
        for sid, cls in FETCHER_MAP.items():
            self.assertTrue(hasattr(cls, "fetch_raw_candidates"), f"{sid} 的 {cls} 不是合法抓取器")

    # 3. 映射键命名约定：小写下划线（与注册表 id 风格一致）
    def test_map_keys_naming(self):
        bad = [k for k in FETCHER_MAP if k != k.lower() or " " in k]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
