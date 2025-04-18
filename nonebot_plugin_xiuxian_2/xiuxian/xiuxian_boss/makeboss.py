import random
from pathlib import Path
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from .bossconfig import get_boss_config
import json

config = get_boss_config()
JINGJIEEXP = {  # 数值为中期和圆满的平均值
    "搬血境": [100, 200, 300],
    "洞天境": [600, 800, 1000],
    "化灵境": [3000, 6000, 9000],
    "铭纹境": [14400, 16000, 17600],
    "列阵境": [35200, 28400, 41600],
    "尊者境": [83200, 89600, 96000],
    "神火境": [192000, 204800, 217600],
    "真一境": [435200, 460800, 486400],
    "圣祭境": [972800, 1234800, 1496800],
    "天神境": [3096800, 3596800, 4096800],
    "虚道境": [6096800, 7096800, 8096800],
    "斩我境": [12096800, 14096800, 16096800],
    "遁一境": [32193600, 45071040, 57948480],
    "至尊境": [115896960, 162255744, 208614528],
    "真仙境": [417229056, 584120678, 751012300],
    "仙王境": [1502024601, 2102834442, 2703644282],
    "准帝境": [5407288565, 7570203992, 9733119418],
    "仙帝境": [19466238836, 27252734370, 35039229904],
    "祭道境": [155039229904, 185039229904, 215039229904]
}

jinjie_list = [k for k, v in JINGJIEEXP.items()]
sql_message = XiuxianDateManage()  # sql类

def get_boss_jinjie_dict():
    CONFIGJSONPATH = Path() / "data" / "xiuxian" / "境界.json"
    with open(CONFIGJSONPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    temp_dict = {}
    data = json.loads(data)
    for k, v in data.items():
        temp_dict[k] = v['exp']
    return temp_dict


def get_boss_exp(boss_jj):
    if boss_jj in JINGJIEEXP:
        bossexp = random.choice(JINGJIEEXP[boss_jj])
        bossinfo = {
            '气血': bossexp * config["Boss倍率"]["气血"],
            '总血量': bossexp * config["Boss倍率"]["气血"],
            '真元': bossexp * config["Boss倍率"]["真元"],
            '攻击': int(bossexp * config["Boss倍率"]["攻击"])
        }
        return bossinfo
    else:
        return None


def createboss():
    top_user_info = sql_message.get_realm_top1_user() # 改成了境界第一
    top_user_level = top_user_info['level']
    if len(top_user_level) == 5:
        level = top_user_level[:3] 
    elif len(top_user_level) == 4: # 对江湖好手判断
        level = "搬血境"

    boss_jj = random.choice(jinjie_list[:jinjie_list.index(level) + 1])
    bossinfo = get_boss_exp(boss_jj)
    bossinfo['name'] = random.choice(config["Boss名字"])
    bossinfo['jj'] = boss_jj
    bossinfo['stone'] = random.choice(config["Boss灵石"][boss_jj])
    return bossinfo


def createboss_jj(boss_jj, boss_name=None):
    bossinfo = get_boss_exp(boss_jj)
    if bossinfo:
        bossinfo['name'] = boss_name if boss_name else random.choice(config["Boss名字"])
        bossinfo['jj'] = boss_jj
        bossinfo['stone'] = random.choice(config["Boss灵石"][boss_jj])
        return bossinfo
    else:
        return None


