"""WeChatArticleFetcher 离线解析测试：mock 网络层，只测 HTML→结构化信息的解析与容错。"""
import datetime
import unittest
import urllib.error
from io import BytesIO
from unittest.mock import patch

from src.fetchers.wechat import WeChatArticleFetcher

ARTICLE_HTML = """<html><head>
<meta property="og:title" content="备选标题：AI 沙龙"/>
<meta property="og:image" content="https://mmbiz.qpic.cn/cover.jpg"/>
</head><body>
<h1 class="rich_media_title">杭州 AI Agent 实战闭门会（第 3 期）</h1>
<a id="js_name">OPC 增长社区</a>
<script>var createTime = '1730000000';</script>
<div id="js_content">
活动时间：11 月 8 日 14:00-17:00
活动地点：余杭区梦想小镇天使村 3 幢
报名方式：评论区扣 1
</div>
</body></html>"""

MINIMAL_HTML = "<html><head><title>空白页</title></head><body><p>没有结构化标记</p></body></html>"


def fake_urlopen(html: str, status: int = 200):
    class Resp:
        def __init__(self, body):
            self.body = body.encode("utf-8")

        def read(self):
            return self.body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return lambda req, timeout=None, context=None: Resp(html)


class TestWeChatArticleFetcher(unittest.TestCase):

    def setUp(self):
        self.fetcher = WeChatArticleFetcher()

    # 1. 非法链接直接拒绝
    def test_invalid_url_rejected(self):
        with self.assertRaises(ValueError):
            self.fetcher.fetch_article("不是链接")
        with self.assertRaises(ValueError):
            self.fetcher.fetch_article("")

    # 2. 完整文章：标题/主办方/时间/正文/封面全部提取
    def test_full_extraction(self):
        with patch("urllib.request.urlopen", fake_urlopen(ARTICLE_HTML)):
            data = self.fetcher.fetch_article("https://mp.weixin.qq.com/s/abc")
        self.assertEqual(data["title"], "杭州 AI Agent 实战闭门会（第 3 期）")
        self.assertEqual(data["organizer"], "OPC 增长社区")
        # fetcher 用 fromtimestamp（本机时区），期望值动态计算而不是写死
        expected = datetime.datetime.fromtimestamp(1730000000).strftime("%m月%d日")
        self.assertEqual(data["published_at"], expected)
        self.assertIn("活动时间：11 月 8 日", data["content"])
        self.assertEqual(data["image_url"], "https://mmbiz.qpic.cn/cover.jpg")

    # 3. 正文启发式：活动时间与地点
    def test_heuristic_time_location(self):
        with patch("urllib.request.urlopen", fake_urlopen(ARTICLE_HTML)):
            data = self.fetcher.fetch_article("https://mp.weixin.qq.com/s/abc")
        self.assertIn("11 月 8 日", data["start_time"])
        self.assertIn("梦想小镇", data["raw_location"])

    # 4. 缺失结构时的兜底：不抛错、用默认值、标题回退 og:title
    def test_minimal_html_fallbacks(self):
        fallback_html = ARTICLE_HTML.replace(
            '<h1 class="rich_media_title">杭州 AI Agent 实战闭门会（第 3 期）</h1>', '')
        with patch("urllib.request.urlopen", fake_urlopen(fallback_html)):
            data = self.fetcher.fetch_article("https://mp.weixin.qq.com/s/abc")
        self.assertEqual(data["title"], "备选标题：AI 沙龙")  # 回退 og:title

        with patch("urllib.request.urlopen", fake_urlopen(MINIMAL_HTML)):
            data = self.fetcher.fetch_article("https://mp.weixin.qq.com/s/xyz")
        self.assertEqual(data["title"], "微信公众号活动通知")
        self.assertEqual(data["organizer"], "微信公众号")
        self.assertEqual(data["published_at"], "近期")
        self.assertEqual(data["raw_location"], "杭州")

    # 5. 损坏的 createTime 不导致崩溃，保持默认"近期"
    def test_broken_create_time_tolerated(self):
        broken = ARTICLE_HTML.replace("1730000000", "'not-a-number'")
        with patch("urllib.request.urlopen", fake_urlopen(broken)):
            data = self.fetcher.fetch_article("https://mp.weixin.qq.com/s/abc")
        self.assertEqual(data["published_at"], "近期")

    # 6. 网络异常向上传播（由调用方决定怎么记录）
    def test_network_error_propagates(self):
        def boom(req, timeout=None, context=None):
            raise urllib.error.URLError("connection refused")
        with patch("urllib.request.urlopen", boom):
            with self.assertRaises(urllib.error.URLError):
                self.fetcher.fetch_article("https://mp.weixin.qq.com/s/abc")


if __name__ == "__main__":
    unittest.main()
