from typing import List, Dict, Any
from src.core.models import Source
from src.core.database import save_source, get_all_sources

DEFAULT_SOURCES: List[Dict[str, Any]] = [
    {
        "id": "lianpu_hangzhou",
        "name": "联谱 Lianpu·杭州科技与AI活动日历",
        "type": "opc_community",
        "url": "https://lianpu.com/city/hangzhou",
        "priority": 1,
        "enabled": True,
        "fetch_method": "http_html",
        "notes": "垂直度最高，覆盖 AI Agent、FDE、Vibe Coding、AI出海等高价值实战沙龙"
    },
    {
        "id": "huodongxing_ai",
        "name": "活动行·杭州 AI 技术沙龙与大会",
        "type": "event_platform",
        "url": "https://www.huodongxing.com/search?qs=%E6%9D%AD%E5%B7%9E+AI",
        "priority": 1,
        "enabled": True,
        "fetch_method": "http_html",
        "notes": "国内最大活动平台杭州站，包含大量 AI 商业落地、开发者大会与产业论坛"
    },
    {
        "id": "huodongxing_opc",
        "name": "活动行·杭州 OPC 一人公司与创业路演",
        "type": "event_platform",
        "url": "https://www.huodongxing.com/search?qs=%E6%9D%AD%E5%B7%9E+OPC",
        "priority": 1,
        "enabled": True,
        "fetch_method": "http_html",
        "notes": "针对杭州超级个体(OPC)、一人创业公司、AI+创投路演专栏"
    },
    {
        "id": "segmentfault_events",
        "name": "SegmentFault 思否·全球开发者技术沙龙",
        "type": "event_platform",
        "url": "https://segmentfault.com/events",
        "priority": 2,
        "enabled": True,
        "fetch_method": "http_html",
        "notes": "开发者技术社区官方活动中心，包含各厂商在杭技术巡回与开发者大会"
    },
    {
        "id": "hangzhou_opc_initiative",
        "name": "杭州打造全国 AI+OPC 创业新高地政务与园区动态",
        "type": "government",
        "url": "https://cn.bing.com/search?q=%E6%9D%AD%E5%B7%9E+AI+OPC+%E6%B4%BB%E5%8A%A8+2026",
        "priority": 2,
        "enabled": True,
        "fetch_method": "web_search",
        "notes": "聚焦杭州上城区、余杭区未来科技城、滨江区打造全国 AI+OPC 创业新高地的大会与政策对接"
    },
    {
        "id": "discovery_agent",
        "name": "Discovery Agent·全网杭州 AI/OPC 动态感知雷达",
        "type": "other",
        "url": "https://cn.bing.com/search?q=%E6%9D%AD%E5%B7%9E+%22Agent%22+OR+%22FDE%22+OR+%22Hacker+House%22+%E6%B4%BB%E5%8A%A8",
        "priority": 3,
        "enabled": True,
        "fetch_method": "web_search",
        "notes": "全网探测 Hacker House、Meetup、创客空间与新型孵化器公开活动"
    },
    {
        "id": "luma_hangzhou",
        "name": "Luma (lu.ma)·杭州极客沙龙与AI闭门会",
        "type": "opc_community",
        "url": "https://lu.ma/hangzhou",
        "priority": 1,
        "enabled": True,
        "fetch_method": "http_html",
        "notes": "覆盖全球及国内 AGI 原生圈、出海黑客松、Founder Meetup 与高纯度 FDE 研讨"
    },
    {
        "id": "wechat_search",
        "name": "搜狗微信·公众号公开活动与闭门会探针",
        "type": "wechat_public",
        "url": "https://weixin.sogou.com",
        "priority": 2,
        "enabled": True,
        "fetch_method": "web_search",
        "notes": "定期自动化检索微信公众号发布的杭州 AI、OPC、独立开发、生财同城局"
    }
]

def initialize_source_registry():
    existing = {s.id: s for s in get_all_sources()}
    for s_data in DEFAULT_SOURCES:
        if s_data["id"] not in existing:
            source = Source(**s_data)
            save_source(source)
            print(f"[Registry] 注册新数据源: {source.name} ({source.id})")
        else:
            # 保持现有状态，更新配置
            source = existing[s_data["id"]]
            source.name = s_data["name"]
            source.url = s_data["url"]
            source.notes = s_data["notes"]
            save_source(source)

def get_active_sources() -> List[Source]:
    all_s = get_all_sources()
    return [s for s in all_s if s.enabled and s.status != "disabled"]
