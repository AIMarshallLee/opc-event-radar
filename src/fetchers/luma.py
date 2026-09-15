import urllib.request
import urllib.parse
import ssl
import json
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from src.fetchers.base import BaseFetcher
from src.core.models import Source

class LumaFetcher(BaseFetcher):
    """
    Luma (lu.ma) 极客沙龙与 AI/OPC 闭门会采集器。
    Luma 是当前全球及国内 AGI 原生圈、出海团队、黑客松最青睐的活动发布平台。
    """
    def __init__(self, source: Source):
        super().__init__(source)
        self.ctx = ssl._create_unverified_context()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

    def fetch_raw_candidates(self) -> List[Dict[str, Any]]:
        candidates = []
        target_urls = [
            "https://lu.ma/hangzhou",
            "https://lu.ma/explore?query=Hangzhou",
            "https://lu.ma/explore?query=AI"
        ]

        for target_url in target_urls:
            try:
                req = urllib.request.Request(target_url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=8, context=self.ctx) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")

                # 1. 尝试从 Next.js 的 __NEXT_DATA__ 脚本中提取结构化状态
                soup = BeautifulSoup(html, "html.parser")
                next_data_el = soup.find("script", id="__NEXT_DATA__")
                if next_data_el and next_data_el.string:
                    try:
                        data = json.loads(next_data_el.string)
                        events_found = self._extract_events_from_json(data)
                        for ev in events_found:
                            title = ev.get("name") or ev.get("title", "")
                            if not title:
                                continue
                            geo = ev.get("geo_address_info") or {}
                            city = geo.get("city", "") or geo.get("full_address", "") or "杭州"
                            if "hangzhou" not in city.lower() and "杭州" not in city and "hangzhou" not in title.lower() and "杭州" not in title:
                                continue

                            candidates.append({
                                "raw_title": title,
                                "description": ev.get("description", "") or ev.get("summary", ""),
                                "raw_time": ev.get("start_at", "近期"),
                                "raw_location": geo.get("full_address", "杭州市"),
                                "organizer": ev.get("host_name") or "Luma Community",
                                "price_text": "免费 (需审核)" if ev.get("require_approval") else "免费",
                                "price": 0.0,
                                "source_id": self.source.id,
                                "source_name": self.source.name,
                                "source_url": f"https://lu.ma/{ev.get('url', '')}" if ev.get("url") else target_url,
                                "signup_url": f"https://lu.ma/{ev.get('url', '')}" if ev.get("url") else target_url,
                                "raw_text": f"{title} | 主办: {ev.get('host_name', '')} | Luma AI/OPC 沙龙"
                            })
                    except Exception:
                        pass

                # 2. DOM 备用解析
                event_cards = soup.find_all("div", class_=re.compile(r"event-card|card|timeline-item"))
                for card in event_cards:
                    title_el = card.find(["h2", "h3", "h4", "a"])
                    if not title_el:
                        continue
                    t_text = title_el.get_text(strip=True)
                    if len(t_text) < 4:
                        continue
                    link = title_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://lu.ma" + link

                    candidates.append({
                        "raw_title": t_text,
                        "description": card.get_text(strip=True)[:200],
                        "raw_time": "近期",
                        "raw_location": "杭州",
                        "organizer": "Luma 开发者",
                        "price_text": "免费",
                        "price": 0.0,
                        "source_id": self.source.id,
                        "source_name": self.source.name,
                        "source_url": link or target_url,
                        "signup_url": link or target_url,
                        "raw_text": f"{t_text} | Luma 闭门沙龙"
                    })

            except Exception as e:
                print(f"[LumaFetcher] 抓取目标 {target_url} 提示: {e}")

        return candidates

    def _extract_events_from_json(self, obj: Any) -> List[Dict[str, Any]]:
        results = []
        if isinstance(obj, dict):
            if "name" in obj and ("start_at" in obj or "geo_address_info" in obj or "hosts" in obj):
                results.append(obj)
            for v in obj.values():
                results.extend(self._extract_events_from_json(v))
        elif isinstance(obj, list):
            for item in obj:
                results.extend(self._extract_events_from_json(item))
        return results
