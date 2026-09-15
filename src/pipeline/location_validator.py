import re
from typing import Tuple

# 四大核心城市与其区县定义
CITY_DISTRICTS = {
    "杭州": [
        "余杭", "滨江", "西湖", "上城", "拱墅", "萧山",
        "临平", "钱塘", "富阳", "临安", "桐庐", "建德", "淳安"
    ],
    "上海": [
        "浦东", "徐汇", "闵行", "杨浦", "黄浦", "静安",
        "长宁", "普陀", "虹口", "宝山", "嘉定", "松江", "青浦", "奉贤", "金山", "崇明"
    ],
    "深圳": [
        "南山", "福田", "宝安", "龙岗", "龙华", "罗湖", "光明", "坪山", "盐田", "大鹏"
    ],
    "厦门": [
        "思明", "湖里", "集美", "海沧", "同安", "翔安"
    ]
}

# 标志性商圈与园区地标映射表 -> (城市, 区县)
LANDMARK_CITY_MAP = {
    # 杭州
    "未来科技城": ("杭州", "余杭"),
    "人工智能小镇": ("杭州", "余杭"),
    "梦想小镇": ("杭州", "余杭"),
    "海创园": ("杭州", "余杭"),
    "仓前": ("杭州", "余杭"),
    "良渚": ("杭州", "余杭"),
    "阿里西溪": ("杭州", "余杭"),
    "阿里滨江": ("杭州", "滨江"),
    "白马湖": ("杭州", "滨江"),
    "长河": ("杭州", "滨江"),
    "浦沿": ("杭州", "滨江"),
    "云栖小镇": ("杭州", "西湖"),
    "紫金港": ("杭州", "西湖"),
    "西溪": ("杭州", "西湖"),
    "黄龙": ("杭州", "西湖"),
    "蚂蚁z空间": ("杭州", "西湖"),
    "钱江新城": ("杭州", "上城"),
    "奥体": ("杭州", "萧山"),
    "钱江世纪城": ("杭州", "萧山"),
    "下沙": ("杭州", "钱塘"),

    # 上海
    "模速空间": ("上海", "徐汇"),
    "西岸智塔": ("上海", "徐汇"),
    "徐汇西岸": ("上海", "徐汇"),
    "张江高科": ("上海", "浦东"),
    "张江人工智能岛": ("上海", "浦东"),
    "陆家嘴": ("上海", "浦东"),
    "临港": ("上海", "浦东"),
    "创智天地": ("上海", "杨浦"),
    "五角场": ("上海", "杨浦"),
    "漕河泾": ("上海", "徐汇"),
    "静安寺": ("上海", "静安"),
    "虹桥": ("上海", "闵行"),

    # 深圳
    "南山科技园": ("深圳", "南山"),
    "粤海街道": ("深圳", "南山"),
    "深圳湾科技生态园": ("深圳", "南山"),
    "大族激光科技中心": ("深圳", "南山"),
    "科兴科学园": ("深圳", "南山"),
    "前海": ("深圳", "南山"),
    "华强北": ("深圳", "福田"),
    "车公庙": ("深圳", "福田"),
    "市民中心": ("深圳", "福田"),
    "坂田": ("深圳", "龙岗"),
    "天安云谷": ("深圳", "龙岗"),

    # 厦门
    "软件园二期": ("厦门", "思明"),
    "软件园三期": ("厦门", "集美"),
    "观音山": ("厦门", "思明"),
    "两岸金融中心": ("厦门", "思明"),
    "集美新城": ("厦门", "集美"),
    "湖里高新技术园": ("厦门", "湖里"),
    "海沧保税港区": ("厦门", "海沧")
}

def resolve_event_location(title: str, raw_location: str, raw_text: str = "") -> Tuple[bool, str, str, str]:
    """
    智能解析活动归属城市、区县与具体场地。
    支持：杭州、上海、深圳、厦门及线上。
    返回: (is_valid, city, district, venue)
    """
    text = f"{title} {raw_location} {raw_text}".lower()

    # 1. 线上活动判断 (线上活动默认归类，全城共享)
    if any(k in text for k in ["线上", "直播", "online", "腾讯会议", "飞书会议", "zoom", "视频号直播"]):
        if any(k in text for k in ["opc", "一人公司", "开发者", "智能体", "agent", "fde", "ai", "黑客松", "创业"]):
            return True, "线上", "线上", raw_location or "线上会议"

    # 2. 地标/园区强匹配
    for landmark, (city, dist) in LANDMARK_CITY_MAP.items():
        if landmark.lower() in text:
            return True, city, dist, raw_location or landmark

    # 3. 明确城市关键词直接判断
    cities_priority = ["深圳", "上海", "厦门", "杭州"]
    for c in cities_priority:
        if c in text:
            # 尝试在对应城市中查找区县
            districts = CITY_DISTRICTS.get(c, [])
            for d in districts:
                if d in text:
                    return True, c, d, raw_location
            return True, c, f"{c}市区", raw_location

    # 4. 单独匹配区县名（防止漏写城市名）
    for city, districts in CITY_DISTRICTS.items():
        for d in districts:
            if f"{d}区" in text or f"在{d}" in text:
                return True, city, d, raw_location

    # 5. 非重点城市（如明确写了北京、广州、成都、武汉等，且不含支持城市，则标记为其它）
    other_cities = ["北京", "广州", "成都", "武汉", "南京", "苏州", "西安", "重庆", "合肥", "长沙"]
    for oc in other_cities:
        if oc in text:
            return False, "其它", "其它", raw_location

    # 兜底：若数据源未明确写明，默认视为杭州（保持向下兼容）
    return True, "杭州", "杭州市区", raw_location

def validate_hangzhou_location(title: str, raw_location: str, raw_text: str = "") -> Tuple[bool, str, str]:
    """向后兼容原有单城校验接口"""
    is_valid, city, district, venue = resolve_event_location(title, raw_location, raw_text)
    if is_valid and city in ["杭州", "线上"]:
        return True, district, venue
    return False, "非杭州", venue
