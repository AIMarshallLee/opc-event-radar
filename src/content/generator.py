import datetime
from typing import List
from src.core.database import get_all_events
from src.core.models import Event

def generate_radar_briefing(period: str = "this_week") -> str:
    """
    基于真实数据库生成活动简报（严禁虚构活动）。
    支持 period: 'today', 'tomorrow', 'this_week', 'weekend', 'monthly'
    """
    events = get_all_events()
    now = datetime.datetime.now()
    today_str = now.strftime("%Y年%m月%d日")
    
    # 过滤未过期的有效活动并按推荐度降序
    valid_events = [e for e in events if e.status != "ended" and e.overall_score >= 70]
    valid_events.sort(key=lambda x: x.overall_score, reverse=True)

    if not valid_events:
        return f"【OPC 活动情报 · 杭州站】（{today_str}）\n当前暂无高分未来活动更新，系统将持续通过流水线自动探测。"

    title_map = {
        "today": "今日杭州值得去 · AI/OPC 精选活动速递",
        "tomorrow": "明日杭州活动早知道 · AI/OPC 精选",
        "this_week": "本周杭州最值得去的 AI / OPC 活动榜单",
        "weekend": "周末极客充电指南 · 杭州 AI/OPC 创业者专属",
        "monthly": "本月杭州 AI / OPC 产业活动全景精选"
    }
    header_title = title_map.get(period, "杭州 AI / OPC 活动情报精选")

    lines = []
    lines.append(f"# ⚡ {header_title}")
    lines.append(f"> **生成时间**：{now.strftime('%Y-%m-%d %H:%M')} | **数据来源**：OPC 活动雷达全自动运营系统（纯真实数据库）")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 取 Top 5-8 场精选
    top_events = valid_events[:8]
    for idx, ev in enumerate(top_events, 1):
        price_tag = "免费" if ev.price == 0 else ev.price_text
        lines.append(f"### {idx}. 【{ev.category} · ★ {ev.overall_score}分】{ev.title}")
        lines.append(f"- **⏰ 时间**：{ev.start_time}")
        lines.append(f"- **📍 地点**：杭州 · {ev.district} | {ev.venue}")
        lines.append(f"- **🏢 主办方**：{ev.organizer}")
        lines.append(f"- **💰 票价**：{price_tag}")
        lines.append(f"- **💡 为什么值得去**：{ev.recommendation_reason}")
        lines.append(f"- **🎯 适合谁**：{ev.suitable_for}")
        lines.append(f"- **🚫 不太适合谁**：{ev.not_suitable_for}")
        lines.append(f"- **🔗 报名直达**：[{ev.source_name}报名链接]({ev.signup_url or ev.source_url})")
        lines.append("")

    lines.append("---")
    lines.append("💡 *声明：本简报由「OPC 活动情报·杭州活动雷达」根据公开数据自动清洗与研判生成，不构成任何商业投资建议。报名请认准官方入口。*")

    return "\n".join(lines)

if __name__ == "__main__":
    briefing = generate_radar_briefing("this_week")
    print(briefing)
