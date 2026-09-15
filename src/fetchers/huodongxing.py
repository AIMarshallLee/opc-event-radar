import urllib.request
import urllib.parse
import ssl
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.fetchers.base import BaseFetcher
from src.core.models import Source

class HuodongxingFetcher(BaseFetcher):
    def __init__(self, source: Source):
        super().__init__(source)

    def fetch_raw_candidates(self) -> List[Dict[str, Any]]:
        candidates = []
        ctx = ssl._create_unverified_context()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        # 支持从 source.url 或者多关键词采集
        urls_to_fetch = [self.source.url]
        if "qs=" not in self.source.url:
            urls_to_fetch = [
                "https://www.huodongxing.com/search?qs=" + urllib.parse.quote("杭州 AI"),
                "https://www.huodongxing.com/search?qs=" + urllib.parse.quote("杭州 OPC"),
                "https://www.huodongxing.com/search?qs=" + urllib.parse.quote("杭州 创业")
            ]
        
        seen_urls = set()
        for fetch_url in urls_to_fetch:
            try:
                req = urllib.request.Request(fetch_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.find_all('div', class_='search-tab-content-item-mesh')
                
                for item in items:
                    title_el = item.find('a', class_='item-title')
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    href = title_el.get('href', '')
                    if not href or href in seen_urls:
                        continue
                    
                    full_url = "https://www.huodongxing.com" + href if href.startswith('/') else href
                    full_text = item.get_text(separator=' | ', strip=True)
                    parts = [p.strip() for p in full_text.split(' | ') if p.strip()]

                    # 时间解析 (例如: 09月18日 | 14:00)
                    raw_time = "待定"
                    raw_location = "杭州"
                    organizer = "活动行发布方"

                    for idx, p in enumerate(parts):
                        if re.search(r'\d+月\d+日', p):
                            raw_time = p
                            if idx + 1 < len(parts) and re.match(r'^\d{1,2}:\d{2}', parts[idx+1]):
                                raw_time += " " + parts[idx+1]
                        if '杭州' in p or any(d in p for d in ['余杭', '滨江', '西湖', '上城', '拱墅', '萧山', '钱塘']):
                            raw_location = p

                    # 主办方通常在包含“粉丝”或“活动”前的一两项
                    for idx, p in enumerate(parts):
                        if p == '活动' and idx > 0:
                            organizer = parts[idx-1]
                            break

                    price_text = "免费"
                    price_val = 0.0
                    price_match = re.search(r'¥\s*(\d+)', full_text)
                    if price_match:
                        price_val = float(price_match.group(1))
                        price_text = f"¥{price_val}"

                    candidates.append({
                        "raw_title": title,
                        "description": f"活动行发布活动：{title}。地点：{raw_location}。主办方：{organizer}。",
                        "raw_time": raw_time,
                        "raw_location": raw_location,
                        "organizer": organizer,
                        "price_text": price_text,
                        "price": price_val,
                        "source_id": self.source.id,
                        "source_name": self.source.name,
                        "source_url": full_url,
                        "signup_url": full_url,
                        "raw_text": full_text
                    })
                    seen_urls.add(href)
            except Exception as e:
                print(f"[HuodongxingFetcher] 抓取失败 {fetch_url}: {e}")

        return candidates
