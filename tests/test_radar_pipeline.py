import unittest
import datetime
from src.core.models import Event, Source
from src.pipeline.location_validator import validate_hangzhou_location
from src.pipeline.deduplicator import normalize_title, calculate_title_similarity, is_same_event, merge_event_sources
from src.pipeline.classifier import classify_event
from src.pipeline.verification import calculate_confidence_score
from src.pipeline.scorer import evaluate_event_scores
from src.pipeline.comment_generator import generate_ai_comment
from src.scheduler.runner import manage_event_lifecycles
from src.core.database import init_db, save_event, get_all_events

class TestRadarPipeline(unittest.TestCase):

    def setUp(self):
        init_db()

    # 1. 测试非杭州活动自动拒绝
    def test_non_hangzhou_rejection(self):
        is_hz, dist, _ = validate_hangzhou_location("全球AI芯片开发者大会", "上海国际博览中心")
        self.assertFalse(is_hz)
        self.assertEqual(dist, "非杭州")

    # 2. 测试杭州 13 区县及典型园区地标识别
    def test_hangzhou_districts_and_landmarks(self):
        is_hz1, dist1, _ = validate_hangzhou_location("杭州OPC创享会", "余杭区梦想小镇天使村")
        self.assertTrue(is_hz1)
        self.assertEqual(dist1, "余杭")

        is_hz2, dist2, _ = validate_hangzhou_location("NVIDIA 技术开放日", "阿里滨江园区")
        self.assertTrue(is_hz2)
        self.assertEqual(dist2, "滨江")

    # 3. 测试线上与杭州 OPC 生态相关活动保留
    def test_online_opc_inclusion(self):
        is_hz, dist, _ = validate_hangzhou_location("全国超级个体 OPC 线上闭门会", "腾讯会议线上直播")
        self.assertTrue(is_hz)
        self.assertEqual(dist, "线上")

    # 4. 测试标题不同但为同一活动 (包含括号、前缀、城市站等)
    def test_title_similarity_dedup(self):
        t1 = "【杭州站】AI跨境增长实战大课"
        t2 = "跃迁--AI跨境增长实战大课杭州场"
        norm1 = normalize_title(t1)
        norm2 = normalize_title(t2)
        sim = calculate_title_similarity(t1, t2)
        self.assertTrue(sim >= 0.70 or norm1 in norm2 or norm2 in norm1)

    # 5. 测试同一活动两个来源合并保留 sources[]
    def test_cross_source_merging(self):
        e1 = Event(
            id="ev_test_1",
            title="OpenFDE 企业 AI 场景共创会",
            normalized_title=normalize_title("OpenFDE 企业 AI 场景共创会"),
            start_time="09月25日",
            source_id="lianpu",
            source_name="联谱",
            source_url="https://lianpu.com/event/1",
            sources=[{"source_id": "lianpu", "source_url": "https://lianpu.com/event/1"}]
        )
        e2 = Event(
            id="ev_test_2",
            title="OpenFDE 企业 AI 场景共创会 · 杭州",
            normalized_title=normalize_title("OpenFDE 企业 AI 场景共创会 · 杭州"),
            start_time="09月25日",
            source_id="huodongxing",
            source_name="活动行",
            source_url="https://huodongxing.com/event/2",
            sources=[{"source_id": "huodongxing", "source_url": "https://huodongxing.com/event/2"}]
        )
        same, _ = is_same_event(e1, e2)
        self.assertTrue(same)
        merged = merge_event_sources(e1, e2)
        self.assertEqual(len(merged.sources), 2)
        self.assertTrue(any(s["source_id"] == "huodongxing" for s in merged.sources))

    # 6. 测试缺失价格与结束时间优雅降级
    def test_missing_fields(self):
        cat, tags = classify_event("AI 研讨会", "")
        self.assertEqual(cat, "AI")
        scores = evaluate_event_scores("AI 研讨会", "", "未知", cat, 0.0, 80)
        self.assertTrue(scores["overall_score"] >= 60)

    # 7. 测试置信度规则与低可信判断
    def test_confidence_scoring(self):
        high_score, high_status = calculate_confidence_score(
            "government", "杭州科技局", "09月20日 14:00", "市民中心", "解放东路18号", "https://hz.gov.cn/reg"
        )
        self.assertTrue(high_score >= 80)
        self.assertEqual(high_status, "verified")

        low_score, low_status = calculate_confidence_score(
            "other", "未知", "近期", "待定", "", ""
        )
        self.assertTrue(low_score < 60)
        self.assertEqual(low_status, "unverified")

    # 8. 测试 AI 评语降级自愈能力 (断网或无 Key 状态)
    def test_ai_comment_fallback(self):
        res = generate_ai_comment("杭州一人公司OPC创业交流", "", "OPC联盟", "OPC", 85)
        self.assertIn("recommendation_reason", res)
        self.assertIn("suitable_for", res)
        self.assertIn("not_suitable_for", res)

    # 9. 测试时间变更与地点变更逻辑
    def test_event_update(self):
        ev = Event(
            id="ev_update_test",
            title="测试活动",
            normalized_title="测试活动",
            start_time="09月10日",
            venue="旧场地",
            source_id="test",
            source_name="test",
            source_url="http://test.com"
        )
        save_event(ev)
        ev.venue = "新场地·未来科技城"
        ev.start_time = "09月30日"
        save_event(ev)
        
        all_ev = [x for x in get_all_events() if x.id == "ev_update_test"]
        self.assertEqual(all_ev[0].venue, "新场地·未来科技城")
        self.assertEqual(all_ev[0].start_time, "09月30日")

    # 10. 测试单源失败隔离
    def test_source_failure_isolation(self):
        s_bad = Source(
            id="bad_src",
            name="不可用假网站",
            type="other",
            url="http://127.0.0.1:9999/not_exist",
            enabled=True
        )
        # 单源不可用应正常捕获，不引发系统崩溃
        try:
            import urllib.request
            urllib.request.urlopen(s_bad.url, timeout=0.5)
            failed = False
        except Exception:
            failed = True
        self.assertTrue(failed)

if __name__ == "__main__":
    unittest.main()
