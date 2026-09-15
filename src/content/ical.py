import re
import datetime
from typing import List, Optional
from src.core.models import Event

def format_ical_datetime(dt: datetime.datetime) -> str:
    """格式化为 iCalendar UTC 时间格式: 20260918T060000Z"""
    return dt.strftime("%Y%m%dT%H%M%SZ")

def parse_event_datetimes(ev: Event) -> tuple[datetime.datetime, datetime.datetime]:
    """
    尝试从活动 start_time 解析具体时间；若无法完全识别，默认以当年该月份为准，时长默认 2.5 小时
    """
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    hour = 14
    minute = 0

    m = re.search(r'(\d{1,2})月(\d{1,2})日', ev.start_time)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
    
    t_match = re.search(r'(\d{1,2}):(\d{2})', ev.start_time)
    if t_match:
        hour = int(t_match.group(1))
        minute = int(t_match.group(2))

    try:
        start_dt = datetime.datetime(year, month, day, hour, minute)
    except Exception:
        start_dt = now + datetime.timedelta(days=1, hours=2)

    end_dt = start_dt + datetime.timedelta(hours=2, minutes=30)
    return start_dt, end_dt

def escape_ical_text(text: str) -> str:
    if not text:
        return ""
    # RFC 5545: 转义逗号、分号和反斜杠，换行符转为 \n
    t = text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,')
    t = t.replace('\r\n', '\\n').replace('\n', '\\n')
    return t

def generate_ical_feed(events: List[Event], min_score: int = 75, category: Optional[str] = None) -> str:
    """
    生成标准 RFC 5545 iCalendar (.ics) 日历订阅源文本。
    支持全平台（Apple 日历、Google Calendar、Outlook、飞书日历）。
    """
    now = datetime.datetime.now()
    stamp_str = format_ical_datetime(now)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//OPC Activity Radar//Hangzhou AI OPC Events Radar//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:⚡ 杭州 AI / OPC 活动雷达",
        "X-WR-CALDESC:杭州本土高价值 AI 与一人公司(OPC)活动情报精选，包含深度推荐理由与避坑指南",
        "X-WR-TIMEZONE:Asia/Shanghai"
    ]

    filtered_events = [e for e in events if e.status != "ended" and e.overall_score >= min_score]
    if category and category != "all":
        filtered_events = [e for e in filtered_events if e.category == category]

    for ev in filtered_events:
        start_dt, end_dt = parse_event_datetimes(ev)
        dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
        dtend = end_dt.strftime("%Y%m%dT%H%M%S")

        desc_content = (
            f"【评分】★ {ev.overall_score} 分推荐 | 分类: {ev.category}\\n"
            f"【主办方】{ev.organizer}\\n"
            f"【票价】{'免费' if ev.price == 0 else ev.price_text}\\n"
            f"----------------------------------------\\n"
            f"💡 为什么值得去：{ev.recommendation_reason}\\n\\n"
            f"🎯 适合谁：{ev.suitable_for}\\n\\n"
            f"🚫 不太适合谁：{ev.not_suitable_for}\\n"
            f"----------------------------------------\\n"
            f"🔗 报名链接：{ev.signup_url or ev.source_url}\\n"
            f"📌 数据来源：{ev.source_name}"
        )

        location_str = f"杭州市 {ev.district or ''} {ev.venue or ''}".strip()

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:event-{ev.id}@opc-radar.hangzhou.ai",
            f"DTSTAMP:{stamp_str}",
            f"DTSTART;TZID=Asia/Shanghai:{dtstart}",
            f"DTEND;TZID=Asia/Shanghai:{dtend}",
            f"SUMMARY:【{ev.category}·★{ev.overall_score}分】{escape_ical_text(ev.title)}",
            f"DESCRIPTION:{desc_content}",
            f"LOCATION:{escape_ical_text(location_str)}",
            f"URL:{ev.signup_url or ev.source_url}",
            f"CATEGORIES:{ev.category},AI,OPC",
            # 提前 2 小时提醒
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:活动提醒: {escape_ical_text(ev.title)} 将在 2 小时后开始",
            "TRIGGER:-PT2H",
            "END:VALARM",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
