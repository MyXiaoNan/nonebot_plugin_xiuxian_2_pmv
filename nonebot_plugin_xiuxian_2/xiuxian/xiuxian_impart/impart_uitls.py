import os
import asyncio
from pathlib import Path
import numpy
import random
from nonebot.adapters.onebot.v11 import (
    MessageSegment,
)

from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.xiuxian2_handle import XiuxianDataManager
from .impart_data import impart_data_json

img_path = Path() / os.getcwd() / "data" / "xiuxian" / "卡图"


def random_int():
    return numpy.random.randint(low=0, high=10000, size=None, dtype="l")


# 抽卡概率来自https://www.bilibili.com/read/cv10468091
# 角色抽卡概率
def character_probability(count):
    count += 1
    if count <= 73:
        ret = 60
    else:
        ret = 60 + 600 * (count - 73)
    return ret


async def get_rank(user_id):
    impart_data = await XiuxianDataManager().get_user_impart_info_with_id(user_id)
    value = random_int()
    num = int(impart_data["impart_wish_quantity"])
    for x in range(num, num + 10):
        index_5 = character_probability(x)
        if value <= index_5:
            return True
        if x >= 89:
            return True
    return False


async def impart_check(user_id):
    impart_data_json.find_user_impart(user_id)
    if await XiuxianDataManager().get_user_impart_info_with_id(user_id) is None:
        await XiuxianDataManager()._create_user(user_id)
        return await XiuxianDataManager().get_user_impart_info_with_id(user_id)
    else:
        return await XiuxianDataManager().get_user_impart_info_with_id(user_id)
    
    


async def build_draw_images(time_imgs, special_card):
    imgs = time_imgs[:10]
    random.shuffle(imgs)
    imgs[random.randint(0, 9)] = special_card
    return imgs


async def re_impart_data(user_id):
    list_tp = impart_data_json.data_person_list(user_id)
    if list_tp is None:
        return False
    else:
        all_data = impart_data_json.data_all_()
        impart_two_exp_quantity = 0
        impart_exp_addition = 0
        impart_atk_addition = 0
        impart_hp_addition = 0
        impart_mp_addition = 0
        impart_boss_atk_addition = 0
        impart_crit_addition = 0
        impart_crit_dmg_addition = 0
        impart_mix_addition = 0
        impart_reap_addition = 0
        for x in list_tp:
            if all_data[x]["type"] == "impart_two_exp_quantity":
                impart_two_exp_quantity = impart_two_exp_quantity + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_exp_addition":
                impart_exp_addition = impart_exp_addition + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_atk_addition":
                impart_atk_addition = impart_atk_addition + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_hp_addition":
                impart_hp_addition = impart_hp_addition + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_mp_addition":
                impart_mp_addition = impart_mp_addition + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_boss_atk_addition":
                impart_boss_atk_addition = impart_boss_atk_addition + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_crit_addition":
                impart_crit_addition = impart_crit_addition + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_crit_dmg_addition":
                impart_crit_dmg_addition = impart_crit_dmg_addition + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_mix_addition":
                impart_mix_addition = impart_mix_addition + all_data[x]["vale"]
            elif all_data[x]["type"] == "impart_reap_addition":
                impart_reap_addition = impart_reap_addition + all_data[x]["vale"]
            else:
                pass
        
        await asyncio.gather(
            XiuxianDataManager().update_impart_two_exp(impart_two_exp_quantity, user_id),
            XiuxianDataManager().update_impart_exp_up(impart_exp_addition, user_id),
            XiuxianDataManager().update_impart_atk_per(impart_atk_addition, user_id),
            XiuxianDataManager().update_impart_hp_per(impart_hp_addition, user_id),
            XiuxianDataManager().update_impart_mp_per(impart_mp_addition, user_id),
            XiuxianDataManager().update_boss_atk(impart_boss_atk_addition, user_id),
            XiuxianDataManager().update_impart_know_per(impart_crit_addition, user_id),
            XiuxianDataManager().update_impart_burst_per(impart_crit_dmg_addition, user_id),
            XiuxianDataManager().update_impart_mix_per(impart_mix_addition, user_id),
            XiuxianDataManager().update_impart_reap_per(impart_reap_addition, user_id)
        )
        return True


async def update_user_impart_data(user_id, time: int):
    """更新用户传承数据

    Args:
        user_id: 用户QQ号
        time: 传承时间
    """
    await XiuxianDataManager().add_impart_exp_day(time, user_id)
    await XiuxianDataManager().update_stone_num(10, user_id, 1)
    await XiuxianDataManager().update_impart_wish(0, user_id)
    # 更新传承数据
    await re_impart_data(user_id)


def get_image_representation(image_name: str) -> MessageSegment | str:
    """根据是否发送图片获取获取对应卡面描述

    Args:
        image_name: 卡面名称

    Returns:
        图片或者文字描述
    """
    return (
        MessageSegment.image(img_path / str(image_name + ".webp"))
        if XiuConfig().merge_forward_send
        else str(image_name)
    )
