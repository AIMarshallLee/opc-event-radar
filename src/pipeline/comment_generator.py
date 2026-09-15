import os
import json
import urllib.request
import ssl
from typing import Dict, Any

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

def generate_ai_comment(
    title: str,
    description: str,
    organizer: str,
    category: str,
    overall_score: int
) -> Dict[str, str]:
    """
    生成高信息密度 AI 评语：
    - recommendation_reason (为什么值得去)
    - suitable_for (适合谁)
    - not_suitable_for (不适合谁)
    """
    # 1. 如果有 DeepSeek API Key，调用大模型生成个性化硬核评语
    if DEEPSEEK_API_KEY:
        try:
            prompt = f"""你是一位深耕杭州人工智能与一人公司(OPC)领域的毒舌资深投资人兼全栈架构师。
请针对以下杭州活动给出极简、高信息密度、直击本质的评价（严禁复述官方客套文案）：
活动名称：{title}
主办方：{organizer}
活动类型：{category}
描述详情：{description[:300]}
综合评分：{overall_score}/100

请严格按以下 JSON 格式返回，不得有其他文字：
{{
  "recommendation_reason": "一句话讲透为什么值得去（聚焦落地场景、真实人脉、技术干货或商业变现）",
  "suitable_for": "明确适合什么具体角色（如：一人公司OPC创始人、AI出海操盘手、全栈开发者）",
  "not_suitable_for": "明确劝退哪些人不适合去（如：泛泛科普围观者、无实际业务场景的纯理论派）"
}}"""

            req_data = json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你只输出合法的 JSON 格式。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }).encode('utf-8')

            req = urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=req_data,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=3.5, context=ctx) as resp:
                resp_json = json.loads(resp.read().decode('utf-8'))

                content = resp_json['choices'][0]['message']['content']
                parsed = json.loads(content)
                if "recommendation_reason" in parsed:
                    return parsed
        except Exception as e:
            # 降级到本地规则生成
            pass

    # 2. 本地高密度专业规则模板（兜底自洽）
    reason = f"聚焦{category}领域的杭州本土实操落地，适合拓展同城生态人脉与业务协同。"
    suitable = "AI产品经理、OPC独立创业者、技术团队负责人"
    not_suitable = "无明确业务落地诉求、仅寻求基础概念科普的人群"

    if category == "OPC":
        reason = "杭州一人公司(OPC)生态关键触点，直击超级个体单人变现与无代码/低代码实战路径。"
        suitable = "独立开发者、超级个体创业者、自由职业者、小微工作室负责人"
        not_suitable = "依赖大兵团作战流程、缺乏全栈业务操盘意愿的传统岗位"
    elif category == "FDE":
        reason = "核心聚焦企业级 AI 落地场景共创，能够直接对接杭州大厂与行业生态真实需求。"
        suitable = "企业解决方案架构师、FDE工程师、B端产品负责人"
        not_suitable = "纯学术研究、不关注工程交付与商业落地的理论学者"
    elif category == "出海":
        reason = "直面杭州跨境与出海前沿供应链，拆解 AI 赋能外贸获客与全球化增长的具体打法。"
        suitable = "外贸老板、跨境电商操盘手、海外业务拓展负责人"
        not_suitable = "纯国内内卷赛道且无意拓展海外市场的传统商家"
    elif category == "开发者":
        reason = "硬核技术交流，深入模型部署、框架选型与实战代码调优，杜绝假大空套话。"
        suitable = "全栈工程师、算法工程师、开源贡献者、架构师"
        not_suitable = "非技术岗人员、无法理解基础代码与系统架构的运营人员"
    elif category == "投融资":
        reason = "杭州本地创投直面对接，检验商业模式成色并接触一线一线机构投资人。"
        suitable = "正在寻求融资的 AI/OPC 创始人、合伙人、早期项目团队"
        not_suitable = "无成型商业计划书、早期纯概念探讨的项目"

    return {
        "recommendation_reason": reason,
        "suitable_for": suitable,
        "not_suitable_for": not_suitable
    }
