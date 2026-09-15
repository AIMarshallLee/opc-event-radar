from typing import Tuple, Dict, Any, List

def calculate_confidence_score(
    source_type: str,
    organizer: str,
    start_time: str,
    venue: str,
    address: str,
    signup_url: str,
    sources_count: int = 1
) -> Tuple[int, str]:
    """
    计算活动可信度 confidence_score (0-100) 并确定 verification_status
    阈值规则：
      80-100: verified (自动发布)
      60-79: partially_verified (可发布并标记部分信息待核实)
      0-59: unverified (默认不公开)
    """
    score = 0

    # 1. 来源权威度 (30分)
    source_weight = {
        "government": 30,
        "organizer": 28,
        "opc_community": 26,
        "event_platform": 25,
        "public_page": 20,
        "other": 15
    }
    score += source_weight.get(source_type, 20)

    # 2. 时间明确度 (20分)
    if any(m in start_time for m in ["月", "-", ":"]) and len(start_time) >= 6:
        score += 20
    elif "近期" in start_time:
        score += 10
    else:
        score += 5

    # 3. 地点明确度 (20分)
    loc_combined = f"{venue} {address}"
    if any(k in loc_combined for k in ["号楼", "室", "大厦", "园区", "路", "街道", "中心", "小镇"]):
        score += 20
    elif any(k in loc_combined for k in ["余杭", "滨江", "西湖", "上城", "萧山", "拱墅", "线上"]):
        score += 15
    else:
        score += 5

    # 4. 主办方可靠度 (15分)
    if organizer and organizer not in ["未知", "主办方", "活动行发布方"]:
        score += 15
    else:
        score += 5

    # 5. 报名链接 (10分)
    if signup_url and signup_url.startswith("http"):
        score += 10

    # 6. 多源交叉印证 (额外加成 5分)
    if sources_count > 1:
        score += 5

    score = min(100, max(0, score))

    if score >= 80:
        status = "verified"
    elif score >= 60:
        status = "partially_verified"
    else:
        status = "unverified"

    return score, status
