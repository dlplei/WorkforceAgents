"""
企业差旅与费控政策矩阵配置
将原本硬编码在业务工具层的城市等级、住宿标准、餐补标准外部化管理
"""
from typing import Dict, List, Tuple
from models import CityTier

# 一线城市列表
TIER_1_CITIES: List[str] = ["北京", "上海", "广州", "深圳"]

# 二线城市列表
TIER_2_CITIES: List[str] = [
    "杭州", "成都", "武汉", "南京", "西安", "重庆", "苏州",
    "天津", "长沙", "郑州", "东莞", "青岛", "合肥", "佛山", "宁波",
]

# 住宿标准（元/天）：城市等级 -> 员工职级 -> 报销上限
ACCOMMODATION_STANDARDS: Dict[str, Dict[str, int]] = {
    CityTier.TIER1.value: {"P5": 400, "P6": 600, "P7": 600, "P8": 1000, "M1": 800, "M2": 1200},
    CityTier.TIER2.value: {"P5": 300, "P6": 500, "P7": 500, "P8": 800, "M1": 600, "M2": 1000},
    CityTier.TIER3.value: {"P5": 250, "P6": 400, "P7": 400, "P8": 600, "M1": 500, "M2": 800},
}

# 餐饮与杂费补贴标准（元/天）：城市等级 -> 补贴基数
MEAL_STANDARDS: Dict[str, int] = {
    CityTier.TIER1.value: 100,
    CityTier.TIER2.value: 80,
    CityTier.TIER3.value: 60,
}

# 默认住宿标准兜底
DEFAULT_ACCOMMODATION_RATE: int = 400
DEFAULT_MEAL_RATE: int = 80


def infer_city_tier(city: str) -> str:
    """根据城市名自动判定城市等级（一线/二线/三线及以下）"""
    city_str = str(city or "").strip()
    for c in TIER_1_CITIES:
        if c in city_str:
            return CityTier.TIER1.value
    for c in TIER_2_CITIES:
        if c in city_str:
            return CityTier.TIER2.value
    return CityTier.TIER3.value


def get_travel_rates(tier: str, level: str) -> Tuple[int, int]:
    """获取指定城市等级与职级的 (住宿上限, 餐补标准)"""
    norm_tier = tier if tier in ACCOMMODATION_STANDARDS else infer_city_tier(tier)
    tier_standards = ACCOMMODATION_STANDARDS.get(norm_tier, {})
    acc_rate = tier_standards.get(level, DEFAULT_ACCOMMODATION_RATE)
    meal_rate = MEAL_STANDARDS.get(norm_tier, DEFAULT_MEAL_RATE)
    return acc_rate, meal_rate
