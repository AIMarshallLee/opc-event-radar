import urllib.request
import ssl
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.fetchers.base import BaseFetcher
from src.core.models import Source

class SegmentFaultFetcher(BaseFetcher):
    def __init__(self, source: Source):
        super().__init__(source)

    def fetch_raw_candidates(self) -> List[Dict[str, Any]]:
        candidates = []
        ctx = ssl._create_unverified_context()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        try:
            req = urllib.request.Request(self.source.url, headers=headers)
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            
            soup = BeautifulSoup(html, 'html.parser')
            seen_ids = set()

            for a in soup.find_all('a', href=re.compile(r'/e/(\d+)')):
                m = re.search(r'/e/(\d+)', a.get('href', ''))
                if not m:
                    continue
                eid = m.group(1)
                if eid in seen_ids:
                    continue
                
                title = a.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                
                card = a.find_parent('div')
                full_text = card.get_text(separator=' | ', strip=True) if card else title

                # 判断是否包含杭州关键词或全国线上开发者大赛
                is_hangzhou = any(k in full_text for k in ['杭州', '余杭', '西湖', '滨江'])
                is_online_tech = any(k in title for k in ['大赛', '挑战赛', '黑客松', 'AI', '智能体'])

                if not is_hangzhou and not is_online_tech:
                    continue

                full_url = f"https://segmentfault.com/e/{eid}"
                candidates.append({
                    "raw_title": title,
                    "description": full_text[:200],
                    "raw_time": "近期",
                    "raw_location": "杭州" if is_hangzhou else "线上",
                    "organizer": "思否技术社区联合主办",
                    "price_text": "免费",
                    "price": 0.0,
                    "source_id": self.source.id,
                    "source_name": self.source.name,
                    "source_url": full_url,
                    "signup_url": full_url,
                    "raw_text": full_text
                })
                seen_ids.add(eid)
        except Exception as e:
            print(f"[SegmentFaultFetcher] 抓取失败: {e}")

        return candidates
