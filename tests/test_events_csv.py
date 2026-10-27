import csv
import io
import unittest

from src.content.csv_export import generate_events_csv
from src.core.models import Event


def make_event(**overrides) -> Event:
    base = dict(
        id="evt-001", title="AI Agent 实战沙龙", normalized_title="ai agent 实战沙龙",
        start_time="11月8日 14:00", city="杭州", district="余杭", venue="梦想小镇",
        organizer="OPC 社区", price=0.0, price_text="免费", category="AI",
        source_id="src-1", source_name="Luma", source_url="https://lu.ma/example",
        signup_url="https://lu.ma/example", overall_score=88, status="upcoming",
        recommendation_reason="硬核实战",
    )
    base.update(overrides)
    return Event(**base)


class TestEventsCsv(unittest.TestCase):

    def setUp(self):
        self.events = [
            make_event(),
            make_event(id="evt-002", title="低分活动", overall_score=60),
            make_event(id="evt-003", title="已结束活动", status="ended"),
            make_event(id="evt-004", title="上海活动", city="上海", category="FDE", price=99.0, price_text="¥99"),
        ]

    # 1. 表头 + BOM + 过滤口径与 iCal/Atom 一致
    def test_header_bom_and_filtering(self):
        out = generate_events_csv(self.events)
        self.assertTrue(out.startswith("\ufeff"))
        rows = list(csv.DictReader(io.StringIO(out.lstrip("\ufeff"))))
        self.assertEqual(len(rows), 2)  # 低分与已结束被过滤
        titles = {r["title"] for r in rows}
        self.assertIn("AI Agent 实战沙龙", titles)
        self.assertIn("上海活动", titles)
        self.assertNotIn("低分活动", titles)
        self.assertNotIn("已结束活动", titles)

    # 2. 城市与分类过滤
    def test_city_category_filters(self):
        hz = list(csv.DictReader(io.StringIO(generate_events_csv(self.events, city="杭州").lstrip("\ufeff"))))
        self.assertEqual({r["city"] for r in hz}, {"杭州"})
        fde = list(csv.DictReader(io.StringIO(generate_events_csv(self.events, category="FDE").lstrip("\ufeff"))))
        self.assertEqual({r["category"] for r in fde}, {"FDE"})

    # 3. 免费票价与付费票价取值正确
    def test_price_field(self):
        rows = {r["id"]: r for r in csv.DictReader(io.StringIO(generate_events_csv(self.events).lstrip("\ufeff")))}
        self.assertEqual(rows["evt-001"]["price_text"], "免费")
        self.assertEqual(rows["evt-004"]["price_text"], "¥99")

    # 4. CSV 注入防护：以 = + - @ 开头的单元格加前导单引号
    def test_csv_injection_guard(self):
        out = generate_events_csv([make_event(title="=HYPERLINK(\"http://evil\")", overall_score=90)])
        self.assertIn("'=HYPERLINK", out)
        self.assertNotIn("\n=HYPERLINK", out)

    # 5. 中文经 BOM 编码可被 utf-8-sig 正确读回
    def test_roundtrip_with_bom(self):
        out = generate_events_csv(self.events)
        rows = list(csv.DictReader(io.StringIO(out.encode("utf-8").decode("utf-8-sig"))))
        self.assertEqual({r["city"] for r in rows}, {"杭州", "上海"})
        self.assertTrue(any(r["title"] == "AI Agent 实战沙龙" for r in rows))


if __name__ == "__main__":
    unittest.main()
