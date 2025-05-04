from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    MessageSegment
)
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from ..xiuxian_utils.xiuxian2_handle import XiuxianDataManager, OtherSet, UserBuffData
from ..xiuxian_utils.data_source import jsondata
from .draw_user_info import draw_user_info_img
from ..xiuxian_utils.utils import check_user, number_to, handle_send
from ..xiuxian_config import XiuConfig

xiuxian_message = on_command("我的修仙信息", aliases={"我的存档"}, priority=23, permission=GROUP, block=True)
  # sql类


@xiuxian_message.handle(parameterless=[Cooldown(at_sender=False)])
async def xiuxian_message_(bot: Bot, event: GroupMessageEvent):
    """我的修仙信息"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = await check_user(event)
    if not isUser:
        await handle_send(bot, event, send_group_id, msg)
        await xiuxian_message.finish()
    user_id = user_info['user_id']
    user_info = await XiuxianDataManager().get_user_real_info(user_id)
    user_name = user_info['user_name']
    
    
    user_num = user_info['id']
    rank = await XiuxianDataManager().get_exp_rank(user_id)
    user_rank = int(rank) if rank is not None else 0
    stone = await XiuxianDataManager().get_stone_rank(user_id)
    user_stone = int(stone) if stone is not None else 0

    if user_name:
        pass
    else:
        user_name = "无名"

    level_rate = await XiuxianDataManager().get_root_rate(user_info['root_type'])  # 灵根倍率
    realm_rate = jsondata.level_data()[user_info['level']]["spend"]  # 境界倍率
    sect_id = user_info['sect_id']
    if sect_id:
        sect_info = await XiuxianDataManager().get_sect_info(sect_id)
        sectmsg = sect_info['sect_name']
        sectzw = jsondata.sect_config_data()[f"{user_info['sect_position']}"]["title"]
    else:
        sectmsg = "无宗门"
        sectzw = "无"

    
    # 判断突破的修为
    list_all = len(OtherSet().level) - 1
    now_index = OtherSet().level.index(user_info['level'])
    if list_all == now_index:
        exp_meg = "位面至高"
    else:
        is_updata_level = OtherSet().level[now_index + 1]
        need_exp = await XiuxianDataManager().get_level_power(is_updata_level)
        get_exp = need_exp - user_info['exp']
        if get_exp > 0:
            exp_meg = f"还需{number_to(get_exp)}修为可突破！"
        else:
            exp_meg = "可突破！"

    user_buff_data = UserBuffData(user_id)
    user_main_buff_date = await user_buff_data.get_user_main_buff_data()
    user_sub_buff_date = await user_buff_data.get_user_sub_buff_data()
    user_sec_buff_date = await user_buff_data.get_user_sec_buff_data()
    user_weapon_data = await user_buff_data.get_user_weapon_data()
    user_armor_data = await user_buff_data.get_user_armor_buff_data()
    main_buff_name = "无"
    sub_buff_name = "无"
    sec_buff_name = "无"
    weapon_name = "无"
    armor_name = "无"
    if user_main_buff_date is not None:
        main_buff_name = f"{user_main_buff_date['name']}({user_main_buff_date['level']})"
    if user_sub_buff_date is not None:
        sub_buff_name = f"{user_sub_buff_date['name']}({user_sub_buff_date['level']})"   
    if user_sec_buff_date is not None:
        sec_buff_name = f"{user_sec_buff_date['name']}({user_sec_buff_date['level']})"
    if user_weapon_data is not None:
        weapon_name = f"{user_weapon_data['name']}({user_weapon_data['level']})"
    if user_armor_data is not None:
        armor_name = f"{user_armor_data['name']}({user_armor_data['level']})"
    main_rate_buff = await UserBuffData(user_id).get_user_main_buff_data() # 功法突破概率提升
    await XiuxianDataManager().update_last_check_info_time(user_id) # 更新查看修仙信息时间
    leveluprate = int(user_info['level_up_rate'])  # 用户失败次数加成
    number =  main_rate_buff["number"] if main_rate_buff is not None else 0
    DETAIL_MAP = {
        "道号": f"{user_name}",
        "境界": f"{user_info['level']}",
        "修为": f"{number_to(user_info['exp'])}",
        "灵石": f"{number_to(user_info['stone'])}",
        "战力": f"{number_to(float(user_info['exp']) * float(level_rate) * float(realm_rate))}",
        "灵根": f"{user_info['root']}({user_info['root_type']}+{int(level_rate * 100)}%)",
        "突破状态": f"{exp_meg}概率：{jsondata.level_rate_data()[user_info['level']] + leveluprate + number}%",
        "攻击力": f"{number_to(user_info['atk'])}，攻修等级{user_info['atk_practice_level']}级",
        "所在宗门": sectmsg,
        "宗门职位": sectzw,
        "主修功法": main_buff_name,
        "辅修功法": sub_buff_name,
        "副修神通": sec_buff_name,
        "法器": weapon_name,
        "防具": armor_name,
        "注册位数": f"道友是踏入修仙世界的第{int(user_num)}人",
        "修为排行": f"道友的修为排在第{int(user_rank)}位",
        "灵石排行": f"道友的灵石排在第{int(user_stone)}位",
    }
    
    if XiuConfig().user_info_image:
        img_res = await draw_user_info_img(user_id, DETAIL_MAP)
        # 根据不同返回类型处理图片
        await bot.send_group_msg(
            group_id=int(send_group_id), 
            message=MessageSegment.image(img_res)
        )
        await xiuxian_message.finish()
    else:
        msg = """{user_name}道友的信息
灵根为：{user_info['root']}({user_info['root_type']}+{int(level_rate * 100)}%)
当前境界：{user_info['level']}(境界+{int(realm_rate * 100)}%)
当前灵石：{user_info['stone']}
当前修为：{user_info['exp']}(修炼效率+{int((level_rate * realm_rate) * 100)}%)
突破状态：{exp_meg}
你的战力为：{int(user_info['exp'] * level_rate * realm_rate)}"""
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)