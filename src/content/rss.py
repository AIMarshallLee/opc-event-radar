import datetime
import re
from typing import List, Optional
from xml.etree import ElementTree as ET

from src.content.ical import parse_event_datetimes
from src.core.models import Event

# 站点对外根地址（与 README「全平台日历一键订阅」中的公开域名一致）
DEFAULT_SITE_URL = "https://ai.2199.chat"

CITY_EN_MAP = {
    "杭州": "hangzhou", "上海": "shanghai", "北京": "beijing",
    "深圳": "shenzhen", "广州": "guangzhou", "成都": "chengdu",
    "厦门": "xiamen", "武汉": "wuhan",
}


def _rfc3339(dt: datetime.datetime) -> str:
    """Atom 要求 RFC 3339 时间；活动时间为本地（Asia/Shanghai） naive 时间，统一标注 +08:00。"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def filter_events(events: List[Event], min_score: int = 75, category: Optional[str] = None, city: Optional[str] = None) -> List[Event]:
    """与 generate_ical_feed 同一套过滤口径：排除已结束，按分数/分类/城市过滤。"""
    filtered = [e for e in events if e.status != "ended" and e.overall_score >= min_score]
    if city and city != "all":
        filtered = [e for e in filtered if e.city == city or e.city == "线上"]
    if category and category != "all":
        filtered = [e for e in filtered if e.category == category]
    return filtered


def generate_atom_feed(
    events: List[Event],
    min_score: int = 75,
    category: Optional[str] = None,
    city: Optional[str] = None,
    site_url: str = DEFAULT_SITE_URL,
    self_path: str = "/feed/events.xml",
) -> str:
    """
    生成标准 RFC 4287 Atom 订阅源（application/atom+xml）。
    与 iCal 订阅互补：RSS/Atom 阅读器（Feedly、Inoreader、Folo 等）可直接订阅高分活动流。
    """
    filtered = filter_events(events, min_score=min_score, category=category, city=city)
    # 未开始的排前，同分按评分高在前
    filtered.sort(key=lambda e: (e.status == "ended", -e.overall_score))

    slug = CITY_EN_MAP.get(city, "events") if city and city != "all" else "events"
    feed_id = f"{site_url}/feed/{slug}-events.xml"
    feed_title = (
        f"⚡ {city} AI / OPC 活动雷达" if city and city != "all" else "⚡ 全国 AI / OPC 活动情报雷达"
    )
    feed_subtitle = (
        f"{city}高价值 AI、FDE 与一人公司(OPC)线下组局精选"
        if city and city != "all"
        else "高价值 AI、FDE 与一人公司(OPC)线下组局精选，含推荐理由与避坑指南"
    )
    updated = _rfc3339(datetime.datetime.now())

    feed = ET.Element("feed", {"xmlns": "http://www.w3.org/2005/Atom"})
    ET.SubElement(feed, "id").text = feed_id
    ET.SubElement(feed, "title").text = feed_title
    ET.SubElement(feed, "subtitle").text = feed_subtitle
    ET.SubElement(feed, "updated").text = updated
    ET.SubElement(feed, "generator", {"uri": site_url}).text = "OPC Activity Radar"
    ET.SubElement(feed, "link", {"rel": "self", "href": f"{site_url}{self_path}"})
    ET.SubElement(feed, "link", {"rel": "alternate", "href": site_url})

    for ev in filtered:
        start_dt, _end = parse_event_datetimes(ev)
        link = ev.signup_url or ev.source_url or site_url
        location = f"{ev.city} {ev.district or ''} {ev.venue or ''}".strip() or "待定"
        summary_text = (
            f"【评分】★ {ev.overall_score} 分推荐 | 分类: {ev.category}\n"
            f"【地点】{location}\n"
            f"【主办方】{ev.organizer}\n"
            f"【票价】{'免费' if ev.price == 0 else ev.price_text}\n"
            f"----------------------------------------\n"
            f"💡 为什么值得去：{ev.recommendation_reason}\n\n"
            f"🎯 适合谁：{ev.suitable_for}\n\n"
            f"🚫 不太适合谁：{ev.not_suitable_for}\n"
            f"----------------------------------------\n"
            f"🔗 报名链接：{link}\n"
            f"📌 数据来源：{ev.source_name}"
        )

        entry = ET.SubElement(feed, "entry")
        ET.SubElement(entry, "id").text = f"urn:opc-radar:event-{ev.id}"
        ET.SubElement(entry, "title").text = f"【{ev.category}·★{ev.overall_score}分】{ev.title}"
        ET.SubElement(entry, "link", {"rel": "alternate", "href": link})
        ET.SubElement(entry, "published").text = _rfc3339(start_dt)
        ET.SubElement(entry, "updated").text = updated
        author = ET.SubElement(entry, "author")
        ET.SubElement(author, "name").text = ev.organizer or "未知主办方"
        ET.SubElement(entry, "category", {"term": ev.category})
        ET.SubElement(
            entry, "summary", {"type": "text"}
        ).text = summary_text

    # minidom 缩进保持可读；ElementTree.tostring 已做 XML 转义
    from xml.dom.minidom import parseString

    xml_bytes = ET.tostring(feed, encoding="utf-8", xml_declaration=True)
    return parseString(xml_bytes).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
