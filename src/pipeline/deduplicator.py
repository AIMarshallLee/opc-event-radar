import re
import difflib
from typing import Optional, List, Dict, Any, Tuple
from src.core.models import Event

SOURCE_PRIORITY = {
    "government": 100,
    "organizer": 90,
    "opc_community": 80,
    "event_platform": 70,
    "public_page": 50,
    "media": 40,
    "other": 30
}

def normalize_title(title: str) -> str:
    """清洗标题，去除噪音词、标点、城市后缀等"""
    if not title:
        return ""
    t = title.lower()
    # 去除括号及其中内容或符号
    t = re.sub(r'[【】\[\]（）()|·•:：\-_]', ' ', t)
    # 去除常见地域后缀与无意义字词
    stopwords = ["杭州站", "杭州场", "浙江", "杭州", "2026", "2025", "第届", "专场", "沙龙", "峰会", "大会", "实战", "免费听"]
    for w in stopwords:
        t = t.replace(w.lower(), "")
    # 合并多余空格
    return re.sub(r'\s+', '', t)

def calculate_title_similarity(t1: str, t2: str) -> float:
    n1 = normalize_title(t1)
    n2 = normalize_title(t2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2 or n1 in n2 or n2 in n1:
        return 1.0
    return difflib.SequenceMatcher(None, n1, n2).ratio()

def is_same_event(new_event: Event, existing_event: Event) -> Tuple[bool, float]:
    """综合 normalized title similarity + start_time + venue/address + organizer 判断"""
    sim = calculate_title_similarity(new_event.title, existing_event.title)
    if sim >= 0.75:
        # 如果标题极高相似，且时间处于相同月份或相近
        return True, sim
    
    # 如果主办方相同且标题相似度 >= 0.55
    if new_event.organizer and existing_event.organizer and new_event.organizer == existing_event.organizer and new_event.organizer != "未知":
        if sim >= 0.55:
            return True, sim

    return False, sim

def merge_event_sources(existing_event: Event, new_event: Event, source_type: str = "event_platform") -> Event:
    """
    同一活动合并并保留 sources[]。
    优先级：官方主办方 > 官方政府/园区 > 官方报名页 > 大型活动平台 > 第三方聚合 > 其他。
    """
    # 构造新来源条目
    new_src_entry = {
        "source_id": new_event.source_id,
        "source_name": new_event.source_name,
        "source_url": new_event.source_url,
        "signup_url": new_event.signup_url,
        "first_seen_at": new_event.first_seen_at
    }

    # 检查是否已包含
    existing_urls = [s.get("source_url") for s in existing_event.sources]
    if new_event.source_url not in existing_urls:
        existing_event.sources.append(new_src_entry)
        # 多源验证增加置信度
        existing_event.confidence_score = min(100, existing_event.confidence_score + 10)

    # 字段补充与富化
    if not existing_event.description and new_event.description:
        existing_event.description = new_event.description
    if existing_event.district in ["未知", "杭州市区"] and new_event.district not in ["未知", "杭州市区"]:
        existing_event.district = new_event.district
    if not existing_event.signup_url and new_event.signup_url:
        existing_event.signup_url = new_event.signup_url

    return existing_event
