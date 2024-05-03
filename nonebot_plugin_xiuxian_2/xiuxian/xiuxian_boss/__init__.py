try:
    import ujson as json
except ImportError:
    import json
import re
from pathlib import Path
import random
import os
import math
from nonebot.rule import Rule
from nonebot import get_bots, get_bot ,on_command, require
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    GROUP_ADMIN,
    GROUP_OWNER,
    ActionFailed,
    MessageSegment
)
from ..xiuxian_utils.lay_out import assign_bot, put_bot, layout_bot_dict, Cooldown
from nonebot.permission import SUPERUSER
from nonebot.log import logger
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage ,OtherSet, UserBuffDate,
    XIUXIAN_IMPART_BUFF, leave_harm_time
)
from ..xiuxian_config import get_user_rank, XiuConfig
from .makeboss import createboss, createboss_root, createboss_jj
from .bossconfig import get_config, savef
from .old_boss_info import old_boss_info
from ..xiuxian_utils.player_fight import Boss_fight
from ..xiuxian_utils.item_json import Items
items = Items()
from ..xiuxian_utils.utils import (
    number_to, check_user,
    get_msg_pic, CommandObjectID,
    pic_msg_format, send_msg_handler
)
from .. import DRIVER
# boss定时任务
require('nonebot_plugin_apscheduler')
from nonebot_plugin_apscheduler import scheduler

config = get_config()
cache_help = {}
del_boss_id = XiuConfig().del_boss_id
gen_boss_id = XiuConfig().gen_boss_id
group_boss = {}
groups = config['open']
battle_flag = {}
sql_message = XiuxianDateManage()  # sql类
xiuxian_impart = XIUXIAN_IMPART_BUFF()


def check_rule_bot_boss() -> Rule:  # 消息检测，是超管，群主或者指定的qq号传入的消息就响应，其他的不响应
    async def _check_bot_(bot: Bot, event: GroupMessageEvent) -> bool:
        if (event.sender.role == "admin" or
                event.sender.role == "owner" or
                event.get_user_id() in bot.config.superusers or
                event.get_user_id() in del_boss_id):
            return True
        else:
            return False

    return Rule(_check_bot_)

def check_rule_bot_boss_s() -> Rule:  # 消息检测，是超管或者指定的qq号传入的消息就响应，其他的不响应
    async def _check_bot_(bot: Bot, event: GroupMessageEvent) -> bool:
        if (event.get_user_id() in bot.config.superusers or
                event.get_user_id() in gen_boss_id):
            return True
        else:
            return False

    return Rule(_check_bot_)


create = on_command("生成世界boss", aliases={"生成世界Boss", "生成世界BOSS"}, priority=5,
                    rule=check_rule_bot_boss_s(), block=True)
create_appoint = on_command("生成指定世界boss", aliases={"生成指定世界boss", "生成指定世界BOSS", "生成指定BOSS", "生成指定boss"}, priority=5,
                            rule=check_rule_bot_boss_s())
boss_info = on_command("查询世界boss", aliases={"查询世界Boss", "查询世界BOSS", "查询boss"}, priority=6, permission=GROUP, block=True)
set_group_boss = on_command("世界boss", aliases={"世界Boss", "世界BOSS"}, priority=13,
                            permission=GROUP and (SUPERUSER | GROUP_ADMIN | GROUP_OWNER), block=True)
battle = on_command("讨伐boss", aliases={"讨伐世界boss", "讨伐Boss", "讨伐BOSS", "讨伐世界Boss", "讨伐世界BOSS"}, priority=6,
                    permission=GROUP, block=True)
boss_help = on_command("世界boss帮助", aliases={"世界Boss帮助", "世界BOSS帮助"}, priority=5, block=True)
boss_delete = on_command("天罚boss", aliases={"天罚世界boss", "天罚Boss", "天罚BOSS", "天罚世界Boss", "天罚世界BOSS"}, priority=7,
                         rule=check_rule_bot_boss(), block=True)
boss_delete_all = on_command("天罚所有boss", aliases={"天罚所有世界boss", "天罚所有Boss", "天罚所有BOSS", "天罚所有世界Boss","天罚所有世界BOSS",
                                                  "天罚全部boss", "天罚全部世界boss"}, priority=5,
                             rule=check_rule_bot_boss(), block=True)
boss_integral_info = on_command("世界积分查看",aliases={"查看世界积分", "查询世界积分", "世界积分查询"} ,priority=10, permission=GROUP, block=True)
boss_integral_use = on_command("世界积分兑换", priority=6, permission=GROUP, block=True)

boss_time = config["Boss生成时间参数"]
__boss_help__ = f"""
世界Boss帮助信息:
指令：
1、生成世界boss:生成一只随机大境界的世界Boss,超管权限
2、生成指定世界boss:生成指定大境界与名称的世界Boss,超管权限
3、查询世界boss:查询本群全部世界Boss,可加Boss编号查询对应Boss信息
4、世界boss开启、关闭:开启后才可以生成世界Boss,管理员权限
5、讨伐boss、讨伐世界boss:讨伐世界Boss,必须加Boss编号
6、世界boss帮助、世界boss:获取世界Boss帮助信息
7、天罚boss、天罚世界boss:删除世界Boss,必须加Boss编号,管理员权限
8、天罚所有世界boss:删除所有世界Boss,,管理员权限
9、世界积分查看:查看自己的世界积分,和世界积分兑换商品
10、世界积分兑换+编号：兑换对应的商品
""".strip()


@DRIVER.on_startup
async def read_boss_():
    global group_boss
    group_boss.update(old_boss_info.read_boss_info())
    logger.opt(colors=True).info("<green>历史boss数据读取成功</green>")


@DRIVER.on_startup
async def set_boss_():
    groups_list = list(groups.keys())
    try:
        for group_id in groups_list:
            scheduler.add_job(
                func=send_bot,
                trigger='interval',
                hours=groups[str(group_id)]["hours"],
                minutes=groups[str(group_id)]['minutes'],
                id="set_boss_{}".format(group_id),
                args=[group_id],
                misfire_grace_time=10
            )
            logger.opt(colors=True).success("<green>开启群{}boss,每{}小时{}分钟刷新！</green>".format(group_id, groups[str(group_id)]['hours'], groups[str(group_id)]['minutes']))
    except Exception as e:
        logger.opt(colors=True).warning(f"<red>警告,定时群boss加载失败!,{e}!</red>")


async def send_bot(group_id:str):
    #初始化
    if not group_id in group_boss:
        group_boss[group_id] = []

    if group_id not in groups:
        return     

    if len(group_boss[group_id]) >= config['Boss个数上限']:
        return
    
    api = 'send_group_msg' #要调用的函数
    data = {'group_id': int(group_id)} #要发送的群
    
    bossinfo = createboss()
    group_boss[group_id].append(bossinfo)
    msg = "野生的{}Boss:{}出现了,诸位道友请击Boss得奖励吧!".format(bossinfo['jj'], bossinfo['name'])
    if XiuConfig().img:
        pic = await get_msg_pic(f"@全体修仙者\n" + msg)
        data['message'] = MessageSegment.image(pic)
    else:
        data['message'] = MessageSegment.text(msg)
        
    try:
        bot_id = layout_bot_dict[group_id] if group_id in layout_bot_dict else put_bot[0]
    except:
        bot = get_bot()
        bot_id = bot.self_id
        
    try:
        if type(bot_id) is str:
            await get_bots()[bot_id].call_api(api, **data)
        elif type(bot_id) is list:
            await get_bots()[random.choice(bot_id)].call_api(api,**data)
        else:
            await get_bots()[put_bot[0]].call_api(api, **data)
            
    except:
        if group_id not in bot.get_group_list():
            logger.opt(colors=True).warning(f"<red>群{group_id}不存在,请检查配置文件!</red>")
            return
        else:
            await get_bot().call_api(api, **data)   
        
    logger.opt(colors=True).info(f"<green>群{group_id}已生成世界boss</green>")


@DRIVER.on_shutdown
async def save_boss_():
    global group_boss
    old_boss_info.save_boss(group_boss)
    logger.opt(colors=True).info("<green>boss数据已保存</green>")


@boss_help.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    if session_id in cache_help:
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(cache_help[session_id]))
        await boss_help.finish()
    else:
        if str(send_group_id) in groups:
            msg = __boss_help__ + "非指令:1、拥有定时任务:每{}小时{}分钟生成一只随机大境界的世界Boss".format(
            groups[str(send_group_id)]["hours"], groups[str(send_group_id)]["minutes"]
            )
        else:
            msg = __boss_help__ 
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            cache_help[session_id] = pic
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_help.finish()


@boss_delete.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_delete_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """天罚世界boss"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = args.extract_plain_text().strip()
    group_id = str(event.group_id)
    boss_num = re.findall(r"\d+", msg)  # boss编号
    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"本群尚未开启世界Boss,请联系管理员开启!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_delete.finish()

    if boss_num:
        boss_num = int(boss_num[0])
    else:
        msg = f"请输入正确的世界Boss编号!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_delete.finish()
    bosss = None
    try:
        bosss = group_boss[group_id]
    except:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_delete.finish()

    if not bosss:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_delete.finish()

    index = len(group_boss[group_id])

    if not (0 < boss_num <= index):
        msg = f"请输入正确的世界Boss编号!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_delete.finish()

    group_boss[group_id].remove(group_boss[group_id][boss_num - 1])
    msg = f"该世界Boss被突然从天而降的神雷劈中,烟消云散了"
    if XiuConfig().img:
        pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await boss_delete.finish()

@boss_delete_all.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_delete_all_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """天罚全部世界boss"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = args.extract_plain_text().strip()
    group_id = str(event.group_id)
    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"本群尚未开启世界Boss,请联系管理员开启!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_delete_all.finish()
    bosss = None
    try:
        bosss = group_boss[group_id]
    except:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_delete_all.finish()

    if not bosss:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_delete_all.finish()

    group_boss[group_id] = []
    msg = f"所有的世界Boss都烟消云散了~~"
    if XiuConfig().img:
        pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await boss_delete_all.finish()


@battle.handle(parameterless=[Cooldown(cd_time=XiuConfig().battle_boss_cd,at_sender=False)])
async def battle_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """讨伐世界boss"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()

    sql_message.update_last_check_info_time(user_id) # 更新查看修仙信息时间
    user_id = user_info['user_id']
    msg = args.extract_plain_text().strip()
    group_id = str(event.group_id)
    boss_num = re.findall(r"\d+", msg)  # boss编号

    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"本群尚未开启世界Boss,请联系管理员开启!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()

    if boss_num:
        boss_num = int(boss_num[0])
    else:
        msg = f"请输入正确的世界Boss编号!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()
    bosss = None
    try:
        bosss = group_boss[group_id]
    except:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()

    if not bosss:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()

    index = len(group_boss[group_id])

    if not (0 < boss_num <= index):
        msg = f"请输入正确的世界Boss编号!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()

    # try:
    #    battle_flag[group_id]
    # except:
    #    battle_flag[group_id] = False

    # if battle_flag[group_id]:
    #     msg = f'当前有道友正在Boss战斗!'
    #     if XiuConfig().img:
    #         pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
    #         await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    #     else:
    #         await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    #     await battle.finish()

    if user_info['hp'] is None or user_info['hp'] == 0:
        # 判断用户气血是否为空
        XiuxianDateManage().update_user_hp(user_id)

    if user_info['hp'] <= user_info['exp'] / 10:
        time = leave_harm_time(user_id)
        msg = f"重伤未愈，动弹不得！距离脱离危险还需要{time}分钟！\n"
        msg += f"请道友进行闭关，或者使用药品恢复气血，不要干等，没有自动回血！！！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()

    player = {"user_id": None, "道号": None, "气血": None, "攻击": None, "真元": None, '会心': None, '防御': 0}
    userinfo = XiuxianDateManage().get_user_real_info(user_id)
    user_weapon_data = UserBuffDate(userinfo['user_id']).get_user_weapon_data()

    impart_data = xiuxian_impart.get_user_message(user_id)
    boss_atk = impart_data['boss_atk'] if impart_data['boss_atk'] is not None else 0
    user_armor_data = UserBuffDate(userinfo['user_id']).get_user_armor_buff_data() #boss战防具会心
    user_main_data = UserBuffDate(userinfo['user_id']).get_user_main_buff_data() #boss战功法会心
    user1_sub_buff_data = UserBuffDate(userinfo['user_id']).get_user_sub_buff_data() #boss战辅修功法信息
    integral_buff = user1_sub_buff_data['integral'] if user1_sub_buff_data is not None else 0
    exp_buff = user1_sub_buff_data['exp'] if user1_sub_buff_data is not None else 0
    
    
    
    if  user_main_data != None: #boss战功法会心
        main_crit_buff = user_main_data['crit_buff']
    else:
        main_crit_buff = 0
  
    if  user_armor_data != None: #boss战防具会心
        armor_crit_buff = user_armor_data['crit_buff']
    else:
        armor_crit_buff = 0
    
    if user_weapon_data != None:
        player['会心'] = int(((user_weapon_data['crit_buff']) + (armor_crit_buff) + (main_crit_buff)) * 100)
    else:
        player['会心'] = (armor_crit_buff + main_crit_buff) * 100
    player['user_id'] = userinfo['user_id']
    player['道号'] = userinfo['user_name']
    player['气血'] = userinfo['hp']
    player['攻击'] = int(userinfo['atk'] * (1 + boss_atk))
    player['真元'] = userinfo['mp']
    player['exp'] = userinfo['exp']

    bossinfo = group_boss[group_id][boss_num - 1]
    if bossinfo['jj'] == '零':
        boss_rank = get_user_rank((bossinfo['jj']))[0]
    else:
        boss_rank = get_user_rank((bossinfo['jj'] + '中期'))[0]
    user_rank = get_user_rank(userinfo['level'])[0]
    boss_old_hp = bossinfo['气血']  # 打之前的血量
    more_msg = ''
    battle_flag[group_id] = True
    result, victor, bossinfo_new, get_stone = await Boss_fight(player, bossinfo, bot_id=bot.self_id)
    if victor == "Boss赢了":
        group_boss[group_id][boss_num - 1] = bossinfo_new
        XiuxianDateManage().update_ls(user_id, get_stone, 1)
        # 新增boss战斗积分点数
        boss_now_hp = bossinfo_new['气血']  # 打之后的血量
        boss_all_hp = bossinfo['总血量']  # 总血量
        boss_integral = int(((boss_old_hp - boss_now_hp) / boss_all_hp) * 30)
        if boss_integral < 5:  # 摸一下不给
            boss_integral = 0
        if user_info['root'] == "器师":
            boss_integral = int(boss_integral * (1 + (user_rank - boss_rank)))
            if boss_integral <= 0:
                boss_integral = 0
            more_msg = f"道友低boss境界{user_rank - boss_rank}层，获得{int(50 * (user_rank - boss_rank))}%积分加成！"
        else:
            if boss_rank - user_rank >= 6:  # 超过太多不给
                boss_integral = 0
                more_msg = "道友的境界超过boss太多了,不齿！"
        user_boss_fight_info = get_user_boss_fight_info(user_id)
        user_boss_fight_info['boss_integral'] += boss_integral
        save_user_boss_fight_info(user_id, user_boss_fight_info)
        
        if exp_buff > 0:
            log_exp = math.log(user_info['exp'] + 1)
            now_exp = int(math.exp(log_exp * exp_buff))
            sql_message.update_exp(user_id, now_exp)
            exp_msg = "，获得修为{}点！".format(now_exp)
        else:
            exp_msg =" "
        msg = f"道友不敌{bossinfo['name']}，重伤逃遁，临逃前收获灵石{get_stone}枚，{more_msg}获得世界积分：{boss_integral}点{exp_msg} "
        battle_flag[group_id] = False
        try:
            await send_msg_handler(bot, event, result)
        except ActionFailed:
            msg += "Boss战消息发送错误,可能被风控!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()
    
    elif victor == "群友赢了":
        # 新增boss战斗积分点数
        boss_all_hp = bossinfo['总血量']  # 总血量
        boss_integral = int((boss_old_hp / boss_all_hp) * 30)
        if user_info['root'] == "器师":
            boss_integral = int(boss_integral * (1 + (user_rank - boss_rank)))
            more_msg = f"道友低boss境界{user_rank - boss_rank}层，获得{int(50 * (user_rank - boss_rank))}%积分加成！"
        else:
            if boss_rank - user_rank >= 6:  # 超过太多不给
                boss_integral = 0
                more_msg = "道友的境界超过boss太多了,不齿！"
                
        if exp_buff > 0:
            log_exp = math.log(user_info['exp'] + 1)
            now_exp = int(math.exp(log_exp * exp_buff))
            sql_message.update_exp(user_id, now_exp)
            exp_msg = f"获得修为{now_exp}点！"
        else:
            exp_msg =" "
                
        drops_id, drops_info =  boss_drops(user_rank, boss_rank, bossinfo, userinfo)
        if drops_id == None:
            drops_msg = " "
        elif boss_rank < 22:           
            drops_msg = f"boss的尸体上好像有什么东西， 凑近一看居然是{drops_info['name']}！ "
            sql_message.send_back(user_info['user_id'], drops_info['id'],drops_info['name'], drops_info['type'], 1)
        else :
            drops_msg = " "
            
        group_boss[group_id].remove(group_boss[group_id][boss_num - 1])
        battle_flag[group_id] = False
        XiuxianDateManage().update_ls(user_id, get_stone, 1)
        user_boss_fight_info = get_user_boss_fight_info(user_id)
        user_boss_fight_info['boss_integral'] += boss_integral
        save_user_boss_fight_info(user_id, user_boss_fight_info)
        msg = f"恭喜道友击败{bossinfo['name']}，收获灵石{get_stone}枚，{more_msg}获得世界积分：{boss_integral}点!{exp_msg} {drops_msg}"
        try:
            await send_msg_handler(bot, event, result)
        except ActionFailed:
            msg += "Boss战消息发送错,可能被风控!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await battle.finish()


@boss_info.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_info_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """查询世界boss"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    group_id = str(event.group_id)
    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"本群尚未开启世界Boss,请联系管理员开启!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_info.finish()
    bosss = None
    try:
        bosss = group_boss[group_id]
    except:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_info.finish()

    msg = args.extract_plain_text().strip()
    boss_num = re.findall(r"\d+", msg)  # boss编号

    if not bosss:
        msg = f"本群尚未生成世界Boss,请等待世界boss刷新!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_info.finish()

    Flag = False  # True查对应Boss
    if boss_num:
        boss_num = int(boss_num[0])
        index = len(group_boss[group_id])
        if not (0 < boss_num <= index):
            msg = f"请输入正确的世界Boss编号!"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await boss_info.finish()

        Flag = True

    bossmsgs = ""
    if Flag:  # 查单个Boss信息
        boss = group_boss[group_id][boss_num - 1]
        bossmsgs = f'''
世界Boss:{boss['name']}
境界：{boss['jj']}
总血量：{number_to(boss['总血量'])}
剩余血量：{number_to(boss['气血'])}
攻击：{number_to(boss['攻击'])}
携带灵石：{number_to(boss['stone'])}
        '''
        msg = bossmsgs
        if int(boss["气血"] / boss["总血量"]) < 0.5:
            boss_name = boss["name"] + "_c"
        else:
            boss_name = boss["name"]
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg, boss_name=boss_name)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_info.finish()
    else:
        i = 1
        for boss in bosss:
            bossmsgs += f"编号{i}、{boss['jj']}Boss:{boss['name']} \n"
            i += 1
        msg = bossmsgs
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_info.finish()


@create.handle(parameterless=[Cooldown(at_sender=False)])
async def create_(bot: Bot, event: GroupMessageEvent):
    """生成世界boss"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    group_id = str(event.group_id)
    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"本群尚未开启世界Boss,请联系管理员开启!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await create.finish()

    bossinfo = createboss_root()
    try:
        group_boss[group_id]
    except:
        group_boss[group_id] = []

    if len(group_boss[group_id]) >= config['Boss个数上限']:
        msg = f"本群世界Boss已达到上限{config['Boss个数上限']}个，无法继续生成"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await create.finish()
    group_boss[group_id].append(bossinfo)
    msg = f"已生成{bossinfo['jj']}Boss:{bossinfo['name']},诸位道友请击败Boss获得奖励吧!"
    if XiuConfig().img:
        pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await create.finish()

@create_appoint.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """生成指定世界boss"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    group_id = str(event.group_id)
    isInGroup = isInGroups(event)
    if not isInGroup:#不在配置表内
        msg = f"本群尚未开启世界Boss，请联系管理员开启!"
        if XiuConfig().img:
            msg = await pic_msg_format(msg, event)
            pic = await get_msg_pic(msg)
            await create_appoint.finish(MessageSegment.image(pic))
        else:
            await create_appoint.finish(msg, at_sender=False)
    try:
        group_boss[group_id]
    except:
        group_boss[group_id] = []
    if len(group_boss[group_id]) >= config['Boss个数上限']:
        msg = f"本群世界Boss已达到上限{config['Boss个数上限']}个，无法继续生成"
        if XiuConfig().img:
            msg = await pic_msg_format(msg, event)
            pic = await get_msg_pic(msg)
            await create_appoint.finish(MessageSegment.image(pic))
        else:
            await create_appoint.finish(msg, at_sender=False)
    arg_list = args.extract_plain_text().split()
    if len(arg_list) < 1:
        msg = "请输入正确的指令，例如：生成指定世界boss 祭道境 少姜"
        if XiuConfig().img:
            msg = await pic_msg_format(msg, event)
            pic = await get_msg_pic(msg)
            await create_appoint.finish(MessageSegment.image(pic))
        else:
            await create_appoint.finish(msg, at_sender=False)
    boss_jj = arg_list[0]  # 用户指定的境界
    boss_name = arg_list[1] if len(arg_list) > 1 else None  # 用户指定的Boss名称，如果有的话
    # 使用提供的境界和名称生成boss信息
    bossinfo = createboss_jj(boss_jj, boss_name)
    group_boss[group_id].append(bossinfo)
    msg = f"已生成{bossinfo['jj']}Boss:{bossinfo['name']}，诸位道友请击败Boss获得奖励吧！"
    if XiuConfig().img:
        msg = await pic_msg_format(msg, event)
        pic = await get_msg_pic(msg)
        await create_appoint.finish(MessageSegment.image(pic))
    else:
        await create_appoint.finish(msg, at_sender=False)


@set_group_boss.handle(parameterless=[Cooldown(at_sender=False)])
async def set_group_boss_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """设置群世界boss开关"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    mode = args.extract_plain_text().strip()
    group_id = str(event.group_id)
    isInGroup = isInGroups(event)  # True在，False不在

    if mode == '开启':
        if isInGroup:
            msg = f"本群已开启世界Boss,请勿重复开启!"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await set_group_boss.finish()
        else:    
            info = {
                str(group_id):{
                                "hours":config['Boss生成时间参数']["hours"],
                                "minutes":config['Boss生成时间参数']["minutes"]
                                }
                            }
            config['open'].update(info)
            savef(config)
            msg = f"已开启本群世界Boss!"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await set_group_boss.finish()

    elif mode == '关闭':
        if isInGroup:
            try:
                del config['open'][str(group_id)]
            except:
                pass
            savef(config)
            msg = f"已关闭本群世界Boss!"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await set_group_boss.finish()
        else:
            msg = f"本群未开启世界Boss!"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await set_group_boss.finish()

    elif mode == '':
        if str(send_group_id) in groups:
            msg = __boss_help__ + "非指令:1、拥有定时任务:每{}小时{}分钟生成一只随机大境界的世界Boss".format(
            groups[str(send_group_id)]["hours"], groups[str(send_group_id)]["minutes"]
            )
        else:
            msg = __boss_help__ 
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await set_group_boss.finish()
    else:
        msg = f"请输入正确的指令:世界boss开启或关闭!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await set_group_boss.finish()


@boss_integral_info.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_integral_info_(bot: Bot, event: GroupMessageEvent):
    """世界积分商店"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_integral_info.finish()

    user_id = user_info['user_id']
    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"本群尚未开启世界Boss,请联系管理员开启!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_integral_info.finish()

    user_boss_fight_info = get_user_boss_fight_info(user_id)
    boss_integral_shop = config['世界积分商品']
    l_msg = [f"道友目前拥有的世界积分：{user_boss_fight_info['boss_integral']}点"]
    if boss_integral_shop != {}:
        for k, v in boss_integral_shop.items():
            msg = f"编号:{k}\n"
            msg += f"描述：{v['desc']}\n"
            msg += f"所需世界积分：{v['cost']}点"
            l_msg.append(msg)
    else:
        l_msg.append(f"世界积分商店内空空如也！")
    await send_msg_handler(bot, event, '世界积分商店', bot.self_id, l_msg)
    await boss_integral_info.finish()


@boss_integral_use.handle(parameterless=[Cooldown(at_sender=False)])
async def boss_integral_use_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """世界积分商店兑换"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_integral_use.finish()

    user_id = user_info['user_id']
    msg = args.extract_plain_text().strip()
    shop_num = re.findall(r"\d+", msg)  # boss编号

    isInGroup = isInGroups(event)
    if not isInGroup:  # 不在配置表内
        msg = f"本群尚未开启世界Boss,请联系管理员开启!"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_integral_use.finish()

    if shop_num:
        shop_num = int(shop_num[0])
    else:
        msg = f"请输入正确的商品编号！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_integral_use.finish()

    boss_integral_shop = config['世界积分商品']
    is_in = False
    cost = None
    shop_id = None
    if boss_integral_shop != {}:
        for k, v in boss_integral_shop.items():
            if shop_num == int(k):
                is_in = True
                cost = v['cost']
                shop_id = v['id']
                break
            else:
                continue
    else:
        msg = f"世界积分商店内空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_integral_use.finish()
    if is_in:
        user_boss_fight_info = get_user_boss_fight_info(user_id)
        if user_boss_fight_info['boss_integral'] < cost:
            msg = f"道友的世界积分不满足兑换条件呢"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await boss_integral_use.finish()
        else:
            user_boss_fight_info['boss_integral'] -= cost
            save_user_boss_fight_info(user_id, user_boss_fight_info)
            item_info = Items().get_data_by_item_id(shop_id)
            sql_message.send_back(user_id, shop_id, item_info['name'], item_info['type'], 1)
            msg = f"道友成功兑换获得：{item_info['name']}"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await boss_integral_use.finish()
    else:
        msg = f"该编号不在商品列表内哦，请检查后再兑换"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await boss_integral_use.finish()


def isInGroups(event: GroupMessageEvent):
    return str(event.group_id) in groups


PLAYERSDATA = Path() / "data" / "xiuxian" / "players"


def get_user_boss_fight_info(user_id):
    try:
        user_boss_fight_info = read_user_boss_fight_info(user_id)
    except:
        user_boss_fight_info = {'boss_integral': 0}
        save_user_boss_fight_info(user_id, user_boss_fight_info)
    return user_boss_fight_info


def read_user_boss_fight_info(user_id):
    user_id = str(user_id)

    FILEPATH = PLAYERSDATA / user_id / "boss_fight_info.json"
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def save_user_boss_fight_info(user_id, data):
    user_id = str(user_id)

    if not os.path.exists(PLAYERSDATA / user_id):
        print("目录不存在，创建目录")
        os.makedirs(PLAYERSDATA / user_id)

    FILEPATH = PLAYERSDATA / user_id / "boss_fight_info.json"
    data = json.dumps(data, ensure_ascii=False, indent=4)
    save_mode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=save_mode, encoding="UTF-8") as f:
        f.write(data)
        f.close()

def get_dict_type_rate(data_dict):
    """根据字典内概率,返回字典key"""
    temp_dict = {}
    for i, v in data_dict.items():
        try:
            temp_dict[i] = v["type_rate"]
        except:
            continue
    key = OtherSet().calculated(temp_dict)
    return key

def get_goods_type():
    data_dict = BOSSDLW['宝物']
    return get_dict_type_rate(data_dict)

def get_story_type():
    """根据概率返回事件类型"""
    data_dict = BOSSDLW
    return get_dict_type_rate(data_dict)

BOSSDLW ={"衣以候": "衣以侯布下了禁制镜花水月，",
    "金凰儿": "金凰儿使用了神通：金凰天火罩！",
    "九寒": "九寒使用了神通：寒冰八脉！",
    "莫女": "莫女使用了神通：圣灯启语诀！",
    "术方": "术方使用了神通：天罡咒！",
    "卫起": "卫起使用了神通：雷公铸骨！",
    "血枫": "血枫使用了神通：混世魔身！",
    "以向": "以向使用了神通：云床九练！",
    "砂鲛": "不说了！开鳖！",
    "神风王": "不说了！开鳖！",
    "鲲鹏": "鲲鹏使用了神通：逍遥游！",
    "天龙": "天龙使用了神通：真龙九变！",
    "历飞雨": "厉飞雨使用了神通：天煞震狱功！",
    "外道贩卖鬼": "不说了！开鳖！",
    "元磁道人": "元磁道人使用了法宝：元磁神山！",
    "散发着威压的尸体": "尸体周围爆发了出强烈的罡气！"
    }


def boss_drops(user_rank, boss_rank, boss, user_info):
    boss_dice = random.randint(0,100)
    drops_id = None
    drops_info = None
    if boss_rank - user_rank >= 6:
        drops_id = None
        drops_info = None
    
    elif  boss_dice >= 90:
        drops_id,drops_info = get_drops(user_info)
       
    return drops_id, drops_info    
        
def get_drops(user_info):
    """
    随机获取一个boss掉落物
    :param user_info:用户信息类
    :param rift_rank:秘境等级
    :return 法器ID, 法器信息json
    """
    drops_data = items.get_data_by_item_type(['掉落物'])
    drops_id = get_id(drops_data, user_info['level'])
    drops_info = items.get_data_by_item_id(drops_id)
    return drops_id, drops_info

def get_id(dict_data, user_level):
    """根据字典的rank、用户等级、秘境等级随机获取key"""
    l_temp = []
    final_rank = get_user_rank(user_level)[0]  # 秘境等级，会提高用户的等级
    pass_rank = 55  # 最终等级超过次等级会抛弃
    for k, v in dict_data.items():
        if v["rank"] >= final_rank and (v["rank"] - final_rank) <= pass_rank:
            l_temp.append(k)

    if len(l_temp) == 0:
        return None
    else:
        return random.choice(l_temp)