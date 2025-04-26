from xiuxian_names_generator import XiuXianNameGenerator, RARITY_NAMES, CREATURE_CATEGORY_NAMES

def main():
    generator = XiuXianNameGenerator(data_dir="/home/rikka/xiuxian/data/xiuxian/修仙随机名词数据")
    
    print("========== 修仙名称生成示例 ==========")
    
    # 生成人名
    names = generator.get_name(5)
    print("\n【随机人名】")
    for name in names:
        print(name)
    
    # 生成女性人名
    female_names = generator.get_name(3, {"isFemale": True})
    print("\n【女性人名】")
    for name in female_names:
        print(name)
    
    # 生成男性人名
    male_names = generator.get_name(3, {"isFemale": False})
    print("\n【男性人名】")
    for name in male_names:
        print(name)
    
    # 生成道号
    print("\n【道号】")
    dao_names = generator.get_dao(5)
    for dao in dao_names:
        print(f"{dao['name']}")
    
    # 获取所有道号称号
    print("\n【可用道号称号数量】")
    print(f"共 {len(generator.dao_titles)} 个")
    
    # 生成技能
    print("\n【功法】")
    skills = generator.get_skill(5)
    for skill in skills:
        print(f"{skill['name']} ({RARITY_NAMES[skill['rarity']]})")
    
    # 生成书籍
    print("\n【秘籍】")
    books = generator.get_book(5)
    for book in books:
        print(f"{book['name']} ({RARITY_NAMES[book['rarity']]})")
    
    # 获取秘籍前缀
    print("\n【可用秘籍前缀数量】")
    print(f"共 {len(generator.book_prefixes)} 个")
    
    # 生成生灵
    print("\n【生灵】")
    creatures = generator.get_creature(5)
    for creature in creatures:
        category_name = CREATURE_CATEGORY_NAMES.get(creature['category'], creature['category'])
        print(f"{creature['name']} - {category_name}")
    
    # 生成特定种类的生灵
    print("\n【鸟类生灵】")
    birds = generator.get_creature(3, {"category": "bird"})
    for bird in birds:
        print(f"{bird['name']} ({RARITY_NAMES[bird['rarity']]})")
    
    # 生成材料
    print("\n【材料】")
    materials = generator.get_material(5)
    for material in materials:
        print(f"{material['name']} ({RARITY_NAMES[material['rarity']]})")
    
    # 生成法宝
    print("\n【法宝】")
    talismans = generator.get_talisman(5)
    for talisman in talismans:
        print(f"{talisman['name']} ({RARITY_NAMES[talisman['rarity']]})")
    
    # 生成丹药
    print("\n【丹药】")
    alchemies = generator.get_alchemy(5)
    for alchemy in alchemies:
        print(f"{alchemy['name']} ({RARITY_NAMES[alchemy['rarity']]})")
    
    # 生成门派
    print("\n【门派】")
    clans = generator.get_clan(5)
    for clan in clans:
        print(clan)
    
    # 生成国家
    print("\n【国家】")
    nations = generator.get_nation(5)
    for nation in nations:
        print(f"{nation['name']}")
    
    # 生成据点
    print("\n【据点】")
    locations = generator.get_location(5)
    for location in locations:
        print(f"{location['name']}")
    
    # 生成地域 - 使用options方式
    print("\n【地域 (使用options)】")
    zones = generator.get_zone(3, {"category": "land"})
    for zone in zones:
        print(f"{zone['name']}")
    
    # 生成地域 - 使用直接传递kind方式
    print("\n【地域 (使用kind字符串)】")
    zones = generator.get_zone(2, "山脉")
    for zone in zones:
        print(f"{zone['name']}")

if __name__ == "__main__":
    main() 