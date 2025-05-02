try:
    import ujson as json
except ImportError:
    import json
import os
from pathlib import Path
from typing import Any, Tuple
from nonebot import on_regex
from nonebot.log import logger
from nonebot.params import RegexGroup
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    GROUP,
    MessageSegment,
)
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from ..xiuxian_utils.xiuxian2_handle import XiuxianDataManager
from datetime import datetime
from .bankconfig import get_config
from ..xiuxian_utils.utils import check_user, get_msg_pic, handle_send
from ..xiuxian_config import XiuConfig

config = get_config()
BANKLEVEL = config["BANKLEVEL"]
  # sql类
PLAYERSDATA = Path() / "data" / "xiuxian" / "players"

bank = on_regex(
    r'^灵庄(存灵石|取灵石|升级会员|信息|结算)?(.*)?',
    priority=9,
    permission=GROUP,
    block=True
)

__bank_help__ = f"""
灵庄帮助信息:
指令：
1、灵庄:查看灵庄帮助信息
2、灵庄存灵石:指令后加存入的金额,获取利息(复利计算)
3、灵庄取灵石:指令后加取出的金额,会先结算利息,再取出灵石
4、灵庄升级会员:灵庄利息倍率与灵庄会员等级有关,升级会员会提升利息倍率
5、灵庄信息:查询自己当前的灵庄信息
6、灵庄结算:结算利息
""".strip()


@bank.handle(parameterless=[Cooldown(at_sender=False)])
async def bank_(bot: Bot, event: GroupMessageEvent, args: Tuple[Any, ...] = RegexGroup()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = await check_user(event)
    from ..xiuxian_utils.utils import number_to, handle_send
    if not isUser:
        await handle_send(bot, event, send_group_id, msg)
        await bank.finish()
    mode = args[0]  # 存灵石、取灵石、升级会员、信息查看
    num = args[1]  # 数值
    if mode is None:
        msg = __bank_help__
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await bank.finish()

    if mode == '存灵石' or mode == '取灵石':
        try:
            num = int(num)
            if num <= 0:
                msg = f"请输入正确的金额！"
                await handle_send(bot, event, send_group_id, msg)
                await bank.finish()
        except ValueError:
            msg = f"请输入正确的金额！"
            await handle_send(bot, event, send_group_id, msg)
            await bank.finish()
    user_id = user_info['user_id']
    try:
        bankinfo = readf(user_id)
    except:
        bankinfo = {
            'savestone': 0,
            'savetime': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'banklevel': '1',
        }

    if mode == '存灵石':  # 存灵石逻辑
        if int(user_info['stone']) < num:
            msg = f"道友所拥有的灵石为{number_to(user_info['stone'])}枚，金额不足，请重新输入！"
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await bank.finish()

        # 先结算之前的利息，采用复利计算
        bankinfo, give_stone, days_diff = get_give_stone(bankinfo)
        
        max = BANKLEVEL[bankinfo['banklevel']]['savemax']
        # 更新存款金额，加上利息
        bankinfo['savestone'] += give_stone
        # 检查是否超过最大存款额度
        if bankinfo['savestone'] > max:
            # 如果超过了，将超出部分加到用户灵石中
            overflow = bankinfo['savestone'] - max
            await XiuxianDataManager().update_ls(user_id, overflow, 0)
            msg = f"道友本次结息时间为：{days_diff:.1f}天，获得灵石：{number_to(give_stone)}枚!\n已达到存款上限，多余的{number_to(overflow)}灵石已返还给道友。"
            bankinfo['savestone'] = max
            savef(user_id, bankinfo)
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await bank.finish()
            
        # 确认剩余可存储空间
        nowmax = max - bankinfo['savestone']

        if num > nowmax:
            msg = f"道友当前灵庄会员等级为{BANKLEVEL[bankinfo['banklevel']]['level']}，可存储的最大灵石为{number_to(max)}枚,当前已存{number_to(bankinfo['savestone'])}枚灵石，可以继续存{number_to(nowmax)}枚灵石！"
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await bank.finish()

        userinfonowstone = int(user_info['stone']) - num
        # 更新利息后的存款金额再加上新存款
        bankinfo['savestone'] += num
        await XiuxianDataManager().update_ls(user_id, num, 1)
        # 将之前结算的利息加给用户
        await XiuxianDataManager().update_ls(user_id, give_stone, 0)
        bankinfo['savetime'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        savef(user_id, bankinfo)
        msg = f"道友本次结息时间为：{days_diff:.1f}天，获得灵石：{number_to(give_stone)}枚!\n道友存入灵石{number_to(num)}枚，当前所拥有灵石{number_to(userinfonowstone + give_stone)}枚，灵庄存有灵石{number_to(bankinfo['savestone'])}枚"
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await bank.finish()

    elif mode == '取灵石':  # 取灵石逻辑
        # 先结算利息，采用复利计算
        bankinfo, give_stone, days_diff = get_give_stone(bankinfo)
        # 更新存款金额，加上利息
        bankinfo['savestone'] += give_stone
        
        if int(bankinfo['savestone']) < num:
            msg = f"道友当前灵庄所存有的灵石为{number_to(bankinfo['savestone'])}枚，金额不足，请重新输入！"
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await bank.finish()

        userinfonowstone = int(user_info['stone']) + num
        bankinfo['savestone'] -= num
        await XiuxianDataManager().update_ls(user_id, num, 0)
        savef(user_id, bankinfo)
        msg = f"道友本次结息时间为：{days_diff:.1f}天，获得灵石：{number_to(give_stone)}枚!\n取出灵石{number_to(num)}枚，当前所拥有灵石{number_to(userinfonowstone)}枚，灵庄存有灵石{number_to(bankinfo['savestone'])}枚!"
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await bank.finish()

    
    elif mode == '升级会员':  # 升级会员逻辑
        userlevel = bankinfo["banklevel"]
        if userlevel == str(len(BANKLEVEL)):
            msg = f"道友已经是本灵庄最大的会员啦！"
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await bank.finish()

        stonecost = BANKLEVEL[f"{int(userlevel)}"]['levelup']
        if int(user_info['stone']) < stonecost:
            msg = f"道友所拥有的灵石为{number_to(user_info['stone'])}枚，当前升级会员等级需求灵石{number_to(stonecost)}枚，金额不足，请重新输入！"
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await bank.finish()

        await XiuxianDataManager().update_ls(user_id, stonecost, 1)
        bankinfo['banklevel'] = f"{int(userlevel) + 1}"
        savef(user_id, bankinfo)
        msg = f"道友成功升级灵庄会员等级，消耗灵石{number_to(stonecost)}枚，当前为：{BANKLEVEL[str(int(userlevel) + 1)]['level']}，灵庄可存有灵石上限{number_to(BANKLEVEL[str(int(userlevel) + 1)]['savemax'])}枚"

        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await bank.finish()

    elif mode == '信息':  # 查询灵庄信息
        msg = f'''道友的灵庄信息：
已存：{number_to(bankinfo['savestone'])}灵石
存入时间：{bankinfo['savetime']}
灵庄会员等级：{BANKLEVEL[bankinfo['banklevel']]['level']}
当前拥有灵石：{number_to(user_info['stone'])}
当前等级存储灵石上限：{number_to(BANKLEVEL[bankinfo['banklevel']]['savemax'])}枚
利息计算方式：0.1%/天（复利）
'''
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await bank.finish()

    elif mode == '结算':
        # 结算利息，采用复利计算
        bankinfo, give_stone, days_diff = get_give_stone(bankinfo)
        
        # 检查是否会超过最大存款额度
        max = BANKLEVEL[bankinfo['banklevel']]['savemax']
        if bankinfo['savestone'] + give_stone > max:
            # 如果超过了，将超出部分加到用户灵石中
            overflow = (bankinfo['savestone'] + give_stone) - max
            actual_give = give_stone - overflow
            await XiuxianDataManager().update_ls(user_id, give_stone, 0)
            bankinfo['savestone'] = max
            savef(user_id, bankinfo)
            msg = f"道友本次结息时间为：{days_diff:.1f}天，获得灵石：{number_to(give_stone)}枚！\n已达到存款上限，多余的{number_to(overflow)}灵石已返还给道友。"
        else:
            # 未超过上限，将全部利息加入存款
            bankinfo['savestone'] += give_stone
            savef(user_id, bankinfo)
            msg = f"道友本次结息时间为：{days_diff:.1f}天，获得灵石：{number_to(give_stone)}枚！"
            
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await bank.finish()


def get_give_stone(bankinfo):
    """获取利息：利息 = give_stone,结算时间 = days_diff"""
    savetime = bankinfo['savetime']  # str
    nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # str
    days_diff = round((datetime.strptime(nowtime, '%Y-%m-%d %H:%M:%S') -
                      datetime.strptime(savetime, '%Y-%m-%d %H:%M:%S')).total_seconds() / 86400, 2)
    
    # 计算复利，1天为一个周期
    days = int(days_diff)
    remaining_time = days_diff - days
    
    # 初始本金
    principal = bankinfo['savestone']
    interest_rate = BANKLEVEL[bankinfo['banklevel']]['interest']
    
    # 按天计算复利
    for _ in range(days):
        interest = int(principal * interest_rate)
        principal += interest
    
    # 计算剩余时间的利息（按单利）
    if remaining_time > 0:
        final_interest = int(principal * remaining_time * interest_rate)
        principal += final_interest
    
    # 计算总利息
    give_stone = principal - bankinfo['savestone']
    
    # 更新存款时间，但不改变存款金额，在调用函数后处理
    bankinfo['savetime'] = nowtime

    return bankinfo, give_stone, days_diff


def readf(user_id):
    user_id = str(user_id)
    FILEPATH = PLAYERSDATA / user_id / "bankinfo.json"
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def savef(user_id, data):
    user_id = str(user_id)
    if not os.path.exists(PLAYERSDATA / user_id):
        logger.opt(colors=True).info(f"<green>用户目录不存在，创建目录</green>")
        os.makedirs(PLAYERSDATA / user_id)
    FILEPATH = PLAYERSDATA / user_id / "bankinfo.json"
    data = json.dumps(data, ensure_ascii=False, indent=3)
    savemode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=savemode, encoding="UTF-8") as f:
        f.write(data)
        f.close()
    return True
