from typing import Tuple, List

VALID_CATEGORIES = [
    "AI", "OPC", "FDE", "Agent", "开发者", "创业", "投融资",
    "出海", "电商", "内容", "企业服务", "政策/园区", "具身智能", "其他"
]

CATEGORY_RULES = {
    "OPC": ["opc", "一人公司", "超级个体", "个人创业", "单人成军", "自由职业", "小微团队", "秒哒"],
    "FDE": ["fde", "openfde", "场景共创", "企业落地共创"],
    "Agent": ["agent", "智能体", "多智能体", "agentic", "自动化流程", "工作流", "autogpt"],
    "具身智能": ["具身智能", "人形机器人", "机器人", "物理ai", "embodied"],
    "出海": ["出海", "跨境", "外贸", "tiktok", "亚马逊", "独立站", "全球化", "海外"],
    "投融资": ["路演", "融资", "投融资", "投资人", "天使轮", "创投", "bp", "闭门对接"],
    "创业": ["创业", "孵化", "合伙人", "创始人", "商业模式", "创业者", "冷启动"],
    "开发者": ["开发者", "技术开放日", "架构", "开源", "编程", "vibe coding", "hackathon", "黑客松", "代码", "github"],
    "电商": ["电商", "选品", "带货", "跨境电商", "买手"],
    "内容": ["自媒体", "短视频", "漫剧", "小红书", "内容生产", "文案", "视频号"],
    "政策/园区": ["政策", "科技局", "算力补贴", "园区", "小镇", "产业基地", "扶持资金", "行动计划"],
    "企业服务": ["获客", "geo", "dso", "企服", "企业服务", "b2b", "私域", "销售赋能"],
    "AI": ["ai", "大模型", "人工智能", "算力", "llm", "gpt", "deepseek", "机器学习", "深度学习"]
}

def classify_event(title: str, description: str = "") -> Tuple[str, List[str]]:
    """
    确定 primary_category 和 tags 列表。
    """
    text = f"{title} {description}".lower()
    matched_tags = []

    # 优先匹配强特征类别
    primary = "AI"
    priority_order = ["OPC", "FDE", "Agent", "具身智能", "出海", "投融资", "创业", "政策/园区", "开发者", "内容", "电商", "企业服务", "AI"]

    for cat in priority_order:
        keywords = CATEGORY_RULES[cat]
        for kw in keywords:
            if kw in text:
                matched_tags.append(cat if cat not in ["AI", "其他"] else kw.upper())
                if primary == "AI" and cat != "AI":
                    primary = cat

    # 去重 tags 并限制长度
    unique_tags = list(dict.fromkeys(matched_tags))
    if not unique_tags:
        unique_tags = ["AI", "技术交流"]

    return primary, unique_tags[:5]
