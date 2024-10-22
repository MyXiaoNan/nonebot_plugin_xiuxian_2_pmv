from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot.params import CommandArg
from nonebot import on_command
from ..xiuxian_config import XiuConfig
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment
)
from ..xiuxian_utils.item_json import Items
from ..xiuxian_config import convert_rank
from ..xiuxian_back.back_util import get_item_msg
from ..xiuxian_utils.utils import (
    check_user, get_msg_pic, number_to
)
sql_message = XiuxianDateManage()  # sql类
items = Items()

fusion_help_text = f"""
合成帮助:
1.合成 物品名:合成指定的物品。
2.可合成物品 [物品名参数可选] 可以查看当前可合成的所有物品以及相关信息。
""".strip()


fusion = on_command('合成', priority=15, permission=GROUP, block=True)
fusion_help = on_command("合成帮助", permission=GROUP, priority=15, block=True)
available_fusion = on_command('查看可合成物品', priority=15, permission=GROUP, block=True)


@fusion_help.handle(parameterless=[Cooldown(at_sender=False)])
async def fusion_help_(bot: Bot, event: GroupMessageEvent):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    msg = fusion_help_text
    if XiuConfig().img:
        pic = await get_msg_pic(msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await fusion_help.finish()


@fusion.handle(parameterless=[Cooldown(at_sender=False)])
async def fusion_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await fusion.finish()

    user_id = user_info['user_id']
    back_msg = sql_message.get_back_msg(user_id)
    if back_msg is None:
        msg = "道友的背包空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await fusion.finish()

    args_str = args.extract_plain_text().strip()
    equipment_id, equipment = items.get_data_by_item_name(args_str)
    if equipment is None:
        msg = f"未找到可合成的物品：{args_str}"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await fusion.finish()

    fusion_info = equipment.get('fusion', None)
    if not fusion_info:
        msg = f"{equipment['name']} 不是一件可以合成的物品！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await fusion.finish()

    limit = fusion_info.get('limit', None)
    if limit is not None:
        current_amount = 0
        for back in back_msg:
            if back['goods_id'] == int(equipment_id):
                current_amount = back['goods_num']
                break
        if current_amount >= limit:
            msg = f"道友的背包中已有足够数量的 {equipment['name']}，无法再次合成！"
            if XiuConfig().img:
                pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await fusion.finish()

    required_rank = fusion_info.get('need_rank', '江湖好手')
    if convert_rank(user_info['level'])[0] > convert_rank(required_rank)[0]:
        msg = f"道友的境界不足，合成 {equipment['name']} 需要达到 {required_rank}！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await fusion.finish()

    if user_info['exp'] < fusion_info.get('need_exp', 0):
        msg = f"道友的修为不足，合成 {equipment['name']} 需要修为 {fusion_info.get('need_exp', 0)}！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await fusion.finish()

    required_stone = int(fusion_info.get('need_stone', 0))
    if user_info['stone'] < required_stone:
        msg = f"道友的灵石不足，合成 {equipment['name']} 需要 {number_to(required_stone)} 枚灵石呢！"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await fusion.finish()

    # 检查数量
    needed_items = fusion_info.get('need_item', {})
    missing_items = []
    for item_id, amount_needed in needed_items.items():
        total_amount = 0
        for back in back_msg:
            if back['goods_id'] == int(item_id):
                total_amount += back['goods_num']
        if total_amount < amount_needed:
            missing_items.append((item_id, amount_needed - total_amount))

    if missing_items:
        missing_names = [f"{amount_needed} 个 {items.get_data_by_item_id(int(item_id))['name']}" for item_id, amount_needed in missing_items]
        msg = "道友还缺少：\n" + "\n".join(missing_names)
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await fusion.finish()

    sql_message.update_user_stone(user_id, required_stone, 2)
    for item_id, amount_needed in needed_items.items():
        sql_message.update_back_j(user_id, int(item_id), amount_needed)

    sql_message.send_back(user_id, int(equipment_id), equipment['name'], equipment['type'], 1, 1)

    item_type = equipment.get('type', '物品')
    msg = f"道友成功合成了{item_type}: {equipment['name']}！！"
    if XiuConfig().img:
        pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await fusion.finish()


@available_fusion.handle(parameterless=[Cooldown(at_sender=False)])
async def available_fusion_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    args_str = args.extract_plain_text().strip()

    if args_str:
        equipment_id, equipment = items.get_data_by_item_name(args_str)
        if equipment and 'fusion' in equipment:
            msg = get_item_msg(int(equipment_id))
        else:
            msg = f"未找到可合成的物品：{args_str}"
    else:
        fusion_items = items.get_fusion_items()
        if not fusion_items:
            msg = "目前没有可合成的物品。"
        else:
            msg = "可合成的物品如下：\n" + "\n".join(fusion_items)

    if XiuConfig().img:
        pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await available_fusion.finish()
