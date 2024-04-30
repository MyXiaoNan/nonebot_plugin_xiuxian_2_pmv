from nonebot import on_command, on_fullmatch
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from ..xiuxian_utils.xiuxian_config import XiuConfig, USERRANK
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_utils.data_source import jsondata
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment,
    ActionFailed
)
from ..xiuxian_utils.utils import (
    check_user, get_msg_pic,
    CommandObjectID,
)

sql_message = XiuxianDateManage()  # sql类


lunhui = on_command('进入千世轮回', priority=15, permission=GROUP,block=True)
Twolun = on_command('进入万世轮回', priority=15, permission=GROUP,block=True)
resetting = on_command('自废修为', priority=15, permission=GROUP,block=True)

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
    user_msg = sql_message.get_user_message(user_id) 
    user_name = user_msg['user_name']
    user_root = user_msg['root_type']
    list_level_all = list(jsondata.level_data().keys())
    level = user_info['level']
    
    if user_root == '轮回道果' :
        msg = '道友已是千世轮回之身！'
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await lunhui.finish()
    
    if user_root == '真·轮回道果' :
        msg = '道友已是万世轮回之身！'
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
        msg = '道友境界未达要求无法重修！'
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await lunhui.finish()
        
@Twolun.handle(parameterless=[Cooldown(at_sender=False)])
async def Twolun_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await Twolun.finish()
        
    user_id = user_info['user_id']
    user_msg = sql_message.get_user_message(user_id) 
    user_name = user_msg['user_name']
    user_root = user_msg['root_type']
    list_level_all = list(jsondata.level_data().keys())
    level = user_info['level']
    
    if user_root == '真·轮回道果':
        msg = '道友已是万世轮回之身！'
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await Twolun.finish() 
        
    if user_root != '轮回道果':
        msg = '道友还未轮回过！'
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await Twolun.finish() 
    
    if list_level_all.index(level) >= list_level_all.index(XiuConfig().twolun_min_level) and user_root == '轮回道果':
        exp = user_msg['exp']
        now_exp = exp - 100
        sql_message.updata_level(user_id, '江湖好手') #重置用户境界
        sql_message.update_levelrate(user_id, 0) #重置突破成功率
        sql_message.update_j_exp(user_id, now_exp) #重置用户修为
        sql_message.update_user_hp(user_id)  # 重置用户HP，mp，atk状态
        sql_message.update_root(user_id, 7) #更换轮回灵根
        msg = "万世道果集一身，脱出凡道入仙道，恭喜大能{user_name}万世轮回成功！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await Twolun.finish()
    else:
        msg = '道友境界未达要求！'
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await Twolun.finish()
        
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
    user_msg = sql_message.get_user_message(user_id) 
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
        await Twolun.finish()
    else:
        msg = '道友境界未达要求！'
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await Twolun.finish()
        
