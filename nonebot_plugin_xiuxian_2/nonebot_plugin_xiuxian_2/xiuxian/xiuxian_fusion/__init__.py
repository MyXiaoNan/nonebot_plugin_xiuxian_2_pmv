from nonebot import on_command, on_fullmatch
from ..lay_out import assign_bot, Cooldown ,assign_bot_group
from nonebot.params import CommandArg
from ..xiuxian_config import XiuConfig, JsonConfig
from ..xiuxian2_handle import XiuxianDateManage, XiuxianJsonDate, OtherSet
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment,
    ActionFailed
)
from ..utils import (
    check_user, send_forward_msg,
    get_msg_pic, number_to,
    CommandObjectID,
    Txt2Img
)
sql_message = XiuxianDateManage()  # sql类
import re
from ..item_json import Items
items = Items()
from nonebot.permission import SUPERUSER

tz = on_command('合成天罪', priority=15, permission=GROUP,block=True)
cz = on_command('创造力量', permission=SUPERUSER, priority=15,block=True)

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
        
    in_flag = False  # 判断指令是否正确，道具是否在背包内
    in_flag_2 = False
    goods_id = None
    goods_type = None
    goods_num = None
    wz = "无罪（残缺）"
    yz = "原罪（残缺）"
    
    for back in back_msg:
        if  wz == back.goods_name:
            in_flag = True
            goods_id = back.goods_id
            goods_type = back.goods_type
            goods_num = back.goods_num
            break
        
    for back in back_msg:        
        if  yz == back.goods_name:
            in_flag_2 = True
            goods_id = back.goods_id
            goods_type = back.goods_type
            goods_num = back.goods_num
            break
        
    if not in_flag:
        msg = f"请检查 {wz} 是否在背包内！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await tz.finish()
        
    if not in_flag_2:
        msg = f"请检查 {yz} 是否在背包内！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await tz.finish()
        
    if in_flag and in_flag_2:
        sql_message.update_back_j(user_id, 7098)
        sql_message.update_back_j(user_id, 7099)
        sql_message.send_back(user_id, 7084,'天罪','装备', 1, 0)
        msg = f"道友成功合成了无上仙器天罪！！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await tz.finish()
    
@cz.handle(parameterless=[Cooldown(at_sender=True)])
async def cz_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    give_qq = None  # 艾特的时候存到这里
    msg = args.extract_plain_text().split()
    if not args:
        msg = "请输入正确指令！例如：创造力量 物品 数量"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await cz.finish()
    goods_name = msg[0]
    goods_id = -1
    goods_type = None
    for k, v in items.items.items():
        if goods_name == v['name']:
            goods_id = k
            goods_type = v['type']
            break
        else:
            continue
    
    
    for arg in args:
        if arg.type == "at":
            give_qq = arg.data.get("qq", "")
    if give_qq:
        give_user = sql_message.get_user_message(give_qq)
        if give_user:
            sql_message.send_back(give_qq, goods_id, goods_name, goods_type, 1)# 增加用户道具
            msg = "{}道友获得了系统赠送的{}！".format(give_user.user_name, goods_name)
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await cz.finish()
        else:
            msg = "对方未踏入修仙界，不可赠送！"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await cz.finish()
    else:
        msg = f"请艾特目标用户！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await cz.finish()
    


