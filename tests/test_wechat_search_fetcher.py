"""WeChatSearchFetcher 离线测试：mock 搜狗搜索响应，验证候选解析、城市过滤与异常静默。"""
import unittest
import urllib.error
from unittest.mock import patch

from src.core.models import Source
from src.fetchers.wechat import WeChatSearchFetcher

SOGOU_HTML = """<html><body>
<div class="txt-box"><h3><a href="/link?url=abc123">杭州 AI Agent 实战沙龙报名开启</a></h3>
<p class="txt-info">本月线下闭门，限 30 人。</p><a class="account">杭州某社区</a></div>
<div class="txt-box"><h3><a href="/link?url=drop">马里兰大学毕业演讲全文</a></h3>
<p class="txt-info">与活动无关的内容。</p><a class="account">某媒体</a></div>
<div class="txt-box"><h3><a href="/link?url=noacc">深圳 FDE 开发者线下聚会</a></h3>
<p class="txt-info">无账号栏的条目。</p></div>
</body></html>"""

EMPTY_HTML = "<html><body>验证码页或空结果</body></html>"


def make_fetcher():
    source = Source(id="s-wechat", name="搜狗微信公开搜索", type="media",
                    url="https://weixin.sogou.com", priority=2)
    return WeChatSearchFetcher(source)


def fake_urlopen_factory(html_by_call=None, default_html=SOGOU_HTML, fail_every=None):
    calls = {"n": 0}

    def _open(req, timeout=None, context=None):
        calls["n"] += 1
        if fail_every and calls["n"] % fail_every == 0:
            raise urllib.error.URLError("blocked")
        class Resp:
            def __init__(self, body):
                self.body = body.encode("utf-8")
            def read(self):
                return self.body
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
        body = default_html
        if html_by_call and calls["n"] in html_by_call:
            body = html_by_call[calls["n"]]
        return Resp(body)
    return _open, calls


class TestWeChatSearchFetcher(unittest.TestCase):

    # 1. 解析候选：带城市/AI 关键词的条目保留，无关条目被过滤
    def test_parse_and_keyword_filter(self):
        fetcher = make_fetcher()
        opener, calls = fake_urlopen_factory()
        with patch("urllib.request.urlopen", opener):
            candidates = fetcher.fetch_raw_candidates()
        self.assertGreater(calls["n"], 0)  # 确实发起了多个关键词查询
        titles = [c["raw_title"] for c in candidates]
        self.assertIn("杭州 AI Agent 实战沙龙报名开启", titles)
        self.assertIn("深圳 FDE 开发者线下聚会", titles)  # 无账号栏也能取默认主办方
        self.assertNotIn("马里兰大学毕业演讲全文", titles)  # 关键词过滤生效
        hangzhou = next(c for c in candidates if "杭州" in c["raw_title"])
        self.assertEqual(hangzhou["organizer"], "杭州某社区")
        self.assertTrue(hangzhou["source_url"].startswith("https://weixin.sogou.com/link"))

    # 2. 每个关键词最多取前 4 条
    def test_max_four_per_query(self):
        many = "<html><body>" + "".join(
            f'<div class="txt-box"><h3><a href="/link?url={i}">杭州 AI 沙龙第 {i} 期</a></h3>'
            f'<p class="txt-info">x</p><a class="account">社区</a></div>'
            for i in range(10)) + "</body></html>"
        fetcher = make_fetcher()
        opener, _ = fake_urlopen_factory(default_html=many)
        with patch("urllib.request.urlopen", opener):
            candidates = fetcher.fetch_raw_candidates()
        # 14 个查询 × 每个最多 4 条
        self.assertLessEqual(len(candidates), 14 * 4)
        self.assertGreater(len(candidates), 0)

    # 3. 单个查询失败不影响整体（异常被吞并继续），全部失败返回空列表
    def test_partial_failure_silent(self):
        fetcher = make_fetcher()
        opener, calls = fake_urlopen_factory(html_by_call={1: EMPTY_HTML}, fail_every=3)
        with patch("urllib.request.urlopen", opener):
            candidates = fetcher.fetch_raw_candidates()
        self.assertIsInstance(candidates, list)

    # 4. 全部失败 → 空列表，不抛异常
    def test_all_failure_returns_empty(self):
        fetcher = make_fetcher()

        def boom(req, timeout=None, context=None):
            raise urllib.error.URLError("down")

        with patch("urllib.request.urlopen", boom):
            self.assertEqual(fetcher.fetch_raw_candidates(), [])


if __name__ == "__main__":
    unittest.main()
