# 修仙名称生成器 (Python版)

基于JavaScript版本的[random_chinese_fantasy_names](https://github.com/hythl0day/random_chinese_fantasy_names)转写，提供了Python的API接口。

## 快速开始

```python
from xiuxian_names_generator import XiuXianNameGenerator, RARITY_NAMES

# 创建名称生成器实例
generator = XiuXianNameGenerator(data_dir="data")

# 生成人名
names = generator.get_name(5)
for name in names:
    print(name)

# 生成道号
dao_names = generator.get_dao(3)
for dao in dao_names:
    print(f"{dao['name']} 
  
# 生成技能名称
skills = generator.get_skill(3)
for skill in skills:
    print(f"{skill['name']} ({RARITY_NAMES[skill['rarity']]})")

```

## API 参考

### 常量

- `SEX_VALUES`: 性别常量列表
- `RARITY_COLORS`: 稀有度对应的颜色
- `RARITY_LEVELS`: 稀有度级别列表
- `RARITY_VALUES`: 稀有度对应的概率值
- `RARITY_NAMES`: 稀有度对应的中文名称
- `CREATURE_CATEGORY`: 生物种类列表
- `CREATURE_CATEGORY_NAMES`: 生物种类对应的中文名称
- `ZONE_CATEGORIES`: 区域类别列表

### XiuXianNameGenerator 类

#### 构造函数

```python
XiuXianNameGenerator(data_dir="data")
```

- `data_dir`: 数据文件目录的路径

#### 属性

- `dao_titles`: 获取所有道号称号列表
- `book_prefixes`: 获取所有书籍前缀列表
- `talisman_kind`: 获取所有符箓类型列表
- `material_kind`: 获取所有材料类型列表
- `material_postfixes`: 获取所有材料后缀列表
- `talisman_postfixes`: 获取所有符箓后缀列表
- `zone_kind`: 获取所有区域类型列表
- `book_postfixes`: 获取所有书籍后缀列表

#### 方法

##### 生成人名

```python
get_name(number=1, options=None) -> List[str]
```

- `number`: 生成名字的数量
- `options`: 选项参数，可包含:
  - `familyName`: 指定姓氏
  - `isFemale`: 是否女性
  - `style`: 命名风格('single', 'double', 'combine')
  - `middleCharacter`: 中间字符

##### 生成道号

```python
get_dao(number=1, options=None) -> List[Dict]
```

- `number`: 生成道号的数量
- `options`: 选项参数，可包含:
  - `firstCharacter`: 第一个字符
  - `isFemale`: 是否女性
  - `title`: 称号

##### 生成功法名称

```python
get_skill(number=1, options=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `options`: 选项参数，可包含:
  - `length`: 长度
  - `kind`: 类型
  - `prefix`: 前缀
  - `numfix`: 数字后缀

##### 生成秘籍名称

```python
get_book(number=1, options=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `options`: 选项参数，可包含:
  - `length`: 长度
  - `mainkind`: 主要类型
  - `prefix`: 前缀
  - `postkind`: 后缀类型
  - `postfix`: 后缀

##### 生成生灵名称

```python
get_creature(number=1, options=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `options`: 选项参数，可包含:
  - `category`: 种类
  - `rarity`: 稀有度

##### 生成材料名称

```python
get_material(number=1, options=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `options`: 选项参数，可包含:
  - `kind`: 类型
  - `rarity`: 稀有度
  - `postfix`: 后缀

##### 生成法宝名称

```python
get_talisman(number=1, options=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `options`: 选项参数，可包含:
  - `kind`: 类型
  - `rarity`: 稀有度
  - `postfix`: 后缀

##### 生成丹药名称

```python
get_alchemy(number=1, kind=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `kind`: 丹药类型

##### 生成门派名称

```python
get_clan(number=1, kind=None) -> List[str]
```

- `number`: 生成名称的数量
- `kind`: 门派类型

##### 生成国家名称

```python
get_nation(number=1, kind=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `kind`: 国家类型

##### 生成据点名称

```python
get_location(number=1, kind=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `kind`: 类型

##### 生成地域名称

```python
get_zone(number=1, options_or_kind=None) -> List[Dict]
```

- `number`: 生成名称的数量
- `options_or_kind`: 可以是类型字符串或包含以下键的选项字典:
  - `kind`: 类型
  - `category`: 类别

## 示例

完整示例请参考 [example_names.py](./example_names.py) 文件。

## 许可证

与原JavaScript版本相同。
