import time
import datetime
import uuid
import concurrent.futures
from typing import Dict, Any, List
from src.core.models import Event, Source, PipelineRun
from src.core.database import (
    get_all_events, save_event, save_source, save_pipeline_run,
    record_business_signal
)
from src.sources.registry import get_active_sources, initialize_source_registry
from src.fetchers.lianpu import LianpuFetcher
from src.fetchers.huodongxing import HuodongxingFetcher
from src.fetchers.segmentfault import SegmentFaultFetcher
from src.fetchers.discovery import DiscoveryAgentFetcher
from src.fetchers.luma import LumaFetcher
from src.fetchers.wechat import WeChatSearchFetcher
from src.pipeline.location_validator import validate_hangzhou_location
from src.pipeline.deduplicator import normalize_title, is_same_event, merge_event_sources
from src.pipeline.classifier import classify_event
from src.pipeline.verification import calculate_confidence_score
from src.pipeline.scorer import evaluate_event_scores
from src.pipeline.comment_generator import generate_ai_comment

FETCHER_MAP = {
    "lianpu_hangzhou": LianpuFetcher,
    "huodongxing_ai": HuodongxingFetcher,
    "huodongxing_opc": HuodongxingFetcher,
    "segmentfault_events": SegmentFaultFetcher,
    "hangzhou_opc_initiative": DiscoveryAgentFetcher,
    "discovery_agent": DiscoveryAgentFetcher,
    "luma_hangzhou": LumaFetcher,
    "wechat_search": WeChatSearchFetcher
}

def process_single_candidate(cand: Dict[str, Any], existing_events: List[Event]) -> Dict[str, Any]:
    """处理单个候选活动的清洗、打分与评语生成"""
    title = cand.get("raw_title", "").strip()
    if not title:
        return {"status": "rejected", "reason": "empty_title"}

    raw_loc = cand.get("raw_location", "")
    raw_text = cand.get("raw_text", "")
    
    # 杭州地域强校验
    is_hz, district, venue = validate_hangzhou_location(title, raw_loc, raw_text)
    if not is_hz:
        return {"status": "rejected", "reason": "not_hangzhou"}

    norm_title = normalize_title(title)
    organizer = cand.get("organizer", "未知").strip()
    desc = cand.get("description", "").strip()
    time_str = cand.get("raw_time", "近期").strip()
    price_val = float(cand.get("price", 0.0))
    price_txt = cand.get("price_text", "免费")
    src_id = cand.get("source_id", "")
    src_name = cand.get("source_name", "")
    src_url = cand.get("source_url", "")
    signup_url = cand.get("signup_url", src_url)

    # 查重比对
    for ex in existing_events:
        sim_norm = normalize_title(ex.title)
        if norm_title == sim_norm or norm_title in sim_norm or sim_norm in norm_title:
            # 合并来源
            merged = merge_event_sources(ex, Event(
                title=title, normalized_title=norm_title, start_time=time_str,
                source_id=src_id, source_name=src_name, source_url=src_url, signup_url=signup_url
            ))
            merged.last_seen_at = datetime.datetime.now().isoformat()
            merged.updated_at = datetime.datetime.now().isoformat()
            save_event(merged)
            return {"status": "duplicate", "event": merged}

    # 新增活动
    primary_cat, tags = classify_event(title, desc)
    conf_score, ver_status = calculate_confidence_score(
        source_type="event_platform" if "huodongxing" in src_id or "segmentfault" in src_id else "opc_community",
        organizer=organizer,
        start_time=time_str,
        venue=venue,
        address=venue,
        signup_url=signup_url,
        sources_count=1
    )

    scores = evaluate_event_scores(
        title=title,
        description=desc,
        organizer=organizer,
        category=primary_cat,
        price=price_val,
        confidence_score=conf_score
    )

    ai_comments = generate_ai_comment(
        title=title,
        description=desc,
        organizer=organizer,
        category=primary_cat,
        overall_score=scores["overall_score"]
    )

    event_status = "upcoming"
    if "今天" in time_str:
        event_status = "today"

    event = Event(
        title=title,
        normalized_title=norm_title,
        description=desc,
        start_time=time_str,
        city="杭州",
        district=district,
        venue=venue,
        address=venue if venue != "杭州" else "",
        organizer=organizer,
        price=price_val,
        price_text=price_txt,
        category=primary_cat,
        tags=tags,
        source_id=src_id,
        source_name=src_name,
        source_url=src_url,
        signup_url=signup_url,
        sources=[{
            "source_id": src_id,
            "source_name": src_name,
            "source_url": src_url,
            "signup_url": signup_url,
            "first_seen_at": datetime.datetime.now().isoformat()
        }],
        confidence_score=conf_score,
        verification_status=ver_status,
        overall_score=scores["overall_score"],
        learning_score=scores["learning_score"],
        networking_score=scores["networking_score"],
        business_score=scores["business_score"],
        technical_score=scores["technical_score"],
        fundraising_score=scores["fundraising_score"],
        recommendation_reason=ai_comments.get("recommendation_reason", ""),
        suitable_for=ai_comments.get("suitable_for", ""),
        not_suitable_for=ai_comments.get("not_suitable_for", ""),
        status=event_status
    )
    save_event(event)

    # 商业信号
    if organizer and organizer not in ["未知", "主办方", "活动行发布方"]:
        record_business_signal(
            organization=organizer,
            signal_type="top_organizer",
            evidence=f"在杭发起《{title}》",
            potential_value="高频AI/OPC活动组织者"
        )
    if district in ["余杭", "滨江", "上城", "西湖", "萧山"] and venue and venue not in ["待定", "杭州", "线上"]:
        record_business_signal(
            organization=f"{district}·{venue[:15]}",
            signal_type="high_frequency_park",
            evidence=f"承办活动《{title}》",
            potential_value="活跃AI/OPC创业集聚区"
        )

    return {"status": "new", "event": event}

def run_pipeline() -> PipelineRun:
    start_time_iso = datetime.datetime.now().isoformat()
    initialize_source_registry()
    active_sources = get_active_sources()
    existing_events = get_all_events()

    run = PipelineRun(
        start_time=start_time_iso,
        scanned_sources=len(active_sources)
    )

    all_raw_candidates: List[Dict[str, Any]] = []

    # 1. 抓取各源 (单源隔离容错)
    for src in active_sources:
        fetcher_cls = FETCHER_MAP.get(src.id)
        if not fetcher_cls:
            continue
        try:
            fetcher = fetcher_cls(src)
            cands = fetcher.fetch_raw_candidates()
            all_raw_candidates.extend(cands)
            src.last_checked_at = datetime.datetime.now().isoformat()
            src.last_success_at = datetime.datetime.now().isoformat()
            src.failure_count = 0
            src.status = "active"
            save_source(src)
            run.success_sources += 1
            print(f"[Pipeline] 数据源 {src.name} 抓取成功，获得 {len(cands)} 个候选")
        except Exception as e:
            src.last_checked_at = datetime.datetime.now().isoformat()
            src.failure_count += 1
            if src.failure_count >= 3:
                src.status = "degraded"
            save_source(src)
            run.failed_sources += 1
            print(f"[Pipeline] 数据源 {src.name} 异常隔离: {e}")

    run.candidate_events = len(all_raw_candidates)

    # 2. 并发处理候选活动（多线程并发加速评分与评语生成）
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_cand = {executor.submit(process_single_candidate, c, existing_events): c for c in all_raw_candidates}
        for future in concurrent.futures.as_completed(future_to_cand):
            try:
                res = future.result()
                st = res.get("status")
                if st == "new":
                    run.new_events += 1
                    existing_events.append(res["event"])
                elif st == "duplicate":
                    run.duplicate_events += 1
                elif st == "rejected":
                    run.rejected_events += 1
            except Exception as e:
                run.rejected_events += 1

    run.end_time = datetime.datetime.now().isoformat()
    run.status = "success" if run.failed_sources == 0 else "partial_failure"
    run.summary = (
        f"扫描 {run.scanned_sources} 个源 (成功 {run.success_sources}, 失败 {run.failed_sources})，"
        f"抓取 {run.candidate_events} 个候选，入库新活动 {run.new_events} 个，合并重复 {run.duplicate_events} 个，"
        f"地域/噪音拒绝 {run.rejected_events} 个。"
    )
    save_pipeline_run(run)
    return run

if __name__ == "__main__":
    print("=== 开始并发执行完整自动化运营流水线 Pipeline ===")
    r = run_pipeline()
    print(r.summary)
