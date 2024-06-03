from nonebot import on_command, on_fullmatch
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_utils.data_source import jsondata
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    MessageSegment
)
from ..xiuxian_utils.utils import (
    check_user, get_msg_pic,
    CommandObjectID
)

__warring_help__ = """
详情：
散尽修为，轮回重修，将万世的道果凝聚为极致天赋
修为、功法、神通将被清空！！
进入千世轮回：获得轮回灵根，可定制极品仙器(在做)
进入万世轮回：获得真轮回灵根，可定制无上仙器(在做)
自废修为：字面意思，仅搬血境可用
""".strip()

cache_help_fk = {}
sql_message = XiuxianDateManage()  # sql类

warring_help = on_fullmatch("轮回重修帮助", priority=12, permission=GROUP, block=True)
lunhui = on_command('进入千世轮回', priority=15, permission=GROUP,block=True)
twolun = on_command('进入万世轮回', priority=15, permission=GROUP,block=True)
resetting = on_command('自废修为', priority=15, permission=GROUP,block=True)


@warring_help.handle(parameterless=[Cooldown(at_sender=False)])
async def warring_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    """轮回重修帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    if session_id in cache_help_fk:
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(cache_help_fk[session_id]))
        await warring_help.finish()
    else:
        msg = __warring_help__
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            cache_help_fk[session_id] = pic
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await warring_help.finish()

@lunhui.handle(parameterless=[Cooldown(at_sender=False)])
async def lunhui_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await lunhui.finish()
        
    user_id = user_info['user_id']
    user_msg = sql_message.get_user_info_with_id(user_id) 
    user_name = user_msg['user_name']
    user_root = user_msg['root_type']
    list_level_all = list(jsondata.level_data().keys())
    level = user_info['level']
    
    if user_root == '轮回道果' :
        msg = "道友已是千世轮回之身！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await lunhui.finish()
    
    if user_root == '真·轮回道果' :
        msg = "道友已是万世轮回之身！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await lunhui.finish()
        
    if list_level_all.index(level) >= list_level_all.index(XiuConfig().lunhui_min_level):
        exp = user_msg['exp']
        now_exp = exp - 100
        sql_message.updata_level(user_id, '江湖好手') #重置用户境界
        sql_message.update_levelrate(user_id, 0) #重置突破成功率
        sql_message.update_j_exp(user_id, now_exp) #重置用户修为
        sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        sql_message.updata_user_main_buff(user_id, 0) #重置用户主功法
        sql_message.updata_user_sub_buff(user_id, 0) #重置用户辅修功法
        sql_message.updata_user_sec_buff(user_id, 0) #重置用户神通
        sql_message.update_user_atkpractice(user_id, 0) #重置用户攻修等级
        sql_message.update_root(user_id, 6) #更换轮回灵根
        msg = f"千世轮回磨不灭，重回绝颠谁能敌，恭喜大能{user_name}轮回成功！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await lunhui.finish()
    else:
        msg = f"道友境界未达要求，进入千世轮回的最低境界为{XiuConfig().lunhui_min_level}"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await lunhui.finish()
        
@twolun.handle(parameterless=[Cooldown(at_sender=False)])
async def twolun_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await twolun.finish()
        
    user_id = user_info['user_id']
    user_msg = sql_message.get_user_info_with_id(user_id) 
    user_name = user_msg['user_name']
    user_root = user_msg['root_type']
    list_level_all = list(jsondata.level_data().keys())
    level = user_info['level']
    
    if user_root == '真·轮回道果':
        msg = "道友已是万世轮回之身！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await twolun.finish() 
        
    if user_root != '轮回道果':
        msg = "道友还未轮回过，请先进入千世轮回！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await twolun.finish() 
    
    if list_level_all.index(level) >= list_level_all.index(XiuConfig().twolun_min_level) and user_root == '轮回道果':
        exp = user_msg['exp']
        now_exp = exp - 100
        sql_message.updata_level(user_id, '江湖好手') #重置用户境界
        sql_message.update_levelrate(user_id, 0) #重置突破成功率
        sql_message.update_j_exp(user_id, now_exp) #重置用户修为
        sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        sql_message.update_root(user_id, 7) #更换轮回灵根
        msg = f"万世道果集一身，脱出凡道入仙道，恭喜大能{user_name}万世轮回成功！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await twolun.finish()
    else:
        msg = f"道友境界未达要求，万世轮回的最低境界为{XiuConfig().twolun_min_level}！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await twolun.finish()
        
@resetting.handle(parameterless=[Cooldown(at_sender=False)])
async def resetting_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await resetting.finish()
        
    user_id = user_info['user_id']
    user_msg = sql_message.get_user_info_with_id(user_id) 
    user_name = user_msg['user_name']

        
    if user_msg['level'] in ['搬血境初期', '搬血境中期', '搬血境圆满']:
        exp = user_msg['exp']
        now_exp = exp
        sql_message.updata_level(user_id, '江湖好手') #重置用户境界
        sql_message.update_levelrate(user_id, 0) #重置突破成功率
        sql_message.update_j_exp(user_id, now_exp) #重置用户修为
        sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        msg = f"{user_name}现在是一介凡人了！！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await resetting.finish()
    else:
        msg = f"道友境界未达要求，自废修为的最低境界为搬血境！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await resetting.finish()
        
