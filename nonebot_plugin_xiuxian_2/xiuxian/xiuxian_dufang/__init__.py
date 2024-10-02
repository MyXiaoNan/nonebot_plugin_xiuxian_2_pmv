import random
from re import I
from typing import Any, Tuple
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot import on_regex, on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    MessageSegment
)
from nonebot.params import RegexGroup
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.utils import (
    check_user,
    get_msg_pic,
    CommandObjectID
)
cache_help = {}
sql_message = XiuxianDateManage()  # sql类

__dufang_help__ = f"""
封群的，不建议玩！！！
超管可以调试，如果你真想玩并且不介意封群风险，可以让超管修改代码
""".strip()
dufang_help = on_command("金银阁帮助", permission=GROUP, priority=7, block=True)
dufang = on_regex(
    r"(金银阁)\s?(\d+)\s?([大|小|奇|偶|猜])?\s?(\d+)?",
    flags=I,
    permission=GROUP and (SUPERUSER),
    block=True
)

@dufang_help.handle(parameterless=[Cooldown(at_sender=False)])
async def dufang_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    if session_id in cache_help:
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(cache_help[session_id]))
        await dufang_help.finish()
    else:
        msg = __dufang_help__
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            cache_help[session_id] = pic
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await dufang_help.finish()


@dufang.handle(parameterless=[Cooldown(cd_time=XiuConfig().dufang_cd, at_sender=False)])
async def dufang_(bot: Bot, event: GroupMessageEvent, args: Tuple[Any, ...] = RegexGroup()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)

    isUser, user_info, msg = check_user(event)
    user_id = user_info['user_id']
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await dufang.finish()

    user_message = sql_message.get_user_info_with_id(user_id)

    if args[2] is None:
        msg = f"请输入正确的指令，例如金银阁10大、金银阁10奇、金银阁10猜3"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await dufang.finish()

    price = args[1]  # 300
    mode = args[2]  # 大、小、奇、偶、猜
    mode_num = 0
    if mode == '猜':
        mode_num = args[3]  # 猜的数值
        if str(mode_num) not in ['1', '2', '3', '4', '5', '6']:
            msg = f"请输入正确的指令，例如金银阁10大、、金银阁10奇、金银阁10猜3"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await dufang.finish()
    price_num = int(price)

    if int(user_message['stone']) < price_num:
        msg = "道友的金额不足，请重新输入！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    elif price_num == 0:
        msg = "走开走开，没钱也敢来这赌！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)

    value = random.randint(1, 6)
    result = f"[CQ:dice,value={value}]"

    if value >= 4 and str(mode) == "大":
        sql_message.update_ls(user_id, price_num, 1)
        await bot.send_group_msg(group_id=int(send_group_id), message=result)
        msg = f"最终结果为{value}，你猜对了，收获灵石{price_num}块"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        
    elif value <= 3 and str(mode) == "小":
        sql_message.update_ls(user_id, price_num, 1)
        await bot.send_group_msg(group_id=int(send_group_id), message=result)
        msg = f"最终结果为{value}，你猜对了，收获灵石{price_num}块"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    elif value %2==1 and str(mode) == "奇":
        sql_message.update_ls(user_id, price_num, 1)
        await bot.send_group_msg(group_id=int(send_group_id), message=result)
        msg = f"最终结果为{value}，你猜对了，收获灵石{price_num}块"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    elif value %2==0 and str(mode) == "偶":
        sql_message.update_ls(user_id, price_num, 1)
        msg = f"最终结果为{value}，你猜对了，收获灵石{price_num}块"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)

    elif str(value) == str(mode_num) and str(mode) == "猜":
        sql_message.update_ls(user_id, price_num * 5, 1)
        msg = f"最终结果为{value}，你猜对了，收获灵石{price_num * 5}块"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)

    else:
        sql_message.update_ls(user_id, price_num, 2)
        msg = f"最终结果为{value}，你猜错了，损失灵石{price_num}块"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)