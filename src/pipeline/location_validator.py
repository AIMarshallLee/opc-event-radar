import re
from typing import Tuple, Optional

# 杭州 13 区县
DISTRICTS = [
    "余杭", "滨江", "西湖", "上城", "拱墅", "萧山",
    "临平", "钱塘", "富阳", "临安", "桐庐", "建德", "淳安"
]

# 标志性商圈与园区映射表
LANDMARK_MAP = {
    "未来科技城": "余杭",
    "人工智能小镇": "余杭",
    "梦想小镇": "余杭",
    "海创园": "余杭",
    "仓前": "余杭",
    "良渚": "余杭",
    "阿里滨江": "滨江",
    "白马湖": "滨江",
    "长河": "滨江",
    "浦沿": "滨江",
    "云栖小镇": "西湖",
    "紫金港": "西湖",
    "西溪": "西湖",
    "黄龙": "西湖",
    "丁兰智慧小镇": "上城",
    "钱江新城": "上城",
    "望江": "上城",
    "杭州湾智慧谷": "萧山",
    "奥体": "萧山",
    "钱江世纪城": "萧山",
    "下沙": "钱塘",
    "大江东": "钱塘",
    "临平新城": "临平",
    "艺尚小镇": "临平"
}

def validate_hangzhou_location(title: str, raw_location: str, raw_text: str = "") -> Tuple[bool, str, str]:
    """
    判断活动是否属于杭州，并提取所在具体区县。
    返回: (is_valid_hangzhou, district, venue)
    """
    text_corpus = f"{title} {raw_location} {raw_text}".lower()

    # 1. 明确的非杭州城市排除
    non_hz_cities = ["上海", "北京", "深圳", "广州", "成都", "武汉", "南京", "苏州", "西安", "合肥"]
    for c in non_hz_cities:
        # 如果出现其他城市，但同时没有明确杭州标识，判定为非杭州
        if c in text_corpus and "杭州" not in text_corpus:
            return False, "非杭州", raw_location

    # 2. 线上活动判断
    if any(k in text_corpus for k in ["线上", "直播", "online", "腾讯会议", "飞书会议", "zoom"]):
        # 若是线上且与 OPC/AI 强相关
        if any(k in text_corpus for k in ["opc", "一人公司", "杭州", "开发者", "智能体", "agent"]):
            return True, "线上", raw_location or "线上会议"

    # 3. 杭州区县直接匹配
    for d in DISTRICTS:
        if d in text_corpus:
            return True, d, raw_location

    # 4. 园区地标映射
    for landmark, dist in LANDMARK_MAP.items():
        if landmark.lower() in text_corpus:
            return True, dist, raw_location

    # 5. 兜底判定：只要包含“杭州”或数据源本身就是杭州站
    if "杭州" in text_corpus or "浙江" in text_corpus:
        return True, "杭州市区", raw_location

    return False, "未知地域", raw_location
