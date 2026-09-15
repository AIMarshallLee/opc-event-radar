import os
import json
import urllib.request
import ssl
from typing import Dict, Any, Tuple

def evaluate_event_scores(
    title: str,
    description: str,
    organizer: str,
    category: str,
    price: float,
    confidence_score: int
) -> Dict[str, Any]:
    """
    根据任务书第 15 条规范评估 100 分制总分及五维子分：
    总分 100：
      - 主办方/嘉宾质量 (20)
      - 内容含金量 (20)
      - 商务连接价值 (20)
      - 创业实际价值 (15)
      - 稀缺性 (10)
      - 性价比 (10)
      - 信息可信度 (5)
    五维细分 (0-100)：
      learning_score, networking_score, business_score, technical_score, fundraising_score
    """
    text = f"{title} {description} {organizer}".lower()

    # 1. 主办方/嘉宾质量 (20)
    host_score = 12
    prestigious_hosts = ["nvidia", "阿里巴巴", "google", "字节跳动", "华为", "h3c", "美通社", "百度", "科技局", "政府", "开源中国"]
    if any(h in text for h in prestigious_hosts):
        host_score = 19
    elif organizer and organizer != "未知":
        host_score = 15

    # 2. 内容含金量 (20)
    content_score = 14
    if any(k in text for k in ["架构", "实践", "nim", "模型落地", "实战", "方法论", "工作流", "agentic", "vibe coding"]):
        content_score = 19
    elif any(k in text for k in ["峰会", "研讨", "沙龙", "大课"]):
        content_score = 16

    # 3. 商务连接价值 (20)
    business_val_score = 13
    if any(k in text for k in ["获客", "对接", "闭门", "外贸", "合伙人", "出海", "跨境", "生态大会"]):
        business_val_score = 18
    elif any(k in text for k in ["沙龙", "聚会", "社交"]):
        business_val_score = 15

    # 4. 创业实际价值 (15)
    startup_score = 10
    if any(k in text for k in ["opc", "一人公司", "超级个体", "创业", "商业模式", "路演", "融资", "冷启动"]):
        startup_score = 14
    elif any(k in text for k in ["变现", "出海", "跨境"]):
        startup_score = 12

    # 5. 稀缺性 (10)
    scarcity_score = 6
    if any(k in text for k in ["首发", "首次", "闭门", "限定", "共创", "邀请制", "黑客松", "hackathon"]):
        scarcity_score = 9
    elif any(k in text for k in ["技术开放日", "特别策划"]):
        scarcity_score = 8

    # 6. 性价比 (10)
    if price == 0:
        cost_score = 10
    elif price <= 100:
        cost_score = 8
    elif price <= 500:
        cost_score = 6
    else:
        cost_score = 4

    # 7. 信息可信度 (5)
    credibility_score = int(confidence_score * 0.05)

    overall = host_score + content_score + business_val_score + startup_score + scarcity_score + cost_score + credibility_score
    overall = min(99, max(45, overall))

    # 五维细分 (0-100)
    learning = min(98, max(50, int(content_score * 4.5 + host_score * 0.5)))
    networking = min(98, max(50, int(business_val_score * 4.0 + 20)))
    business = min(98, max(50, int(business_val_score * 3.5 + startup_score * 2.0)))
    technical = 85 if any(k in text for k in ["技术", "nvidia", "架构", "fde", "agent", "编程", "nim"]) else 65
    fundraising = 88 if any(k in text for k in ["路演", "融资", "投资人", "bp", "创投"]) else 55

    return {
        "overall_score": overall,
        "learning_score": learning,
        "networking_score": networking,
        "business_score": business,
        "technical_score": technical,
        "fundraising_score": fundraising
    }
