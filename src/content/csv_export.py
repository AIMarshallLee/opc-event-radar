import csv
import io
from typing import List, Optional

from src.content.rss import filter_events
from src.core.models import Event


def _csv_cell(value) -> str:
    """CSV 注入防护：以 = + - @ 开头的单元格前加单引号，防止在 Excel 中被当公式执行。"""
    text = "" if value is None else str(value)
    if text[:1] in {"=", "+", "-", "@"}:
        return "'" + text
    return text


def generate_events_csv(events: List[Event], min_score: int = 75, category: Optional[str] = None, city: Optional[str] = None) -> str:
    """生成活动列表 CSV（UTF-8 with BOM，Excel 打开中文不乱码）。

    过滤口径与 /feed/events.ics、/feed/events.xml 完全一致（状态/评分/城市/分类），
    输出按开始时间升序；字段见 header。
    """
    filtered = filter_events(events, min_score=min_score, category=category, city=city)
    filtered.sort(key=lambda e: (e.start_time, e.city))

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow([
        "id", "title", "category", "city", "district", "venue",
        "start_time", "overall_score", "confidence_score",
        "organizer", "price_text", "status",
        "signup_url", "source_name", "source_url", "recommendation_reason",
    ])
    for ev in filtered:
        writer.writerow([
            _csv_cell(ev.id), _csv_cell(ev.title), _csv_cell(ev.category),
            _csv_cell(ev.city), _csv_cell(ev.district), _csv_cell(ev.venue),
            _csv_cell(ev.start_time), ev.overall_score, ev.confidence_score,
            _csv_cell(ev.organizer), _csv_cell("免费" if ev.price == 0 else ev.price_text),
            _csv_cell(ev.status),
            _csv_cell(ev.signup_url or ev.source_url),
            _csv_cell(ev.source_name), _csv_cell(ev.source_url),
            _csv_cell(ev.recommendation_reason),
        ])
    return "\ufeff" + buf.getvalue()
