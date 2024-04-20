from nonebot import on_command, on_fullmatch
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot.params import CommandArg
from ..xiuxian_utils.xiuxian_config import XiuConfig
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment,
    ActionFailed
)
from ..xiuxian_utils.utils import (
    check_user, get_msg_pic
)
sql_message = XiuxianDateManage()  # sql类
import re
from ..xiuxian_utils.item_json import Items
items = Items()
from nonebot.permission import SUPERUSER

tz = on_command('合成天罪', priority=15, permission=GROUP,block=True)

@tz.handle(parameterless=[Cooldown(at_sender=True)])
async def use_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    user_id = user_info.user_id
    back_msg = sql_message.get_back_msg(user_id)
    if back_msg is None:
        msg = "道友的背包空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await tz.finish()
        

    wz = "无罪（残缺）"
    yz = "原罪（残缺）"
    in_flag_wz = False  # 判断无罪（残缺）是否在背包内
    in_flag_yz = False  # 判断原罪（残缺）是否在背包内

    for back in back_msg:
        if wz == back.goods_name:
            in_flag_wz = True
        elif yz == back.goods_name:
            in_flag_yz = True
        if in_flag_wz and in_flag_yz:
            break
    
    if not in_flag_wz:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + "请检查 {} 是否在背包内！".format(wz))
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await tz.finish()
    
    if not in_flag_yz:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + "请检查 {} 是否在背包内！".format(yz))
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await tz.finish()

    if in_flag_wz and in_flag_yz:
        sql_message.update_back_j(user_id, 7098)
        sql_message.update_back_j(user_id, 7099)
        sql_message.send_back(user_id, 7084, '天罪', '装备', 1, 0)
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + "道友成功合成了无上仙器天罪！！")
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await tz.finish()
    



