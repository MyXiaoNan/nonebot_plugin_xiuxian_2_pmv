import json
import random
import os
from typing import Dict, List, Optional, Union, Any
# 常量定义
SEX_VALUES = [
    {"text": "随机", "value": None},
    {"text": "女", "value": True},
    {"text": "男", "value": False}
]

RARITY_COLORS = {
    "common": "#CCCCCC",
    "uncommon": "#222A35",
    "rare": "#00A6A9",
    "epic": "#804DC8",
    "legendary": "#C5C660",
    "mythic": "#F28234",
    "exotic": "#C65043",
}

RARITY_LEVELS = [
    "common",
    "uncommon",
    "rare",
    "epic", 
    "legendary",
    "mythic",
    "exotic",
]

RARITY_VALUES = {
    "common": 1.0,     # 灰
    "uncommon": 0.35,  # 白
    "rare": 0.15,      # 蓝
    "epic": 0.075,     # 紫
    "legendary": 0.03, # 橙
    "mythic": 0.012,   # 金
    "exotic": 0.005,   # 虹
}

RARITY_NAMES = {
    "common": "凡品",
    "uncommon": "良品",
    "rare": "上品",
    "epic": "极品", 
    "legendary": "秘宝",
    "mythic": "灵宝",
    "exotic": "古宝",
}

CREATURE_CATEGORY = ["plant", "worm", "fish", "beast", "bird", "reptile", "insect"]

CREATURE_CATEGORY_NAMES = {
    "plant": "草木",
    "worm": "赢虫",
    "fish": "鱼",
    "beast": "兽",
    "bird": "鸟",
    "reptile": "爬虫",
    "insect": "甲虫",
}

ZONE_CATEGORIES = ["land", "water", "void"]

# 特殊符号常量
_PARENTHESIS_LEFT = "（"
_PARENTHESIS_RIGHT = "）"
_BOOK_LEFT = "《"
_BOOK_RIGHT = "》"
_LINK_WORD = "之"
_NUMBER_BEGIN_SUPPLEMENT = "路"
_NUMBER_END_SUPPLEMENT = "式"
_COUNTRY = "国"
_AGE1 = "百年"
_AGE10 = "千年"
_AGE100 = "万年"

class XiuXianNameGenerator:
    def __init__(self, data_dir: str = ""):
        """初始化修仙名称生成器
        
        Args:
            data_dir: 数据文件目录路径
        """
        self.data_dir = data_dir
        self.data = self._load_data()
        self._validate_data()
        
    def _load_data(self) -> Dict[str, Any]:
        """加载所有JSON数据文件"""
        data = {}
        
        # 加载共享数据
        data["common"] = self._load_json_file("shared/common.json")
        data["strange"] = self._load_json_file("shared/strange.json")
        data["color"] = self._load_json_file("shared/color.json")
        data["spirit"] = self._load_json_file("shared/spirit.json")
        
        # 加载人名数据
        data["family"] = self._load_json_file("name/family.json")
        data["female"] = self._load_json_file("name/female.json")
        data["male"] = self._load_json_file("name/male.json")
        data["middle"] = self._load_json_file("name/middle.json")
        
        # 加载道号数据
        data["dao"] = self._load_json_file("dao/dao.json")
        data["dao_title_male"] = self._load_json_file("dao/title_male.json")
        data["dao_title_female"] = self._load_json_file("dao/title_female.json")
        
        # 加载技能数据
        data["skill"] = self._load_json_file("skill/skill.json")
        data["skill_prefix"] = self._load_json_file("skill/prefix.json")
        data["skill_numfix"] = self._load_json_file("skill/numfix.json")
        
        # 加载书籍数据
        data["book"] = self._load_json_file("book/book.json")
        data["book_prefix"] = self._load_json_file("book/prefix.json")
        data["book_postfix"] = self._load_json_file("book/postfix.json")
        
        # 加载符箓数据
        data["talisman"] = self._load_json_file("talisman/talisman.json")
        data["talisman_material"] = self._load_json_file("talisman/material.json")
        data["talisman_postfix"] = self._load_json_file("talisman/postfix.json")
        
        # 加载组织数据
        data["clan"] = self._load_json_file("organization/clan.json")
        data["nation"] = self._load_json_file("organization/nation.json")
        
        # 加载地点数据
        data["place"] = self._load_json_file("place/place.json")
        data["place_prefix"] = self._load_json_file("place/prefix.json")
        data["place_postfix"] = self._load_json_file("place/postfix.json")
        data["location"] = self._load_json_file("place/location.json")
        data["zone"] = self._load_json_file("place/zone.json")
        
        # 加载材料数据
        data["material"] = self._load_json_file("material/material.json")
        data["material_postfix"] = self._load_json_file("material/postfix.json")
        
        # 加载生物数据
        data["creature"] = self._load_json_file("creature/creature.json")
        data["creature_prefix"] = self._load_json_file("creature/prefix.json")
        data["strange_creature"] = self._load_json_file("creature/strange.json")
        
        # 加载丹药数据
        data["alchemy"] = self._load_json_file("alchemy/alchemy.json")
        
        return data
    
    def _load_json_file(self, file_path: str) -> Any:
        """加载单个JSON文件
        
        Args:
            file_path: 相对于data_dir的文件路径
        
        Returns:
            加载的JSON数据
        """
        full_path = os.path.join(self.data_dir, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"无法加载 {full_path}: {e}")
            return {} if file_path.endswith(".json") else []
    
    def _validate_data(self):
        """验证加载的数据是否完整有效"""
        required_data = [
            "common", "strange", "color", "spirit", 
            "family", "female", "male", "middle",
            "dao", "dao_title_male", "dao_title_female",
            "skill", "skill_prefix", "skill_numfix",
            "book", "book_prefix", "book_postfix",
            "talisman", "talisman_material", "talisman_postfix",
            "clan", "nation",
            "place", "place_prefix", "place_postfix", "location", "zone",
            "material", "material_postfix",
            "creature", "creature_prefix", "strange_creature",
            "alchemy"
        ]
        missing = []
        for item in required_data:
            if not self.data.get(item):
                missing.append(item)
        
        if missing:
            print(f"警告: 以下数据不完整或缺失: {', '.join(missing)}")
    
    @property
    def dao_titles(self) -> List[str]:
        """获取所有道号称号列表"""
        titles = []
        for gender in ["dao_title_male", "dao_title_female"]:
            for rarity in RARITY_LEVELS:
                if gender in self.data and rarity in self.data[gender]:
                    titles.extend(self.data[gender][rarity])
        return list(set(titles))  # 去重
    
    @property
    def book_prefixes(self) -> List[str]:
        """获取所有书籍前缀列表"""
        prefixes = []
        for rarity in ["epic", "legendary", "mythic", "exotic"]:
            if "book_prefix" in self.data and rarity in self.data["book_prefix"]:
                prefixes.extend(self.data["book_prefix"][rarity])
        return prefixes
    
    @property
    def talisman_kind(self) -> List[str]:
        """获取所有符箓类型列表"""
        kinds = []
        for rarity in RARITY_LEVELS:
            if "talisman" in self.data and rarity in self.data["talisman"]:
                kinds.extend(self.data["talisman"][rarity])
        return kinds
    
    @property
    def material_kind(self) -> List[str]:
        """获取所有材料类型列表"""
        kinds = []
        for rarity in RARITY_LEVELS:
            if "material" in self.data and rarity in self.data["material"]:
                kinds.extend(self.data["material"][rarity])
        return kinds
    
    @property
    def material_postfixes(self) -> List[str]:
        """获取所有材料后缀列表"""
        postfixes = []
        for kind in ["broken", "handmade"]:
            if "material_postfix" in self.data and kind in self.data["material_postfix"]:
                postfixes.extend(self.data["material_postfix"][kind])
        return postfixes
    
    @property
    def talisman_postfixes(self) -> List[str]:
        """获取所有符箓后缀列表"""
        postfixes = []
        for kind in ["broken", "handmade"]:
            if "talisman_postfix" in self.data and kind in self.data["talisman_postfix"]:
                postfixes.extend(self.data["talisman_postfix"][kind])
        return postfixes
    
    @property
    def zone_kind(self) -> List[str]:
        """获取所有区域类型列表"""
        kinds = []
        for category in ZONE_CATEGORIES:
            if "zone" in self.data and category in self.data["zone"]:
                kinds.extend(self.data["zone"][category])
        return kinds
    
    @property
    def book_postfixes(self) -> List[str]:
        """获取所有书籍后缀列表"""
        postfixes = []
        for rarity in ["uncommon", "rare"]:
            if "book_postfix" in self.data and rarity in self.data["book_postfix"]:
                postfixes.extend(self.data["book_postfix"][rarity])
        return postfixes
    
    def _get_rarity(self, max_value: float = 1.0) -> Dict[str, str]:
        """获取随机稀有度
        
        Args:
            max_value: 随机值上限
            
        Returns:
            包含稀有度和随机值的字典
        """
        value = random.random() * (max_value or 1.0)
        if value < RARITY_VALUES["exotic"]:
            rarity = "exotic"
        elif value < RARITY_VALUES["mythic"]:
            rarity = "mythic"
        elif value < RARITY_VALUES["legendary"]:
            rarity = "legendary"
        elif value < RARITY_VALUES["epic"]:
            rarity = "epic"
        elif value < RARITY_VALUES["rare"]:
            rarity = "rare"
        elif value < RARITY_VALUES["uncommon"]:
            rarity = "uncommon"
        else:
            rarity = "common"
        return {"rarity": rarity, "value": value}
    
    def get_name(self, number: int = 1, options: Dict = None) -> List[str]:
        """生成人名
        
        Args:
            number: 生成名字的数量
            options: 选项参数，可包含:
                    familyName: 指定姓氏
                    isFemale: 是否女性
                    style: 命名风格('single', 'double', 'combine')
                    middleCharacter: 中间字符
        
        Returns:
            生成的名字列表
        """
        options = options or {}
        names = []
        
        for _ in range(number):
            if options.get("familyName"):
                the_family_name = options["familyName"]
            else:
                family_index = random.randint(0, len(self.data["family"]) - 1)
                the_family_name = self.data["family"][family_index]
            
            is_female = options.get("isFemale", random.randint(0, 1) == 0)
            names_of_a_sex = self.data["female"] if is_female else self.data["male"]
            
            r = random.random()
            style = options.get("style")
            if not style:
                if r < 0.33333333:
                    style = "single"
                elif r < 0.66666666:
                    style = "double"
                else:
                    style = "combine"
            
            name = ""
            if style == "single":
                if options.get("middleCharacter"):
                    name = options["middleCharacter"]
                else:
                    name_index = random.randint(0, len(names_of_a_sex) - 1)
                    name = names_of_a_sex[name_index]
            elif style == "double":
                if options.get("middleCharacter"):
                    the_middle_character = options["middleCharacter"]
                else:
                    name_index = random.randint(0, len(names_of_a_sex) - 1)
                    the_middle_character = names_of_a_sex[name_index]
                
                name_index = random.randint(0, len(names_of_a_sex) - 1)
                the_last_character = names_of_a_sex[name_index]
                name = the_middle_character + the_last_character
            else:
                if options.get("middleCharacter"):
                    the_middle_character = options["middleCharacter"]
                else:
                    name_index = random.randint(0, len(self.data["middle"]) - 1)
                    the_middle_character = self.data["middle"][name_index]
                
                name_index = random.randint(0, len(names_of_a_sex) - 1)
                the_last_character = names_of_a_sex[name_index]
                name = the_middle_character + the_last_character
            
            names.append(the_family_name + name)
        
        return names
    
    def get_dao(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成道号
        
        Args:
            number: 生成道号的数量
            options: 选项参数，可包含:
                    firstCharacter: 第一个字符
                    isFemale: 是否女性
                    title: 称号
        
        Returns:
            生成的道号列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        
        for _ in range(number):
            if options.get("firstCharacter"):
                the_first_character = options["firstCharacter"]
            else:
                name_index1 = random.randint(0, len(self.data["dao"]) - 1)
                the_first_character = self.data["dao"][name_index1]
            
            name_index2 = random.randint(0, len(self.data["dao"]) - 1)
            name = the_first_character + self.data["dao"][name_index2]
            
            is_female = options.get("isFemale", random.randint(0, 1) == 0)
            title_group = self.data["dao_title_female"] if is_female else self.data["dao_title_male"]
            
            t = options.get("title", "")
            rarity = "common"
            
            if not t:
                rarity_info = self._get_rarity()
                rarity = rarity_info["rarity"]
                
                if rarity == "exotic" and title_group.get("exotic"):
                    t = random.choice(title_group["exotic"])
                elif rarity == "mythic" and title_group.get("mythic"):
                    t = random.choice(title_group["mythic"])
                elif rarity == "legendary" and title_group.get("legendary"):
                    t = random.choice(title_group["legendary"])
                elif rarity == "epic" and title_group.get("epic"):
                    t = random.choice(title_group["epic"])
                elif rarity == "rare" and title_group.get("rare"):
                    t = random.choice(title_group["rare"])
                elif rarity == "uncommon" and title_group.get("uncommon"):
                    t = random.choice(title_group["uncommon"])
            else:
                if t in (title_group.get("exotic", []) + self.data["dao_title_male"].get("exotic", [])):
                    rarity = "exotic"
                elif t in (title_group.get("mythic", []) + self.data["dao_title_male"].get("mythic", [])):
                    rarity = "mythic"
                elif t in (title_group.get("legendary", []) + self.data["dao_title_male"].get("legendary", [])):
                    rarity = "legendary"
                elif t in (title_group.get("epic", []) + self.data["dao_title_male"].get("epic", [])):
                    rarity = "epic"
                elif t in (title_group.get("rare", []) + self.data["dao_title_male"].get("rare", [])):
                    rarity = "rare"
                elif t in (title_group.get("uncommon", []) + self.data["dao_title_male"].get("uncommon", [])):
                    rarity = "uncommon"
            
            names.append({"name": name + t, "rarity": rarity})
        
        return names
    
    def _get_skill_name(self, length: Optional[int] = None, kind: Optional[str] = None, 
                       prefix: Optional[str] = None, numfix: Optional[str] = None) -> Dict:
        """生成单个技能名称
        
        Args:
            length: 名称长度
            kind: 技能类型
            prefix: 前缀
            numfix: 数字后缀
            
        Returns:
            包含name和rarity的字典
        """
        l = length or 1
        rarity = "common"
        
        if not length:
            r = self._get_rarity()
            if r["value"] < RARITY_VALUES["rare"]:
                l = 3
            elif r["value"] < RARITY_VALUES["uncommon"]:
                l = 2
            rarity = r["rarity"]
        else:
            if length > 2:
                rarity = "rare"
            elif length > 1:
                rarity = "uncommon"

        common = []
        for category in ["dao", "element", "creature", "thing", "color", "place", 
                         "adj", "number", "gesture", "action"]:
            if category in self.data.get("common", {}):
                common.extend(self.data["common"][category])
        
        name = ""
        for _ in range(l):
            name += random.choice(common)
        
        pre = prefix or ""
        if not pre and random.random() < RARITY_VALUES["epic"]:
            pre = random.choice(self.data["skill_prefix"])
        
        n = numfix or ""
        if not n and random.random() < RARITY_VALUES["epic"]:
            n = random.choice(self.data["skill_numfix"])
        
        k = kind or random.choice(self.data["skill"])
        
        if random.random() < 0.5:
            name = (n + _NUMBER_BEGIN_SUPPLEMENT if n else "") + pre + name + k
        else:
            if len(k) > 1:
                name = pre + name + k + (n + _NUMBER_END_SUPPLEMENT if n else "")
            else:
                name = pre + name + n + k
        
        return {"name": name, "rarity": rarity}
    
    def get_skill(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成功法名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    length: 技能名称长度
                    kind: 技能类型
                    prefix: 前缀
                    numfix: 数字后缀
        
        Returns:
            生成的功法名称列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        
        for _ in range(number):
            name = self._get_skill_name(
                options.get("length"),
                options.get("kind"),
                options.get("prefix"),
                options.get("numfix")
            )
            names.append(name)
        
        return names
    
    def get_book(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成秘籍名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    length: 书名长度
                    mainkind: 主要类型
                    prefix: 前缀
                    postkind: 后缀类型
                    postfix: 后缀
        
        Returns:
            生成的秘籍名称列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        
        for _ in range(number):
            skillname = self._get_skill_name(options.get("length"), options.get("mainkind"))
            rarity = skillname["rarity"]
            
            pre = options.get("prefix", "")
            if not pre:
                if rarity == "exotic" and "exotic" in self.data["book_prefix"]:
                    pre = random.choice(self.data["book_prefix"]["exotic"])
                elif rarity == "mythic" and "mythic" in self.data["book_prefix"]:
                    pre = random.choice(self.data["book_prefix"]["mythic"])
                elif rarity == "legendary" and "legendary" in self.data["book_prefix"]:
                    pre = random.choice(self.data["book_prefix"]["legendary"])
                elif rarity == "epic" and "epic" in self.data["book_prefix"]:
                    pre = random.choice(self.data["book_prefix"]["epic"])
            
            pk = options.get("postkind", "")
            if pre and not pk:
                pk = random.choice(self.data["book"])
            
            post = options.get("postfix", "")
            if not post:
                r1 = random.random()
                r2 = random.random()
                if r1 < RARITY_VALUES["rare"] and r2 < RARITY_VALUES["rare"] and "rare" in self.data["book_postfix"]:
                    post = _PARENTHESIS_LEFT + random.choice(self.data["book_postfix"]["rare"]) + _PARENTHESIS_RIGHT
                elif r1 < RARITY_VALUES["uncommon"] and r2 < RARITY_VALUES["uncommon"] and "uncommon" in self.data["book_postfix"]:
                    post = _PARENTHESIS_LEFT + random.choice(self.data["book_postfix"]["uncommon"]) + _PARENTHESIS_RIGHT
            else:
                post = _PARENTHESIS_LEFT + post + _PARENTHESIS_RIGHT
            
            names.append({
                "name": _BOOK_LEFT + skillname["name"] + pre + pk + post + _BOOK_RIGHT,
                "rarity": rarity
            })
        
        return names
    
    def get_creature(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成生灵名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    category: 生物种类
                    rarity: 稀有度
        
        Returns:
            生成的生灵名称列表，每个元素包含name，rarity和category
        """
        options = options or {}
        names = []
        common_creature_names = []
        for category in ["dao", "element", "thing", "color", "number", "action"]:
            if category in self.data.get("common", {}):
                common_creature_names.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            pre = random.choice(common_creature_names)
            c = random.choice(self.data["color"])
            s = random.choice(self.data["creature_prefix"])
            
            cat = options.get("category")
            if not cat:
                cat = random.choice(CREATURE_CATEGORY)
            
            k = random.choice(self.data["creature"][cat])
            r = options.get("rarity") or self._get_rarity(RARITY_VALUES["uncommon"])["rarity"]
            
            if r == "exotic":
                name = random.choice(self.data["strange_creature"])
            elif r == "mythic":
                name = pre + c + s + k
            elif r == "legendary":
                name = pre + s + k
            elif r == "epic":
                name = pre + c + k
            elif r == "rare":
                name = pre + k
            elif r == "uncommon":
                name = c + s + k
            elif r == "common":
                name = c + k
            
            names.append({"name": name, "rarity": r, "category": cat})
        
        return names
    
    def get_material(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成材料名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    kind: 材料类型
                    rarity: 稀有度
                    postfix: 后缀
        
        Returns:
            生成的材料名称列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            age = ""
            pre = random.choice(common)
            c = random.choice(self.data["color"])
            s = random.choice(self.data["spirit"])
            
            k = options.get("kind")
            r = options.get("rarity") or self._get_rarity(RARITY_VALUES["uncommon"])["rarity"]
            
            if r == "exotic":
                all_materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in self.data["material"]:
                        all_materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(all_materials)
                age = _AGE100
                name = age + pre + c + s + k
            elif r == "mythic":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["mythic", "legendary", "epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                age = _AGE10
                name = age + pre + c + s + k
            elif r == "legendary":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["legendary", "epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                age = _AGE1
                name = age + pre + c + s + k
            elif r == "epic":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                name = pre + c + s + k
            elif r == "rare":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["rare", "uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                name = pre + s + k
            elif r == "uncommon":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                name = c + s + k
            elif r == "common":
                if "common" in self.data["material"]:
                    k = k or random.choice(self.data["material"]["common"])
                name = c + k
            
            post = options.get("postfix", "")
            if not post:
                r1 = random.random()
                r2 = random.random()
                if (r1 < RARITY_VALUES["rare"] and r2 < RARITY_VALUES["rare"] and 
                    "broken" in self.data["material_postfix"]):
                    post = (_PARENTHESIS_LEFT + 
                           random.choice(self.data["material_postfix"]["broken"]) + 
                           _PARENTHESIS_RIGHT)
                elif (r1 < RARITY_VALUES["uncommon"] and r2 < RARITY_VALUES["uncommon"] and 
                      "handmade" in self.data["material_postfix"]):
                    post = (_PARENTHESIS_LEFT + 
                           random.choice(self.data["material_postfix"]["handmade"]) + 
                           _PARENTHESIS_RIGHT)
            else:
                post = _PARENTHESIS_LEFT + post + _PARENTHESIS_RIGHT
            
            names.append({"name": name + post, "rarity": r})
        
        return names
    
    def get_talisman(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成法宝名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    kind: 符箓类型
                    rarity: 稀有度
                    postfix: 后缀
        
        Returns:
            生成的法宝名称列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            prefix = random.choice(common)
            c = random.choice(self.data["color"])
            m = random.choice(self.data["talisman_material"])
            s = random.choice(self.data["spirit"])
            
            k = options.get("kind")
            r = options.get("rarity") or self._get_rarity(RARITY_VALUES["uncommon"])["rarity"]
            
            if r == "exotic":
                all_talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in self.data["talisman"]:
                        all_talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(all_talismans)
                name = prefix + s + k
            elif r == "mythic":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["mythic", "legendary", "epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = prefix + s + k
            elif r == "legendary":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["legendary", "epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = prefix + c + m + k
            elif r == "epic":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = prefix + m + k
            elif r == "rare":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["rare", "uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = prefix + k
            elif r == "uncommon":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = c + m + k
            elif r == "common":
                if "common" in self.data["talisman"]:
                    k = k or random.choice(self.data["talisman"]["common"])
                name = m + k
            
            post = options.get("postfix", "")
            if not post:
                r1 = random.random()
                r2 = random.random()
                if (r1 < RARITY_VALUES["rare"] and r2 < RARITY_VALUES["rare"] and 
                    "broken" in self.data["talisman_postfix"]):
                    post = (_PARENTHESIS_LEFT + 
                           random.choice(self.data["talisman_postfix"]["broken"]) + 
                           _PARENTHESIS_RIGHT)
                elif (r1 < RARITY_VALUES["uncommon"] and r2 < RARITY_VALUES["uncommon"] and 
                      "handmade" in self.data["talisman_postfix"]):
                    post = (_PARENTHESIS_LEFT + 
                           random.choice(self.data["talisman_postfix"]["handmade"]) + 
                           _PARENTHESIS_RIGHT)
            else:
                post = _PARENTHESIS_LEFT + post + _PARENTHESIS_RIGHT
            
            names.append({"name": name + post, "rarity": r})
        
        return names
    
    def get_alchemy(self, number: int = 1, kind: Optional[str] = None) -> List[Dict]:
        """生成丹药名称
        
        Args:
            number: 生成名称的数量
            kind: 丹药类型
        
        Returns:
            生成的丹药名称列表，每个元素包含name和rarity
        """
        names = []
        common_alchemy_names = []
        for category in ["dao", "element", "color", "number", "action"]:
            if category in self.data.get("common", {}):
                common_alchemy_names.extend(self.data["common"][category])
        
        for _ in range(number):
            rarity = "common"
            pre = random.choice(common_alchemy_names)
            s = ""
            
            r = self._get_rarity()
            if r["value"] < RARITY_VALUES["rare"]:
                s = random.choice(self.data["spirit"])
            
            rarity = r["rarity"]
            k = kind or ""
            if not kind:
                k = random.choice(self.data["alchemy"])
            
            names.append({"name": pre + s + k, "rarity": rarity})
        
        return names
    
    def get_clan(self, number: int = 1, kind: Optional[str] = None) -> List[str]:
        """生成门派名称
        
        Args:
            number: 生成名称的数量
            kind: 门派类型
        
        Returns:
            生成的门派名称列表
        """
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = random.choice(common)
            k = kind
            if not k:
                k = random.choice(self.data["clan"])
            
            names.append(name + k)
        
        return names
    
    def get_nation(self, number: int = 1, kind: Optional[str] = None) -> List[Dict]:
        """生成国家名称
        
        Args:
            number: 生成名称的数量
            kind: 国家类型
        
        Returns:
            生成的国家名称列表，每个元素包含name和rarity
        """
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            k = kind or ""
            rarity = "common"
            
            r = random.random()
            if r < RARITY_VALUES["rare"]:
                name = random.choice(self.data["strange"])
                rarity = "rare"
                if not kind:
                    if len(name) == 1:
                        k = _COUNTRY
                    else:
                        k = random.choice(self.data["nation"])
            elif r < RARITY_VALUES["uncommon"]:
                name = random.choice(common)
                rarity = "uncommon"
                if not kind:
                    if len(name) == 1:
                        k = _COUNTRY
                    else:
                        k = random.choice(self.data["nation"])
            else:
                prefix = ""
                if random.random() < RARITY_VALUES["rare"]:
                    prefix = random.choice(self.data["place_prefix"])
                
                name = prefix + random.choice(self.data["place"])
                if not kind:
                    k = _COUNTRY
            
            names.append({"name": name + k, "rarity": rarity})
        
        return names
    
    def get_location(self, number: int = 1, kind: Optional[str] = None) -> List[Dict]:
        """生成据点名称
        
        Args:
            number: 生成名称的数量
            kind: 地点类型
        
        Returns:
            生成的据点名称列表，每个元素包含name和rarity
        """
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            k = kind or ""
            rarity = "common"
            
            r = random.random()
            if r < RARITY_VALUES["rare"]:
                name = random.choice(self.data["strange"])
                rarity = "rare"
            elif r < RARITY_VALUES["uncommon"]:
                name = random.choice(common)
                rarity = "uncommon"
            else:
                place_index = random.randint(0, len(self.data["place"]) - 1)
                postfix = ""
                if random.random() < RARITY_VALUES["uncommon"]:
                    postfix_index = random.randint(0, len(self.data["place_postfix"]) - 1)
                    postfix = self.data["place_postfix"][postfix_index]
                
                name = self.data["place"][place_index] + postfix
            
            if not kind:
                k = random.choice(self.data["location"])
            
            names.append({"name": name + k, "rarity": rarity})
        
        return names
    
    def _get_zone_kind(self, category: Optional[str] = None) -> str:
        """获取地域类型
        
        Args:
            category: 区域类别
        
        Returns:
            地域类型字符串
        """
        category = category or random.choice(ZONE_CATEGORIES)
        group = self.data["zone"][category]
        return random.choice(group)
    
    def get_zone(self, number: int = 1, options_or_kind=None) -> List[Dict]:
        """生成地域名称
        
        Args:
            number: 生成名称的数量
            options_or_kind: 可以是区域类型字符串或包含以下键的选项字典:
                    kind: 区域类型
                    category: 区域类别
        
        Returns:
            生成的地域名称列表，每个元素包含name和rarity
        """
        options = {}
        if isinstance(options_or_kind, str):
            options = {"kind": options_or_kind}
        elif isinstance(options_or_kind, dict):
            options = options_or_kind
        
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            k = options.get("kind") or self._get_zone_kind(options.get("category"))
            rarity = "common"
            
            r = random.random()
            if r < RARITY_VALUES["rare"]:
                name = random.choice(self.data["strange"])
                rarity = "rare"
            elif r < RARITY_VALUES["uncommon"]:
                name = random.choice(common)
                rarity = "uncommon"
            else:
                prefix = ""
                if random.random() < RARITY_VALUES["rare"]:
                    prefix = random.choice(self.data["place_prefix"])
                
                name = prefix + random.choice(self.data["place"])
                if len(name) == 1:
                    if len(k) > 1:
                        name += _LINK_WORD
                    else:
                        if random.random() < RARITY_VALUES["rare"]:
                            name += _LINK_WORD
            
            names.append({"name": name + k, "rarity": rarity})
        
        return names