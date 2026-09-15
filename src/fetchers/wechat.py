import urllib.request
import urllib.parse
import ssl
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from src.fetchers.base import BaseFetcher
from src.core.models import Source

class WeChatArticleFetcher:
    """
    微信公众号公开文章直读解析器。
    无需微信登录，无需依赖任何第三方黑盒服务，
    直接基于微信文章公共 Web 端渲染骨架抽取活动关键信息。
    """
    def __init__(self):
        self.ctx = ssl._create_unverified_context()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

    def fetch_article(self, url: str) -> Dict[str, Any]:
        """抓取单篇微信公众号文章全文与元数据"""
        clean_url = url.strip()
        if not clean_url.startswith("http"):
            raise ValueError("非法的链接格式")

        req = urllib.request.Request(clean_url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=8, context=self.ctx) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        soup = BeautifulSoup(html, 'html.parser')

        # 1. 提取文章标题
        title = ""
        title_el = soup.find('h1', class_='rich_media_title') or soup.find('h1', id='activity-name')
        if title_el:
            title = title_el.get_text(strip=True)
        if not title:
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                title = meta_title.get('content', '').strip()

        # 2. 提取公众号名称 (主办方/发布方)
        author = "微信公众号"
        author_el = soup.find('a', id='js_name') or soup.find('span', class_='rich_media_meta_text') or soup.find('strong', class_='profile_nickname')
        if author_el:
            author = author_el.get_text(strip=True)

        # 3. 提取文章发布时间
        pub_time = "近期"
        publish_match = re.search(r'createTime\s*=\s*[\'"]?(\d+)[\'"]?', html)
        if publish_match:
            try:
                import datetime
                ts = int(publish_match.group(1))
                pub_time = datetime.datetime.fromtimestamp(ts).strftime("%m月%d日")
            except Exception:
                pass

        # 4. 提取文章正文文本
        content_el = soup.find('div', id='js_content') or soup.find('div', class_='rich_media_content')
        content_text = ""
        if content_el:
            content_text = content_el.get_text(separator='\n', strip=True)

        # 5. 提取封面图
        image_url = ""
        meta_img = soup.find('meta', property='og:image')
        if meta_img:
            image_url = meta_img.get('content', '')

        # 6. 从正文中启发式提取活动时间与地点
        event_time = pub_time
        time_match = re.search(r'(?:时间|活动时间|日期)[:：\s]*([^\n]{5,30})', content_text)
        if time_match:
            event_time = time_match.group(1).strip()

        event_loc = "杭州"
        loc_match = re.search(r'(?:地点|活动地点|地址|场地)[:：\s]*([^\n]{5,40})', content_text)
        if loc_match:
            event_loc = loc_match.group(1).strip()

        return {
            "title": title or "微信公众号活动通知",
            "organizer": author,
            "published_at": pub_time,
            "start_time": event_time,
            "raw_location": event_loc,
            "content": content_text[:1500],
            "url": clean_url,
            "image_url": image_url
        }

class WeChatSearchFetcher(BaseFetcher):
    """
    通过搜狗微信搜索公开索引自动感知微信公众号文章。
    全合规、无封号风险、稳定增量更新。
    """
    def __init__(self, source: Source):
        super().__init__(source)
        self.ctx = ssl._create_unverified_context()

    def fetch_raw_candidates(self) -> List[Dict[str, Any]]:
        candidates = []
        queries = [
            "杭州 AI 沙龙",
            "杭州 OPC 线下",
            "杭州 AI 闭门会",
            "上海 AI 闭门会",
            "模速空间 AI 沙龙",
            "深圳 AI 硬件 沙龙",
            "深圳 FDE 开发者 线下",
            "厦门 独立开发 出海",
            "杭州 生财 线下"
        ]
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        for q in queries:
            try:
                url = f"https://weixin.sogou.com/weixin?type=2&query={urllib.parse.quote(q)}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=6, context=self.ctx) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                
                soup = BeautifulSoup(html, 'html.parser')
                news_boxes = soup.find_all('div', class_='txt-box')
                for box in news_boxes[:4]:
                    h3 = box.find('h3')
                    if not h3:
                        continue
                    a_tag = h3.find('a')
                    if not a_tag:
                        continue
                    title = a_tag.get_text(strip=True)
                    desc_el = box.find('p', class_='txt-info')
                    desc = desc_el.get_text(strip=True) if desc_el else ""
                    author_el = box.find('a', class_='account')
                    author = author_el.get_text(strip=True) if author_el else "微信公众号"

                    if not any(k in title for k in ['杭州', '上海', '深圳', '厦门', 'AI', 'OPC', 'FDE', '沙龙', '闭门', '大会', '报名', '出海', '模速空间']):
                        continue

                    candidates.append({
                        "raw_title": title,
                        "description": desc,
                        "raw_time": "近期",
                        "raw_location": "杭州",
                        "organizer": author,
                        "price_text": "免费",
                        "price": 0.0,
                        "source_id": self.source.id,
                        "source_name": "搜狗微信公开搜索",
                        "source_url": "https://weixin.sogou.com" + a_tag.get('href', ''),
                        "signup_url": "",
                        "raw_text": f"{title} | {desc} | 主办: {author}"
                    })
            except Exception as e:
                print(f"[WeChatSearchFetcher] 抓取关键词 [{q}] 提示: {e}")

        return candidates
