import urllib.request
import urllib.parse
import ssl
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.fetchers.base import BaseFetcher
from src.core.models import Source

class DiscoveryAgentFetcher(BaseFetcher):
    def __init__(self, source: Source):
        super().__init__(source)

    def fetch_raw_candidates(self) -> List[Dict[str, Any]]:
        candidates = []
        ctx = ssl._create_unverified_context()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        search_queries = [
            "杭州 AI+OPC 创业大会 2026",
            "杭州 AI Agent 沙龙 报名",
            "杭州 Hacker House 活动"
        ]

        seen_titles = set()
        for q in search_queries:
            try:
                url = f"https://cn.bing.com/search?q={urllib.parse.quote(q)}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                results = soup.find_all('li', class_='b_algo')

                for r in results:
                    h2 = r.find('h2')
                    if not h2:
                        continue
                    a_tag = h2.find('a')
                    if not a_tag:
                        continue
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get('href', '')
                    caption = r.find('div', class_='b_caption')
                    desc = caption.get_text(strip=True) if caption else ""

                    if not any(k in title for k in ['杭州', 'OPC', 'AI', '大会', '沙龙', '展', '路演']):
                        continue
                    if title in seen_titles:
                        continue

                    candidates.append({
                        "raw_title": title,
                        "description": desc,
                        "raw_time": "近期",
                        "raw_location": "杭州",
                        "organizer": "杭州市科技/产业园区",
                        "price_text": "免费",
                        "price": 0.0,
                        "source_id": self.source.id,
                        "source_name": self.source.name,
                        "source_url": link,
                        "signup_url": link,
                        "raw_text": f"{title} | {desc}"
                    })
                    seen_titles.add(title)
            except Exception as e:
                print(f"[DiscoveryAgent] 查询 [{q}] 失败: {e}")

        return candidates
