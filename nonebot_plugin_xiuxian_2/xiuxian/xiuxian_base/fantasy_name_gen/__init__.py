import os
from .xiuxian_names_generator import (
    XiuXianNameGenerator, 
    RARITY_NAMES, 
    CREATURE_CATEGORY_NAMES, 
    SEX_VALUES, 
    RARITY_LEVELS, 
    RARITY_VALUES, ZONE_CATEGORIES)

_generator = None

def get_generator():
    """获取或初始化名称生成器实例"""
    global _generator
    if _generator is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, "data")

        if os.path.exists(data_path):
            _generator = XiuXianNameGenerator(data_dir=data_path)
            print(f"成功加载修仙名称生成器数据: {data_path}")
    
    return _generator

def generate_name(is_female=None) -> str:
    """生成随机人名，返回单个字符串"""
    try:
        generator = get_generator()
        options = {}
        if is_female is not None:
            options["isFemale"] = is_female
        names = generator.get_name(1, options)
        if names and len(names) > 0:
            return names[0]
    except Exception as e:
        print(f"生成人名时出错: {e}")
    return "无名之人"