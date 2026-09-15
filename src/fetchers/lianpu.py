import urllib.request
import ssl
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from src.fetchers.base import BaseFetcher
from src.core.models import Source

class LianpuFetcher(BaseFetcher):
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
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            
            soup = BeautifulSoup(html, 'html.parser')
            seen_urls = set()

            for a in soup.find_all('a', href=re.compile(r'/event/')):
                href = a.get('href')
                if not href or href in seen_urls:
                    continue
                
                # 寻找外层卡片容器
                card = a.find_parent('div')
                while card and card.name == 'div' and len(card.get_text(strip=True)) < 50:
                    card = card.find_parent('div')
                
                if not card:
                    continue
                
                full_text = card.get_text(separator=' | ', strip=True)
                parts = [p.strip() for p in full_text.split(' | ') if p.strip()]
                
                # 提取主办方
                organizer = parts[0] if parts and not parts[0].startswith('¥') and len(parts[0]) < 25 else "未知"

                # 提取标题
                title = a.get_text(strip=True)
                title_candidates = [p for p in parts if len(p) > 5 and not p.startswith('¥') and not re.search(r'^\d+月\d+日', p) and not p.startswith('杭州 /') and p != organizer]
                if (not title or len(title) < 4 or title == organizer) and title_candidates:
                    title = title_candidates[0]


                # 提取描述
                description = ""
                for p in parts:
                    if len(p) > 30 and p != title:
                        description = p
                        break

                # 提取时间与地点
                time_str = "待定"
                location_str = "杭州"
                for i, p in enumerate(parts):
                    if re.search(r'\d+月\d+日', p) or re.search(r'\d{4}-\d{2}-\d{2}', p):
                        # 合并时间片段
                        time_str = p
                        if i + 2 < len(parts) and parts[i+1] == '-':
                            time_str += f" - {parts[i+2]}"
                    if '杭州 /' in p or '杭州市' in p or any(d in p for d in ['余杭', '滨江', '西湖', '上城', '拱墅', '萧山']):
                        location_str = p

                # 提取价格
                price_text = "免费"
                price_val = 0.0
                price_match = re.search(r'¥\s*(\d+)', full_text)
                if price_match:
                    price_val = float(price_match.group(1))
                    price_text = f"¥{price_val}"
                elif '免费' in full_text:
                    price_text = "免费"
                    price_val = 0.0

                full_url = "https://lianpu.com" + href if href.startswith('/') else href
                candidates.append({
                    "raw_title": title,
                    "description": description,
                    "raw_time": time_str,
                    "raw_location": location_str,
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
            print(f"[LianpuFetcher] 抓取异常: {e}")

        return candidates
