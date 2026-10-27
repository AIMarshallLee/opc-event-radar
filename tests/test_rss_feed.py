import unittest
import xml.etree.ElementTree as ET

from src.content.rss import generate_atom_feed, filter_events, DEFAULT_SITE_URL
from src.core.models import Event

ATOM_NS = "http://www.w3.org/2005/Atom"


def make_event(**overrides) -> Event:
    base = dict(
        id="evt-001",
        title="AI Agent 实战沙龙",
        normalized_title="ai agent 实战沙龙",
        start_time="11月8日 14:00",
        city="杭州",
        district="余杭",
        venue="梦想小镇",
        organizer="OPC 社区",
        price=0.0,
        price_text="免费",
        category="AI",
        source_id="src-1",
        source_name="Luma",
        source_url="https://lu.ma/example",
        signup_url="https://lu.ma/example",
        overall_score=88,
        status="upcoming",
        recommendation_reason="硬核实战",
        suitable_for="AI 从业者",
        not_suitable_for="纯小白",
    )
    base.update(overrides)
    return Event(**base)


class TestAtomFeed(unittest.TestCase):

    def setUp(self):
        self.events = [
            make_event(),
            make_event(id="evt-002", title="低分活动", overall_score=60),
            make_event(id="evt-003", title="已结束活动", status="ended"),
            make_event(id="evt-004", title="上海活动", city="上海", category="FDE"),
            make_event(id="evt-005", title="线上活动", city="线上"),
        ]

    # 1. 输出是合法 XML 且根节点为 Atom feed
    def test_valid_atom_xml(self):
        xml = generate_atom_feed(self.events)
        root = ET.fromstring(xml)
        self.assertEqual(root.tag, f"{{{ATOM_NS}}}feed")
        ids = [e.text for e in root.findall(f"{{{ATOM_NS}}}id")]
        self.assertTrue(ids[0].startswith(DEFAULT_SITE_URL))
        self.assertIsNotNone(root.find(f"{{{ATOM_NS}}}link[@rel='self']"))
        self.assertIsNotNone(root.find(f"{{{ATOM_NS}}}updated"))

    # 2. 过滤口径与 iCal 一致：排除已结束与低分
    def test_score_and_status_filtering(self):
        xml = generate_atom_feed(self.events, min_score=75)
        titles = ET.fromstring(xml).findall(f"{{{ATOM_NS}}}entry/{{{ATOM_NS}}}title")
        text = " ".join(t.text or "" for t in titles)
        self.assertIn("AI Agent 实战沙龙", text)
        self.assertNotIn("低分活动", text)
        self.assertNotIn("已结束活动", text)

    # 3. 城市过滤：命中最保留，同时保留线上活动
    def test_city_filter_keeps_online(self):
        kept = filter_events(self.events, city="杭州")
        cities = {e.city for e in kept}
        self.assertIn("杭州", cities)
        self.assertIn("线上", cities)
        self.assertNotIn("上海", cities)

    # 4. 分类过滤
    def test_category_filter(self):
        kept = filter_events(self.events, category="AI")
        self.assertTrue(all(e.category == "AI" for e in kept))

    # 5. 特殊字符不破坏 XML（ElementTree 自动转义）
    def test_special_chars_escaped(self):
        xml = generate_atom_feed(
            [make_event(title='报名<爆款>&"优惠"')],
            min_score=75,
        )
        root = ET.fromstring(xml)  # 不抛异常即转义成功
        titles = [t.text for t in root.findall(f"{{{ATOM_NS}}}entry/{{{ATOM_NS}}}title")]
        self.assertTrue(any('报名<爆款>&"优惠"' in t for t in titles))

    # 6. 时间符合 RFC 3339 +08:00（与 Asia/Shanghai 口径一致）
    def test_rfc3339_timezone(self):
        xml = generate_atom_feed(self.events)
        root = ET.fromstring(xml)
        published = root.find(f"{{{ATOM_NS}}}entry/{{{ATOM_NS}}}published").text
        self.assertRegex(published, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")

    # 7. 摘要包含评分、地点、避坑三要素
    def test_summary_contents(self):
        xml = generate_atom_feed(self.events)
        summary = ET.fromstring(xml).find(f"{{{ATOM_NS}}}entry/{{{ATOM_NS}}}summary").text
        for marker in ("【评分】", "【地点】", "不太适合谁", "报名链接"):
            self.assertIn(marker, summary)


if __name__ == "__main__":
    unittest.main()
