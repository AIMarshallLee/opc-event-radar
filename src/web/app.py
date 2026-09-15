import os
import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.core.models import Event, PipelineRun
from src.core.database import (
    get_all_events, get_all_sources, get_business_signals,
    get_recent_pipeline_runs, save_event
)
from src.pipeline.engine import run_pipeline
from src.scheduler.runner import manage_event_lifecycles, EventScheduler
from src.pipeline.classifier import classify_event
from src.pipeline.location_validator import validate_hangzhou_location
from src.pipeline.deduplicator import normalize_title
from src.pipeline.verification import calculate_confidence_score
from src.pipeline.scorer import evaluate_event_scores
from src.pipeline.comment_generator import generate_ai_comment
from src.content.ical import generate_ical_feed
from src.pipeline.vision_extractor import extract_event_from_image
from src.fetchers.wechat import WeChatArticleFetcher
from fastapi import UploadFile, File, Response



app = FastAPI(title="OPC 活动情报 - 杭州 AI / OPC 活动雷达 V0.1")

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

scheduler_instance = EventScheduler()

@app.on_event("startup")
def startup_event():
    # 启动定时调度器
    scheduler_instance.start_background()

@app.on_event("shutdown")
def shutdown_event():
    scheduler_instance.stop()

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>OPC 活动情报 - 杭州 AI / OPC 活动雷达</h1><p>页面构建中...</p>"

@app.get("/api/events")
def list_events(
    city: str = Query("all", description="all, 杭州, 上海, 深圳, 厦门"),
    time_filter: str = Query("all", description="all, today, tomorrow, this_week, weekend"),
    category: str = Query("all", description="all, AI, OPC, FDE, Agent, 开发者, 创业, 投融资, 出海..."),
    sort_by: str = Query("recommendation", description="recommendation, time, free_first"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    all_events = get_all_events()
    now = datetime.datetime.now()
    today_md = now.strftime("%m月%d日")
    tomorrow_date = now + datetime.timedelta(days=1)
    tomorrow_md = tomorrow_date.strftime("%m月%d日")
    
    # 本周与周末计算
    weekday = now.weekday()  # 0=Mon, 6=Sun
    days_to_sat = 5 - weekday
    sat_date = now + datetime.timedelta(days=days_to_sat)
    sun_date = now + datetime.timedelta(days=days_to_sat + 1)
    sat_md = sat_date.strftime("%m月%d日")
    sun_md = sun_date.strftime("%m月%d日")

    filtered = []
    for ev in all_events:
        # 1. 过滤已过期 (除非指定查看)
        if ev.status == "ended":
            continue

        # 2. 城市筛选 (指定城市同时展示线上活动)
        if city != "all":
            if ev.city != city and ev.city != "线上":
                continue

        # 3. 分类筛选
        if category != "all" and ev.category != category:
            continue

        # 3. 时间切片筛选
        t_str = ev.start_time
        if time_filter == "today":
            if today_md not in t_str and "今天" not in t_str and ev.status != "today":
                continue
        elif time_filter == "tomorrow":
            if tomorrow_md not in t_str and "明天" not in t_str:
                continue
        elif time_filter == "weekend":
            if sat_md not in t_str and sun_md not in t_str and "周末" not in t_str:
                continue
        elif time_filter == "this_week":
            # 只要不是已结束且在未来两周内
            pass

        # 4. 搜索关键词
        if search:
            s_low = search.lower()
            corpus = f"{ev.title} {ev.organizer} {ev.venue} {' '.join(ev.tags)} {ev.district}".lower()
            if s_low not in corpus:
                continue

        filtered.append(ev)

    # 5. 排序处理
    if sort_by == "recommendation":
        # 综合排序：overall_score (权重高) + confidence_score
        filtered.sort(key=lambda x: (x.overall_score * 0.7 + x.confidence_score * 0.3), reverse=True)
    elif sort_by == "time":
        filtered.sort(key=lambda x: x.start_time)
    elif sort_by == "free_first":
        filtered.sort(key=lambda x: (x.price > 0, -x.overall_score))

    return {
        "total": len(filtered),
        "events": [e.dict() for e in filtered]
    }

@app.get("/api/events/{event_id}")
def get_event_detail(event_id: str):
    all_events = get_all_events()
    for ev in all_events:
        if ev.id == event_id:
            return ev.dict()
    raise HTTPException(status_code=404, detail="活动未找到")

@app.get("/api/observability")
def get_observability():
    events = get_all_events()
    sources = get_all_sources()
    runs = get_recent_pipeline_runs(limit=5)
    signals = get_business_signals()

    upcoming_count = len([e for e in events if e.status in ["upcoming", "today"]])
    verified_count = len([e for e in events if e.verification_status == "verified"])
    partially_count = len([e for e in events if e.verification_status == "partially_verified"])

    from collections import Counter
    city_counts = dict(Counter([e.city for e in events]))

    return {
        "summary": {
            "total_events": len(events),
            "upcoming_events": upcoming_count,
            "verified_events": verified_count,
            "partially_verified_events": partially_count,
            "active_sources": len([s for s in sources if s.status == "active"]),
            "total_sources": len(sources),
            "signals_count": len(signals),
            "city_breakdown": city_counts
        },
        "sources": [s.dict() for s in sources],
        "recent_runs": [r.dict() for r in runs],
        "business_signals": signals[:15]
    }

@app.get("/api/stats")
def get_stats():
    """轻量状态与健康检查别名端点"""
    return get_observability()

@app.post("/api/pipeline/trigger")
def trigger_pipeline():
    manage_event_lifecycles()
    run = run_pipeline()
    return {"status": "success", "run": run.dict()}

class ManualIntakeRequest(BaseModel):
    raw_text: str
    url: Optional[str] = ""

@app.post("/api/intake")
def manual_intake(req: ManualIntakeRequest):
    """
    任务书第 8 条：Manual Intake API，支持粘贴文本或链接手动补漏，
    自动完成结构化抽取、杭州校验、去重、验证、评分入库。
    """
    text = req.raw_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="内容不能为空")

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    title = lines[0] if lines else "杭州 AI 社区活动"
    
    is_hz, district, venue = validate_hangzhou_location(title, text)
    if not is_hz:
        return {"status": "rejected", "message": "非杭州本地相关活动，已自动拒绝"}

    category, tags = classify_event(title, text)
    conf_score, ver_status = calculate_confidence_score("public_page", "手工投递", "近期", venue, venue, req.url)
    scores = evaluate_event_scores(title, text, "社区投递", category, 0.0, conf_score)
    comments = generate_ai_comment(title, text, "社区投递", category, scores["overall_score"])

    event = Event(
        title=title,
        normalized_title=normalize_title(title),
        description=text[:500],
        start_time="近期",
        city="杭州",
        district=district,
        venue=venue,
        organizer="社区投递",
        price=0.0,
        price_text="免费",
        category=category,
        tags=tags,
        source_id="manual_intake",
        source_name="Manual Intake (手动补漏)",
        source_url=req.url or "https://opc.hangzhou.ai",
        signup_url=req.url or "",
        confidence_score=conf_score,
        verification_status=ver_status,
        overall_score=scores["overall_score"],
        learning_score=scores["learning_score"],
        networking_score=scores["networking_score"],
        business_score=scores["business_score"],
        technical_score=scores["technical_score"],
        fundraising_score=scores["fundraising_score"],
        recommendation_reason=comments.get("recommendation_reason", "社区精选活动"),
        suitable_for=comments.get("suitable_for", "OPC与AI爱好者"),
        not_suitable_for=comments.get("not_suitable_for", "无特定限制")
    )
    save_event(event)
    return {"status": "success", "event": event.dict()}

@app.get("/feed/hangzhou-ai.ics")
@app.get("/feed/events.ics")
def ical_subscription_feed(
    city: Optional[str] = Query(None, description="城市过滤 (杭州/上海/深圳/厦门)"),
    min_score: int = Query(75, description="最低综合评分过滤"),
    category: Optional[str] = Query(None, description="分类过滤")
):
    """
    全平台 iCalendar (.ics) 日历订阅源。
    支持在 iPhone、Mac Calendar、Google 日历、Outlook 中一键订阅，
    静默同步各城市高分 AI / OPC 活动并提前 2 小时推送日程提醒。
    """
    events = get_all_events()
    ics_text = generate_ical_feed(events, min_score=min_score, category=category, city=city)
    city_en_map = {
        "杭州": "hangzhou", "上海": "shanghai", "北京": "beijing",
        "深圳": "shenzhen", "广州": "guangzhou", "成都": "chengdu",
        "厦门": "xiamen", "武汉": "wuhan"
    }
    slug = city_en_map.get(city, "events") if city else "hangzhou"
    filename = f"{slug}-ai-events.ics"
    return Response(
        content=ics_text,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "max-age=1800"
        }
    )

@app.post("/api/intake/upload")
async def upload_poster_intake(file: UploadFile = File(...)):
    """
    多模态海报图片补漏摄入：直接上传微信群活动海报/长截图，
    调用视觉多模态大模型秒级抽取结构化信息并入库。
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="上传文件为空")

    parsed = extract_event_from_image(contents, file.filename or "poster.jpg")
    title = parsed.get("title", "杭州微信社群活动")
    raw_text = f"{title} {parsed.get('description', '')} {parsed.get('location', '')}"
    
    is_hz, district, venue = validate_hangzhou_location(title, parsed.get("location", "杭州"), raw_text)
    if not is_hz:
        return {"status": "rejected", "message": "图片识别为非杭州本地活动，已过滤"}

    cat, tags = classify_event(title, raw_text)
    conf_score, ver_status = calculate_confidence_score("public_page", parsed.get("organizer", "微信群"), parsed.get("start_time", "近期"), venue, venue, "")
    scores = evaluate_event_scores(title, raw_text, parsed.get("organizer", "微信群"), cat, 0.0, conf_score)
    comments = generate_ai_comment(title, raw_text, parsed.get("organizer", "微信群"), cat, scores["overall_score"])

    event = Event(
        title=title,
        normalized_title=normalize_title(title),
        description=parsed.get("description", "海报图片自动解析"),
        start_time=parsed.get("start_time", "近期"),
        city="杭州",
        district=district,
        venue=venue,
        organizer=parsed.get("organizer", "微信群组织"),
        price=0.0,
        price_text=parsed.get("price_text", "免费"),
        category=cat,
        tags=tags,
        source_id="vision_poster",
        source_name="海报视觉多模态直解",
        source_url="https://opc.hangzhou.ai",
        confidence_score=conf_score,
        verification_status=ver_status,
        overall_score=scores["overall_score"],
        learning_score=scores["learning_score"],
        networking_score=scores["networking_score"],
        business_score=scores["business_score"],
        technical_score=scores["technical_score"],
        fundraising_score=scores["fundraising_score"],
        recommendation_reason=comments.get("recommendation_reason", "社群高质活动"),
        suitable_for=comments.get("suitable_for", "OPC与AI开发者"),
        not_suitable_for=comments.get("not_suitable_for", "无明确需求者")
    )
    save_event(event)
    return {"status": "success", "event": event.dict(), "parsed": parsed}

class WeChatIntakeRequest(BaseModel):
    url: str

@app.post("/api/intake/wechat")
def wechat_article_intake(req: WeChatIntakeRequest):
    """
    微信公众号文章直读导入：输入任意微信文章链接 (https://mp.weixin.qq.com/s/...)，
    系统自动抓取文章标题、发布方公众号、正文全文与时间地点，
    执行杭州地域校验、行业分类、价值雷达评估，生成犀利评语并入库。
    """
    url = req.url.strip()
    if not url or "weixin.qq.com" not in url:
        raise HTTPException(status_code=400, detail="请输入有效的微信公众号文章链接 (以 https://mp.weixin.qq.com/ 开头)")

    fetcher = WeChatArticleFetcher()
    try:
        article = fetcher.fetch_article(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抓取微信公众号文章失败: {str(e)}")

    title = article.get("title", "")
    content = article.get("content", "")
    raw_loc = article.get("raw_location", "杭州")
    raw_text = f"{title} {content} {raw_loc}"

    is_hz, district, venue = validate_hangzhou_location(title, raw_loc, raw_text)
    if not is_hz:
        return {
            "status": "rejected",
            "message": f"文章《{title[:25]}...》经智能地域判定为非杭州本地活动，已被安全过滤。"
        }

    cat, tags = classify_event(title, raw_text)
    organizer = article.get("organizer", "微信公众号发布方")
    start_time = article.get("start_time", "近期")

    conf_score, ver_status = calculate_confidence_score("media", organizer, start_time, venue, venue, url)
    scores = evaluate_event_scores(title, raw_text, organizer, cat, 0.0, conf_score)
    comments = generate_ai_comment(title, raw_text, organizer, cat, scores["overall_score"])

    event = Event(
        title=title,
        normalized_title=normalize_title(title),
        description=content[:500],
        start_time=start_time,
        city="杭州",
        district=district,
        venue=venue,
        organizer=organizer,
        price=0.0,
        price_text="详见文章",
        category=cat,
        tags=tags,
        source_id="wechat_article",
        source_name=f"微信公众号: {organizer}",
        source_url=url,
        signup_url=url,
        confidence_score=conf_score,
        verification_status=ver_status,
        overall_score=scores["overall_score"],
        learning_score=scores["learning_score"],
        networking_score=scores["networking_score"],
        business_score=scores["business_score"],
        technical_score=scores["technical_score"],
        fundraising_score=scores["fundraising_score"],
        recommendation_reason=comments.get("recommendation_reason", f"由公众号【{organizer}】发布的杭州本地AI活动"),
        suitable_for=comments.get("suitable_for", "OPC创始人、AI从业者"),
        not_suitable_for=comments.get("not_suitable_for", "无明确业务场景的围观者")
    )
    save_event(event)
    return {"status": "success", "event": event.dict(), "article": article}


