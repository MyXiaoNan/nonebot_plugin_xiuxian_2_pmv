import asyncio
import random
from datetime import datetime
from nonebot import on_command, require, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    Message,
    GroupMessageEvent,
    MessageSegment,
    GROUP_ADMIN,
    GROUP_OWNER,
    ActionFailed
)
from ..xiuxian_utils.lay_out import assign_bot, assign_bot_group, Cooldown, CooldownIsolateLevel
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from .back_util import (
    get_user_main_back_msg, check_equipment_can_use,
    get_use_equipment_sql, get_shop_data, save_shop,
    get_item_msg, get_item_msg_rank, check_use_elixir,
    get_use_jlq_msg, get_no_use_equipment_sql
)
from .backconfig import get_auction_config, savef_auction, remove_auction_item
from ..xiuxian_utils.item_json import Items
from ..xiuxian_utils.utils import (
    check_user, get_msg_pic, 
    send_msg_handler, CommandObjectID,
    Txt2Img, number_to
)
from ..xiuxian_utils.xiuxian2_handle import (
    XiuxianDateManage, get_weapon_info_msg, get_armor_info_msg,
    get_sec_msg, get_main_info_msg, get_sub_info_msg, UserBuffDate
)
from ..xiuxian_config import XiuConfig, convert_rank

items = Items()
config = get_auction_config()
groups = config['open']  # list，群交流会使用
auction = {}
AUCTIONSLEEPTIME = 120  # 拍卖初始等待时间（秒）
cache_help = {}
auction_offer_flag = False  # 拍卖标志
AUCTIONOFFERSLEEPTIME = 30  # 每次拍卖增加拍卖剩余的时间（秒）
auction_offer_time_count = 0  # 计算剩余时间
auction_offer_all_count = 0  # 控制线程等待时间
auction_time_config = config['拍卖会定时参数'] # 定时配置
sql_message = XiuxianDateManage()  # sql类
# 定时任务
set_auction_by_scheduler = require("nonebot_plugin_apscheduler").scheduler
reset_day_num_scheduler = require("nonebot_plugin_apscheduler").scheduler

goods_re_root = on_command("炼金", priority=6, permission=GROUP, block=True)
shop = on_command("坊市查看", aliases={"查看坊市"}, priority=8, permission=GROUP, block=True)
auction_view = on_command("拍卖品查看", aliases={"查看拍卖品"}, priority=8, permission=GROUP, block=True)
shop_added = on_command("坊市上架", priority=10, permission=GROUP, block=True)
shop_added_by_admin = on_command("系统坊市上架", priority=5, permission=SUPERUSER, block=True)
shop_off = on_command("坊市下架", priority=5, permission=GROUP, block=True)
shop_off_all = on_fullmatch("清空坊市", priority=3, permission=SUPERUSER, block=True)
main_back = on_command('我的背包', aliases={'我的物品'}, priority=10, permission=GROUP, block=True)
use = on_command("使用", priority=15, permission=GROUP, block=True)
no_use_zb = on_command("换装", priority=5, permission=GROUP, block=True)
buy = on_command("坊市购买", priority=5, block=True)
auction_add = on_command("提交拍卖品", aliases={"拍卖品提交"}, priority=10, permission=GROUP, block=True)
auction_withdraw = on_command("撤回拍卖品", aliases={"拍卖品撤回"}, priority=10, permission=GROUP, block=True)
set_auction = on_command("群拍卖会", priority=4, permission=GROUP and (SUPERUSER | GROUP_ADMIN | GROUP_OWNER), block=True)
creat_auction = on_fullmatch("举行拍卖会", priority=5, permission=GROUP and SUPERUSER, block=True)
offer_auction = on_command("拍卖", priority=5, permission=GROUP, block=True)
back_help = on_command("背包帮助", aliases={"坊市帮助"}, priority=8, permission=GROUP, block=True)
xiuxian_sone = on_fullmatch("灵石", priority=4, permission=GROUP, block=True)
chakan_wupin = on_command("查看修仙界物品", priority=25, permission=GROUP, block=True)

__back_help__ = """
指令：
1、我的背包、我的物品:查看自身背包前196个物品的信息
2、使用+物品名字：使用物品,可批量使用
3、换装+装备名字：卸载目标装备
4、坊市购买+物品编号:购买坊市内的物品，可批量购买
5、坊市查看、查看坊市:查询坊市在售物品
6、查看拍卖品、拍卖品查看:查询将在拍卖品拍卖的玩家物品
7、坊市上架:坊市上架 物品 金额，上架背包内的物品,最低金额50w，可批量上架
8、提交拍卖品:提交拍卖品 物品 金额，上架背包内的物品,最低金额随意，可批量上架(需要超管重启机器人)
9、系统坊市上架:系统坊市上架 物品 金额，上架任意存在的物品，超管权限
10、坊市下架+物品编号：下架坊市内的物品，管理员和群主可以下架任意编号的物品！
11、群交流会开启、关闭:开启拍卖行功能，管理员指令，注意：会在机器人所在的全部已开启此功能的群内通报拍卖消息
12、拍卖+金额：对本次拍卖会的物品进行拍卖
13、炼金+物品名字：将物品炼化为灵石,支持批量炼金和绑定丹药炼金
14、背包帮助:获取背包帮助指令
15、查看修仙界物品:支持类型【功法|神通|丹药|合成丹药|法器|防具】
16、清空坊市:清空本群坊市,管理员权限
非指令：
1、定时生成拍卖会,每天{}点每整点生成一场拍卖会
""".format(auction_time_config['hours']).strip()


# 重置丹药每日使用次数
@reset_day_num_scheduler.scheduled_job("cron", hour=0, minute=0, )
async def reset_day_num_scheduler_():
    sql_message.day_num_reset()
    logger.opt(colors=True).info("<green>每日丹药使用次数重置成功！</green>")


# 定时任务生成拍卖会
@set_auction_by_scheduler.scheduled_job("cron", hour=auction_time_config['hours'], minute=auction_time_config['minutes'])
async def set_auction_by_scheduler_():
    global auction, auction_offer_flag, auction_offer_all_count, auction_offer_time_count
    if groups:
        if auction:
            logger.opt(colors=True).info("<green>本群已存在一场拍卖会，已清除！</green>")
            auction = {}

    auction_items = []
    try:
        # 获取用户拍卖品
        user_auction_id_list = get_user_auction_id_list()
        for auction_id in user_auction_id_list:
            user_auction_info = get_user_auction_price_by_id(auction_id)
            auction_items.append((auction_id, user_auction_info['quantity'], user_auction_info['start_price'], True))

        # 获取系统拍卖品
        auction_id_list = get_auction_id_list()
        auction_count = random.randint(3, 8)  # 随机挑选系统拍卖品数量
        auction_ids = random.sample(auction_id_list, auction_count)
        for auction_id in auction_ids:
            item_info = items.get_data_by_item_id(auction_id)
            item_quantity = 1
            if item_info['type'] in ['神物', '丹药']:
                item_quantity = random.randint(1, 3) # 如果是丹药的话随机挑1-3个
            auction_items.append((auction_id, item_quantity, get_auction_price_by_id(auction_id)['start_price'], False))
    except LookupError:
        logger.opt(colors=True).info("<red>获取不到拍卖物品的信息，请检查配置文件！</red>")
        return
    
    # 打乱拍卖品顺序
    random.shuffle(auction_items)
    
    logger.opt(colors=True).info("<red>野生的大世界定时拍卖会出现了！！！，请管理员在这个时候不要重启机器人</red>")
    msg = "大世界定时拍卖会出现了！！！\n"
    msg = "请各位道友稍作准备，拍卖即将开始...\n"
    msg += "本场拍卖会共有{}件物品，将依次拍卖，分别是：\n".format(len(auction_items))
    for idx, (auction_id, item_quantity, start_price, is_user_auction) in enumerate(auction_items):
        item_name = items.get_data_by_item_id(auction_id)['name']
        if is_user_auction:
            owner_info = sql_message.get_user_info_with_id(get_user_auction_price_by_id(auction_id)['user_id'])
            owner_name = owner_info['user_name']
            msg += f"{idx + 1}号：{item_name}x{item_quantity}（由{owner_name}道友提供）\n"
        else:
            msg += f"{idx + 1}号：{item_name}x{item_quantity}（由拍卖场提供）\n"

    for gid in groups:
        bot = await assign_bot_group(group_id=gid)
        try:
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(gid), message=msg)
        except ActionFailed:  # 发送群消息失败
            continue
    
    auction_results = []  # 存储拍卖结果
    for i, (auction_id, item_quantity, start_price, is_user_auction) in enumerate(auction_items):
        auction_info = items.get_data_by_item_id(auction_id)

        auction = {
            'id': auction_id,
            'user_id': 0,
            'now_price': start_price,
            'name': auction_info['name'],
            'type': auction_info['type'],
            'quantity': item_quantity,
            'start_time': datetime.now(),
            'group_id': 0
        }

        
        if i + 1 == len(auction_items):
            msg = "最后一件拍卖品为：\n{}\n".format(get_auction_msg(auction_id))
        else:
            msg = "第{}件拍卖品为：\n{}\n".format(i + 1, get_auction_msg(auction_id))
        msg += "\n底价为{}，加价不少于{}".format(start_price, int(start_price * 0.05))
        msg += "\n竞拍时间为:{}秒，请诸位道友发送 拍卖+金额 来进行拍卖吧！".format(AUCTIONSLEEPTIME)

        if auction['quantity'] > 1:
            msg += "\n注意：拍卖品共{}件，最终价为{} * 成交价。\n".format(auction['quantity'], auction['quantity'])

        if i + 1 < len(auction_items):
            next_item_name = items.get_data_by_item_id(auction_items[i + 1][0])['name']
            msg += "\n下一件拍卖品为：{}，请心仪的道友提前开始准备吧！".format(next_item_name)

        for gid in groups:
            bot = await assign_bot_group(group_id=gid)
            try:
                if XiuConfig().img:
                    pic = await get_msg_pic(msg)
                    await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
                else:
                    await bot.send_group_msg(group_id=int(gid), message=msg)
            except ActionFailed:  # 发送群消息失败
                continue

     
        remaining_time = AUCTIONSLEEPTIME
        while remaining_time > 0:
            await asyncio.sleep(10)
            remaining_time -= 10


        while auction_offer_flag:  # 有人拍卖
            if auction_offer_all_count == 0:
                auction_offer_flag = False
                break

            logger.opt(colors=True).info("<green>有人拍卖，本次等待时间：{}秒</green>".format(auction_offer_all_count * AUCTIONOFFERSLEEPTIME))
            first_time = auction_offer_all_count * AUCTIONOFFERSLEEPTIME
            auction_offer_all_count = 0
            auction_offer_flag = False
            await asyncio.sleep(first_time)
            logger.opt(colors=True).info("<green>总计等待时间{}秒，当前拍卖标志：{}，本轮等待时间：{}</green>".format(auction_offer_time_count * AUCTIONOFFERSLEEPTIME, auction_offer_flag, first_time))

        logger.opt(colors=True).info("<green>等待时间结束，总计等待时间{}秒</green>".format(auction_offer_time_count * AUCTIONOFFERSLEEPTIME))
        if auction['user_id'] == 0:
            msg = "很可惜，{}流拍了\n".format(auction['name'])
            if i + 1 == len(auction_items):
                msg += "本场拍卖会到此结束，开始整理拍卖会结果，感谢各位道友参与！"
                
            for gid in groups:
                bot = await assign_bot_group(group_id=gid)
                try:
                    if XiuConfig().img:
                        pic = await get_msg_pic(msg)
                        await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
                    else:
                        await bot.send_group_msg(group_id=int(gid), message=msg)
                except ActionFailed:  # 发送群消息失败
                    continue
            auction_results.append((auction_id, None, auction['group_id'], auction_info['type'], auction['now_price'], auction['quantity']))
            auction = {}
            continue
        
        user_info = sql_message.get_user_info_with_id(auction['user_id'])
        msg = "(拍卖锤落下)！！！\n"
        msg += "恭喜来自群{}的{}道友成功拍下：{}-{}x{}，将在拍卖会结算后送到您手中。\n".format(
            auction['group_id'], user_info['user_name'], auction['type'], auction['name'], auction['quantity'])
        if i + 1 == len(auction_items):
            msg += "本场拍卖会到此结束，开始整理拍卖会结果，感谢各位道友参与！"

        auction_results.append((auction_id, user_info['user_id'], auction['group_id'], 
                                auction_info['type'], auction['now_price'], auction['quantity']))
        auction = {}
        auction_offer_time_count = 0
        for gid in groups:

            bot = await assign_bot_group(group_id=gid)
            try:
                if XiuConfig().img:
                    pic = await get_msg_pic(msg)
                    await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
                else:
                    await bot.send_group_msg(group_id=int(gid), message=msg)
            except ActionFailed:  # 发送群消息失败
                continue

        await asyncio.sleep(random.randint(5, 30))

    # 拍卖会结算
    logger.opt(colors=True).info("<green>野生的大世界定时拍卖会结束了！！！</green>")
    end_msg = "本场拍卖会结束！感谢各位道友的参与。\n拍卖结果整理如下：\n"
    for idx, (auction_id, user_id, group_id, item_type, final_price, quantity) in enumerate(auction_results):
        item_name = items.get_data_by_item_id(auction_id)['name']
        final_user_info = sql_message.get_user_info_with_id(user_id)
        if user_id:
            sql_message.update_ls(user_id, int(final_price) * quantity, 2)
            sql_message.send_back(user_id, auction_id, item_name, item_type, quantity)
            end_msg += "{}号拍卖品：{}x{}由群{}的{}道友成功拍下\n".format(
                idx + 1, item_name, quantity, group_id, final_user_info['user_name']
            )

            user_auction_info = get_user_auction_price_by_id(auction_id)
            if user_auction_info:
                seller_id = user_auction_info['user_id']
                auction_earnings = int(final_price) * quantity * 0.7
                sql_message.update_ls(seller_id, auction_earnings, 1)

            remove_auction_item(auction_id)

            auction = {}
            auction_offer_time_count = 0
        else:
            end_msg += "{}号拍卖品：{}x{} - 流拍了\n".format(
                idx + 1, item_name, quantity
            )

    for gid in groups:
        bot = await assign_bot_group(group_id=gid)
        try:
            if XiuConfig().img:
                pic = await get_msg_pic(end_msg)
                await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(gid), message=end_msg)
        except ActionFailed:  # 发送群消息失败
            continue

    return


@back_help.handle(parameterless=[Cooldown(at_sender=False)])
async def back_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    """背包帮助"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    if session_id in cache_help:
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(cache_help[session_id]))
        await back_help.finish()
    else:
        msg = __back_help__
        title = ''
        font_size = 32
        img = Txt2Img(font_size)
        if XiuConfig().img:
            pic = await img.save(title,msg)
            cache_help[session_id] = pic
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await back_help.finish()


@xiuxian_sone.handle(parameterless=[Cooldown(at_sender=False)])
async def xiuxian_sone_(bot: Bot, event: GroupMessageEvent):
    """我的灵石信息"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await xiuxian_sone.finish()
    msg = "当前灵石：{}({})".format((user_info['stone']), number_to(user_info['stone']))
    if XiuConfig().img:
        pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await xiuxian_sone.finish()


buy_lock = asyncio.Lock()


@buy.handle(parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GROUP)])
async def buy_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """购物"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    async with buy_lock:
        isUser, user_info, msg = check_user(event)
        if not isUser:
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await buy.finish()
        user_id = user_info['user_id']
        group_id = str(event.group_id)
        shop_data = get_shop_data(group_id)
        
        if shop_data[group_id] == {}:
            msg = "坊市目前空空如也！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await buy.finish()
        input_args = args.extract_plain_text().strip().split() # 购买参数
        # 确定物品的价格和数量
        if len(input_args) < 1:
            # 没有输入任何参数或只输入了"坊市购买"而没有后续的物品编号和数量
            msg = "请输入正确指令！例如：坊市购买 物品编号 数量"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await buy.finish()
        else:
            try:
                arg = int(input_args[0]) # 购买编号
                if len(input_args) == 0:
                    # 没有输入任何参数
                    msg = "请输入正确指令！例如：坊市购买 物品 数量"

                # 取出商品信息，检查库存
                goods_info = shop_data[group_id].get(str(arg))
                if not goods_info:
                    raise ValueError("编号对应的商品不存在！")

                purchase_quantity = int(input_args[1]) if len(input_args) > 1 else 1  # 购买数量，没指定的话默认为1
                if purchase_quantity <= 0:
                    raise ValueError("购买数量必须是正数！")
    
                if 'stock' in goods_info and purchase_quantity > goods_info['stock']:
                 # 如果商品有库存限制，且购买数量超过库存，则抛出错误
                    raise ValueError("购买数量超过库存限制！")
    
            except ValueError as e:
                msg = "{}！".format(str(e))
                if XiuConfig().img:
                    pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                    await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
                else:
                    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
                await buy.finish()
        shop_user_id = shop_data[group_id][str(arg)]['user_id']
        goods_price = goods_info['price'] * purchase_quantity  # 总价格
        goods_stock = goods_info.get('stock', 1)  # 如果没有指定数量，默认为1
        if user_info['stone'] < goods_price:
            msg = '没钱还敢来买东西！！'
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await buy.finish()
        elif int(user_id) == int(shop_data[group_id][str(arg)]['user_id']):
            msg = "道友自己的东西就不要自己购买啦！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await buy.finish()
        elif purchase_quantity > goods_stock and shop_user_id != 0:
            msg = "库存不足，无法购买所需数量！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        else:
            shop_goods_name = shop_data[group_id][str(arg)]['goods_name']
            shop_user_name = shop_data[group_id][str(arg)]['user_name']
            shop_goods_id = shop_data[group_id][str(arg)]['goods_id']
            shop_goods_type = shop_data[group_id][str(arg)]['goods_type']
            sql_message.update_ls(user_id, goods_price, 2)
            sql_message.send_back(user_id, shop_goods_id, shop_goods_name, shop_goods_type, purchase_quantity)
            save_shop(shop_data)

            if shop_user_id == 0:  # 0为系统
                msg = "道友成功购买{}个{}，消耗灵石{}枚！".format(purchase_quantity, shop_goods_name, goods_price)
            else:
                # 更新坊市物品库存
                goods_info['stock'] -= purchase_quantity
                if goods_info['stock'] <= 0:
                    del shop_data[group_id][str(arg)]  # 如果库存为0，则从坊市中移除该物品
                else:
                    shop_data[group_id][str(arg)] = goods_info # 更新库存
                service_charge = int(goods_price * 0.1)  # 手续费10%
                give_stone = goods_price - service_charge
                msg = "道友成功购买{}个{}道友寄售的{}，消耗灵石{}枚,坊市收取手续费：{}枚灵石！".format(purchase_quantity, shop_user_name, shop_goods_name, goods_price, service_charge)
                sql_message.update_ls(shop_user_id, give_stone, 1)
            shop_data[group_id] = reset_dict_num(shop_data[group_id])
            save_shop(shop_data)
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await buy.finish()


@shop.handle(parameterless=[Cooldown(at_sender=False)])
async def shop_(bot: Bot, event: GroupMessageEvent):
    """坊市查看"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop.finish()

    group_id = str(event.group_id)
    shop_data = get_shop_data(group_id)
    data_list = []
    if shop_data[group_id] == {}:
        msg = "坊市目前空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop.finish()

    for k, v in shop_data[group_id].items():
        msg = "编号：{}\n".format(k)
        msg += "{}".format(v['desc'])
        msg += "\n价格：{}枚灵石\n".format(v['price'])
        if v['user_id'] != 0:
            msg += "拥有人：{}道友\n".format(v['user_name'])
            msg += "数量：{}\n".format(v['stock'])
        else:
            msg += "系统出售\n"
            msg += "数量：无限\n"
        data_list.append(msg)
    await send_msg_handler(bot, event, '坊市', bot.self_id, data_list)
    await shop.finish()


@shop_added_by_admin.handle(parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GROUP, parallel=1)])
async def shop_added_by_admin_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """系统上架坊市"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    args = args.extract_plain_text().split()
    if not args:
        msg = "请输入正确指令！例如：系统坊市上架 物品 金额"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added_by_admin.finish()
    goods_name = args[0]
    goods_id = -1
    for k, v in items.items.items():
        if goods_name == v['name']:
            goods_id = k
            break
        else:
            continue
    if goods_id == -1:
        msg = "不存在物品：{}的信息，请检查名字是否输入正确！".format(goods_name)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added_by_admin.finish()
    price = None
    try:
        price = args[1]
    except LookupError:
        msg = "请输入正确指令！例如：系统坊市上架 物品 金额"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added_by_admin.finish()
    try:
        price = int(price)
        if price < 0:
            msg = "请不要设置负数！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await shop_added_by_admin.finish()
    except LookupError:
        msg = "请输入正确的金额！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added_by_admin.finish()

    try:
        var = args[2]
        msg = "请输入正确指令！例如：系统坊市上架 物品 金额"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added_by_admin.finish()
    except LookupError:
        pass

    group_id = str(event.group_id)
    shop_data = get_shop_data(group_id)
    if shop_data == {}:
        shop_data[group_id] = {}
    goods_info = items.get_data_by_item_id(goods_id)

    id_ = len(shop_data[group_id]) + 1
    shop_data[group_id][id_] = {}
    shop_data[group_id][id_]['user_id'] = 0
    shop_data[group_id][id_]['goods_name'] = goods_name
    shop_data[group_id][id_]['goods_id'] = goods_id
    shop_data[group_id][id_]['goods_type'] = goods_info['type']
    shop_data[group_id][id_]['desc'] = get_item_msg(goods_id)
    shop_data[group_id][id_]['price'] = price
    shop_data[group_id][id_]['user_name'] = '系统'
    save_shop(shop_data)
    msg = "物品：{}成功上架坊市，金额：{}枚灵石！".format(goods_name, price)
    if XiuConfig().img:
        pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await shop_added_by_admin.finish()


@shop_added.handle(parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GROUP)])
async def shop_added_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """用户上架坊市"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()
    user_id = user_info['user_id']
    args = args.extract_plain_text().split()
    goods_name = args[0] if len(args) > 0 else None
    price_str = args[1] if len(args) > 1 else "500000"  # 默认为500000
    quantity_str = args[2] if len(args) > 2 else "1"  # 默认为1
    if len(args) == 0:
        # 没有输入任何参数
        msg = "请输入正确指令！例如：坊市上架 物品 可选参数为(金额 数量)"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()
    elif len(args) == 1:
        # 只提供了物品名称
        goods_name, price_str = args[0], "500000"
        quantity_str = "1"
    elif len(args) == 2:
        # 提供了物品名称和价格
        goods_name, price_str = args[0], args[1]
        quantity_str = "1"
    else:
        # 提供了物品名称、价格和数量
        goods_name, price_str, quantity_str = args[0], args[1], args[2]

    back_msg = sql_message.get_back_msg(user_id)  # 背包sql信息,dict
    if back_msg is None:
        msg = "道友的背包空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()
    in_flag = False  # 判断指令是否正确，道具是否在背包内
    goods_id = None
    goods_type = None
    goods_state = None
    goods_num = None
    goods_bind_num = None
    for back in back_msg:
        if goods_name == back['goods_name']:
            in_flag = True
            goods_id = back['goods_id']
            goods_type = back['goods_type']
            goods_state = back['state']
            goods_num = back['goods_num']
            goods_bind_num = back['bind_num']
            break
    if not in_flag:
        msg = "请检查该道具 {} 是否在背包内！".format(goods_name)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()
    price = None
    
    # 解析价格
    try:
        price = int(price_str)
        if price <= 0:
            raise ValueError("价格必须为正数！")
    except ValueError as e:
        msg = "请输入正确的金额: {}".format(str(e))
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()
    # 解析数量
    try:
        quantity = int(quantity_str)
        if quantity <= 0 or quantity > goods_num:  # 检查指定的数量是否合法
            raise ValueError("数量必须为正数或者小于等于你拥有的物品数!")
    except ValueError as e:
        msg = "请输入正确的数量: {}".format(str(e))
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()
    price = max(price, 500000)  # 最低价格为50w
    if goods_type == "装备" and int(goods_state) == 1 and int(goods_num) == 1:
        msg = "装备：{}已经被道友装备在身，无法上架！".format(goods_name)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()

    if int(goods_num) <= int(goods_bind_num):
        msg = "该物品是绑定物品，无法上架！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()
    if goods_type == "聚灵旗" or goods_type == "炼丹炉":
        if user_info['root'] == "器师" :
            pass
        else:
            msg = "道友职业无法上架！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await shop_added.finish() 

    group_id = str(event.group_id)
    shop_data = get_shop_data(group_id)

    num = 0
    for k, v in shop_data[group_id].items():
        if str(v['user_id']) == str(user_info['user_id']):
            num += 1
        else:
            pass
    if num >= 5 :
        msg = "每人只可上架五个物品！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_added.finish()

    if shop_data == {}:
        shop_data[group_id] = {}
    id_ = len(shop_data[group_id]) + 1
    shop_data[group_id][id_] = {
        'user_id': user_id,
        'goods_name': goods_name,
        'goods_id': goods_id,
        'goods_type': goods_type,
        'desc': get_item_msg(goods_id),
        'price': price,
        'user_name': user_info['user_name'],
        'stock': quantity,  # 物品数量
    }
    sql_message.update_back_j(user_id, goods_id, num = quantity)
    save_shop(shop_data)
    msg = "物品：{}成功上架坊市，金额：{}枚灵石，数量{}！".format(goods_name, price, quantity)
    if XiuConfig().img:
        pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await shop_added.finish()


@goods_re_root.handle(parameterless=[Cooldown(at_sender=False)])
async def goods_re_root_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """炼金"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await goods_re_root.finish()
    user_id = user_info['user_id']
    args = args.extract_plain_text().split()
    if args is None:
        msg = "请输入要炼化的物品！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await goods_re_root.finish()
    goods_name = args[0]
    back_msg = sql_message.get_back_msg(user_id)  # 背包sql信息,list(back)
    if back_msg is None:
        msg = "道友的背包空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await goods_re_root.finish()
    in_flag = False  # 判断指令是否正确，道具是否在背包内
    goods_id = None
    goods_type = None
    goods_state = None
    goods_num = None
    for back in back_msg:
        if goods_name == back['goods_name']:
            in_flag = True
            goods_id = back['goods_id']
            goods_type = back['goods_type']
            goods_state = back['state']
            goods_num = back['goods_num']
            break
    if not in_flag:
        msg = "请检查该道具 {} 是否在背包内！".format(goods_name)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await goods_re_root.finish()

    if goods_type == "装备" and int(goods_state) == 1 and int(goods_num) == 1:
        msg = "装备：{}已经被道友装备在身，无法炼金！".format(goods_name)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await goods_re_root.finish()

    if get_item_msg_rank(goods_id) == 520:
        msg = "此类物品不支持！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await goods_re_root.finish()
    try:
        if 1 <= int(args[1]) <= int(goods_num):
            num = int(args[1])
    except:
            num = 1 
    price = int(6000000 - get_item_msg_rank(goods_id) * 100000) * num
    if price <= 0:
        msg = "物品：{}炼金失败，凝聚{}枚灵石，记得通知晓楠！".format(goods_name, price)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await goods_re_root.finish()

    sql_message.update_back_j(user_id, goods_id, num=num)
    sql_message.update_ls(user_id, price, 1)
    msg = "物品：{} 数量：{} 炼金成功，凝聚{}枚灵石！".format(goods_name, num, price)
    if XiuConfig().img:
        pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await goods_re_root.finish()


@shop_off.handle(parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GROUP, parallel=1)])
async def shop_off_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """下架商品"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_off.finish()
    user_id = user_info['user_id']
    group_id = str(event.group_id)
    shop_data = get_shop_data(group_id)
    if shop_data[group_id] == {}:
        msg = "坊市目前空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_off.finish()

    arg = args.extract_plain_text().strip()
    shop_user_name = shop_data[group_id][str(arg)]['user_name']
    try:
        arg = int(arg)
        if arg <= 0 or arg > len(shop_data[group_id]):
            msg = "请输入正确的编号！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await shop_off.finish()
    except ValueError:
        msg = "请输入正确的编号！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_off.finish()

    if shop_data[group_id][str(arg)]['user_id'] == user_id:
        sql_message.send_back(user_id, shop_data[group_id][str(arg)]['goods_id'],
                              shop_data[group_id][str(arg)]['goods_name'], shop_data[group_id][str(arg)]['goods_type'],
                              shop_data[group_id][str(arg)]['stock'])
        msg = "成功下架物品：{}！".format(shop_data[group_id][str(arg)]['goods_name'])
        del shop_data[group_id][str(arg)]
        shop_data[group_id] = reset_dict_num(shop_data[group_id])
        save_shop(shop_data)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_off.finish()

    elif event.sender.role == "admin" or event.sender.role == "owner" or event.get_user_id() in bot.config.superusers:
        if shop_data[group_id][str(arg)]['user_id'] == 0:  # 这么写为了防止bot.send发送失败，不结算
            msg = "成功下架物品：{}！".format(shop_data[group_id][str(arg)]['goods_name'])
            del shop_data[group_id][str(arg)]
            shop_data[group_id] = reset_dict_num(shop_data[group_id])
            save_shop(shop_data)
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await shop_off.finish()
        else:
            sql_message.send_back(shop_data[group_id][str(arg)]['user_id'], shop_data[group_id][str(arg)]['goods_id'],
                                  shop_data[group_id][str(arg)]['goods_name'],
                                  shop_data[group_id][str(arg)]['goods_type'], shop_data[group_id][str(arg)]['stock'])
            msg1 = "道友上架的{}个{}已被管理员{}下架！".format(shop_data[group_id][str(arg)]['stock'], 
                                                 shop_data[group_id][str(arg)]['goods_name'], user_info['user_name'])
            del shop_data[group_id][str(arg)]
            shop_data[group_id] = reset_dict_num(shop_data[group_id])
            save_shop(shop_data)
            try:
                if XiuConfig().img:
                    pic = await get_msg_pic(f"@{shop_user_name}\n" + msg1)
                    await bot.send(event=event, message=MessageSegment.image(pic))
                else:
                    await bot.send(event=event, message=Message(msg1))
            except ActionFailed:
                pass

    else:
        msg = "这东西不是你的！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_off.finish()


@auction_withdraw.handle(parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GROUP)])
async def auction_withdraw_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """用户撤回拍卖品"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_withdraw.finish()

    group_id = str(event.group_id)
    if group_id not in groups:
        msg = '本群尚未开启拍卖会功能，请联系管理员开启！'
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await auction_withdraw.finish()

    config = get_auction_config()
    user_auctions = config.get('user_auctions', [])

    if not user_auctions:
        msg = "拍卖会目前没有道友提交的物品！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_withdraw.finish()

    arg = args.extract_plain_text().strip()
    auction_index = int(arg) - 1
    if auction_index < 0 or auction_index >= len(user_auctions):
        msg = "请输入正确的编号"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_withdraw.finish()

    auction = user_auctions[auction_index]
    goods_name, details = list(auction.items())[0]
    if details['user_id'] != user_info['user_id']:
        msg = "这不是你的拍卖品！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_withdraw.finish()

    back_msg = sql_message.get_back_msg(details['user_id'])
    goods_type = None
    for back in back_msg:
        if goods_name == back['goods_name']:
            goods_type = back['goods_type']
            break

    if not goods_type:
        msg = "物品类型未找到，无法撤回拍卖品：{}".format(goods_name)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_withdraw.finish()

    sql_message.send_back(details['user_id'], details['id'], goods_name, goods_type, details['quantity'])
    user_auctions.pop(auction_index)
    config['user_auctions'] = user_auctions
    savef_auction(config)

    msg = "成功撤回拍卖品：{}x{}！".format(goods_name, details['quantity'])
    if XiuConfig().img:
        pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)

    await auction_withdraw.finish()




@main_back.handle(parameterless=[Cooldown(cd_time=10, at_sender=False)])
async def main_back_(bot: Bot, event: GroupMessageEvent):
    """我的背包
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await main_back.finish()
    user_id = user_info['user_id']
    msg = get_user_main_back_msg(user_id)

    if len(msg) >= 98: #背包更新
        # 将第一条消息和第二条消息合并为一条消息
        msg1 = [f"{user_info['user_name']}的背包，持有灵石：{number_to(user_info['stone'])}枚"] + msg[:98]
        msg2 = [f"{user_info['user_name']}的背包，持有灵石：{number_to(user_info['stone'])}枚"] + msg[98:]
        try:
            await send_msg_handler(bot, event, '背包', bot.self_id, msg1)
            if msg2:
                # 如果有第三条及以后的消息，需要等待一段时间再发送，避免触发限制
                await asyncio.sleep(1)
                await send_msg_handler(bot, event, '背包', bot.self_id, msg2)
        except ActionFailed:
            await main_back.finish("查看背包失败!", reply_message=True)
    else:
        msg = [f"{user_info['user_name']}的背包，持有灵石：{number_to(user_info['stone'])}枚"] + msg
        try:
            await send_msg_handler(bot, event, '背包', bot.self_id, msg)
        except ActionFailed:
            await main_back.finish("查看背包失败!", reply_message=True)

    await main_back.finish()



@no_use_zb.handle(parameterless=[Cooldown(at_sender=False)])
async def no_use_zb_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """卸载物品（只支持装备）
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await no_use_zb.finish()
    user_id = user_info['user_id']
    arg = args.extract_plain_text().strip()

    back_msg = sql_message.get_back_msg(user_id)  # 背包sql信息,list(back)
    if back_msg is None:
        msg = "道友的背包空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await no_use_zb.finish()
    in_flag = False  # 判断指令是否正确，道具是否在背包内
    goods_id = None
    goods_type = None
    for back in back_msg:
        if arg == back['goods_name']:
            in_flag = True
            goods_id = back['goods_id']
            goods_type = back['goods_type']
            break
    if not in_flag:
        msg = "请检查该道具 {} 是否在背包内！".format(arg)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await no_use_zb.finish()

    if goods_type == "装备":
        if not check_equipment_can_use(user_id, goods_id):
            sql_str, item_type = get_no_use_equipment_sql(user_id, goods_id)
            for sql in sql_str:
                sql_message.update_back_equipment(sql)
            if item_type == "法器":
                sql_message.updata_user_faqi_buff(user_id, 0)
            if item_type == "防具":
                sql_message.updata_user_armor_buff(user_id, 0)
            msg = "成功卸载装备{}！".format(arg)
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await no_use_zb.finish()
        else:
            msg = "装备没有被使用，无法卸载！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await no_use_zb.finish()
    else:
        msg = "目前只支持卸载装备！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await no_use_zb.finish()


@use.handle(parameterless=[Cooldown(at_sender=False)])
async def use_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """使用物品
    ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
    "remake", "day_num", "all_num", "action_time", "state"]
    """
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()
    user_id = user_info['user_id']
    args = args.extract_plain_text().split()
    arg = args[0]  # 
    back_msg = sql_message.get_back_msg(user_id)  # 背包sql信息,dict
    if back_msg is None:
        msg = "道友的背包空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()
    in_flag = False  # 判断指令是否正确，道具是否在背包内
    goods_id = None
    goods_type = None
    goods_num = None
    for back in back_msg:
        if arg == back['goods_name']:
            in_flag = True
            goods_id = back['goods_id']
            goods_type = back['goods_type']
            goods_num = back['goods_num']
            break
    if not in_flag:
        msg = "请检查该道具 {} 是否在背包内！".format(arg)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()

    if goods_type == "装备":
        if not check_equipment_can_use(user_id, goods_id):
            msg = "该装备已被装备，请勿重复装备！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await use.finish()
        else:  # 可以装备
            sql_str, item_type = get_use_equipment_sql(user_id, goods_id)
            for sql in sql_str:
                sql_message.update_back_equipment(sql)
            if item_type == "法器":
                sql_message.updata_user_faqi_buff(user_id, goods_id)
            if item_type == "防具":
                sql_message.updata_user_armor_buff(user_id, goods_id)
            msg = "成功装备{}！".format(arg)
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await use.finish()
    elif goods_type == "技能":
        user_buff_info = UserBuffDate(user_id).BuffInfo
        skill_info = items.get_data_by_item_id(goods_id)
        skill_type = skill_info['item_type']
        if skill_type == "神通":
            if int(user_buff_info['sec_buff']) == int(goods_id):
                msg = "道友已学会该神通：{}，请勿重复学习！".format(skill_info['name'])
            else:  # 学习sql
                sql_message.update_back_j(user_id, goods_id)
                sql_message.updata_user_sec_buff(user_id, goods_id)
                msg = "恭喜道友学会神通：{}！".format(skill_info['name'])
        elif skill_type == "功法":
            if int(user_buff_info['main_buff']) == int(goods_id):
                msg = "道友已学会该功法：{}，请勿重复学习！".format(skill_info['name'])
            else:  # 学习sql
                sql_message.update_back_j(user_id, goods_id)
                sql_message.updata_user_main_buff(user_id, goods_id)
                msg = "恭喜道友学会功法：{}！".format(skill_info['name'])
        elif skill_type == "辅修功法": #辅修功法1
            if int(user_buff_info['sub_buff']) == int(goods_id):
                msg = "道友已学会该辅修功法：{}，请勿重复学习！".format(skill_info['name'])
            else:#学习sql
                sql_message.update_back_j(user_id, goods_id)
                sql_message.updata_user_sub_buff(user_id, goods_id)
                msg = "恭喜道友学会辅修功法：{}！".format(skill_info['name'])   
        else:
            msg = "发生未知错误！"

        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()
    elif goods_type == "丹药":
        num = 1
        try:
            if len(args) > 1 and 1 <= int(args[1]) <= int(goods_num):
                num = int(args[1])
            elif len(args) > 1 and int(args[1]) > int(goods_num):
                msg = "道友背包中的{}数量不足，当前仅有{}个！".format(arg, goods_num)
                if XiuConfig().img:
                    pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                    await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
                else:
                    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
                await use.finish()
        except ValueError:
            num = 1
        msg = check_use_elixir(user_id, goods_id, num)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()
    elif goods_type =="神物":
        num = 1
        try:
            if len(args) > 1 and 1 <= int(args[1]) <= int(goods_num):
                num = int(args[1])
            elif len(args) > 1 and int(args[1]) > int(goods_num):
                msg = "道友背包中的{}数量不足，当前仅有{}个！".format(arg, goods_num)
                if XiuConfig().img:
                    pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                    await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
                else:
                    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
                await use.finish()
        except ValueError:
            num = 1
        goods_info = items.get_data_by_item_id(goods_id)
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info['level'])[0]
        goods_rank = goods_info['rank']
        goods_name = goods_info['name']
        if goods_rank < user_rank:  # 使用限制
                msg = "神物：{}的使用境界为{}以上，道友不满足使用条件！".format(goods_name, goods_info['境界'])
        else:
                exp = goods_info['buff'] * num
                user_hp = int(user_info['hp'] + (exp / 2))
                user_mp = int(user_info['mp'] + exp)
                user_atk = int(user_info['atk'] + (exp / 10))
                sql_message.update_exp(user_id, exp)
                sql_message.update_power2(user_id)  # 更新战力
                sql_message.update_user_attribute(user_id, user_hp, user_mp, user_atk)  # 这种事情要放在update_exp方法里
                sql_message.update_back_j(user_id, goods_id, num=num, use_key=1)
                msg = "道友成功使用神物：{} {}个 ,修为增加{}点！".format(goods_name, num, exp)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()
        
    elif goods_type =="礼包":
        num = 1  # 默认使用数量为1
        try:
             # 如果用户指定了数量，并且数量在合法范围内
            if len(args) > 1 and 1 <= int(args[1]) <= int(goods_num):
                num = int(args[1])
            elif len(args) > 1 and int(args[1]) > int(goods_num):
                # 如果用户指定的数量大于背包中的数量，则返回数量不足的提示
                msg = "道友背包中的{}数量不足，当前仅有{}个！".format(arg, goods_num)
                if XiuConfig().img:
                    pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                    await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
                else:
                    await bot.send_group_msg(group_id=int(send_group_id), message=msg)
                await use.finish()
        except ValueError:
            # 如果用户输入的数量不是一个合法的数字，则默认使用1个，并继续后续操作
            num = 1
        goods_info = items.get_data_by_item_id(goods_id)
        user_info = sql_message.get_user_info_with_id(user_id)
        user_rank = convert_rank(user_info['level'])[0]
        goods_name = goods_info['name']
        goods_id1 = goods_info['buff_1']
        goods_id2 = goods_info['buff_2']
        goods_id3 = goods_info['buff_3']
        goods_name1 = goods_info['name_1']
        goods_name2 = goods_info['name_2']
        goods_name3 = goods_info['name_3']
        goods_type1 = goods_info['type_1']
        goods_type2 = goods_info['type_2']
        goods_type3 = goods_info['type_3']
        
        sql_message.send_back(user_id, goods_id1, goods_name1, goods_type1, 1 * num, 1)# 增加用户道具
        sql_message.send_back(user_id, goods_id2, goods_name2, goods_type2, 2 * num, 1)
        sql_message.send_back(user_id, goods_id3, goods_name3, goods_type3, 2 * num, 1)
        sql_message.update_back_j(user_id, goods_id, num, 0)
        msg = "道友打开了{}个{},里面居然是{}{}个、{}{}个、{}{}个".format(num, goods_name, goods_name1, int(1 * num), goods_name2, int(2 * num), goods_name3, int(2 * num))
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()   
        
    elif goods_type == "聚灵旗":
        msg = get_use_jlq_msg(user_id, goods_id)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()
    else:
        msg = '该类型物品调试中，未开启！'
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await use.finish()

@auction_view.handle(parameterless=[Cooldown(at_sender=False, isolate_level=CooldownIsolateLevel.GROUP)])
async def auction_view_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """查看拍卖会物品"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    group_id = str(event.group_id)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_view.finish()
    
    if group_id not in groups:
        msg = '本群尚未开启拍卖会功能，请联系管理员开启！'
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await auction_view.finish()

    config = get_auction_config()
    user_auctions = config.get('user_auctions', [])

    if not user_auctions:
        msg = "拍卖会目前没有道友提交的物品！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_view.finish()

    auction_list_msg = "拍卖会物品列表:\n"
    for idx, auction in enumerate(user_auctions):
        for goods_name, details in auction.items():
            user_info = sql_message.get_user_info_with_id(details['user_id'])
            auction_list_msg += "编号: {}\n物品名称: {}\n所有者：{}\n底价: {} 枚灵石\n数量: {}\n".format(
                idx + 1, goods_name, user_info['user_name'], details['start_price'], details['quantity']
            )
            auction_list_msg += "☆------------------------------☆\n"

    if XiuConfig().img:
        pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + auction_list_msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=auction_list_msg)

    await auction_view.finish()


@creat_auction.handle(parameterless=[Cooldown(at_sender=False)])
async def creat_auction_(bot: Bot, event: GroupMessageEvent):
    global auction, auction_offer_flag, auction_offer_all_count, auction_offer_time_count
    group_id = str(event.group_id)
    bot = await assign_bot_group(group_id=group_id)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()
        
    if group_id not in groups:
        msg = '本群尚未开启拍卖会功能，请联系管理员开启！'
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()

    if auction:
        msg = "本群已存在一场拍卖会，请等待拍卖会结束！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()

    auction_items = []
    try:
        # 获取用户拍卖品
        user_auction_id_list = get_user_auction_id_list()
        for auction_id in user_auction_id_list:
            user_auction_info = get_user_auction_price_by_id(auction_id)
            auction_items.append((auction_id, user_auction_info['quantity'], user_auction_info['start_price'], True))

        # 获取系统拍卖品
        auction_id_list = get_auction_id_list()
        auction_count = random.randint(3, 8)  # 随机挑选系统拍卖品数量
        auction_ids = random.sample(auction_id_list, auction_count)
        for auction_id in auction_ids:
            item_info = items.get_data_by_item_id(auction_id)
            item_quantity = 1
            if item_info['type'] in ['神物', '丹药']:
                item_quantity = random.randint(1, 3) # 如果是丹药的话随机挑1-3个
            auction_items.append((auction_id, item_quantity, get_auction_price_by_id(auction_id)['start_price'], False))
    except LookupError:
        msg = "获取不到拍卖物品的信息，请检查配置文件！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()

    # 打乱拍卖品顺序
    random.shuffle(auction_items)

    msg = "请各位道友稍作准备，拍卖即将开始...\n"
    msg += "本场拍卖会共有{}件物品，将依次拍卖，分别是：\n".format(len(auction_items))
    for idx, (auction_id, item_quantity, start_price, is_user_auction) in enumerate(auction_items):
        item_name = items.get_data_by_item_id(auction_id)['name']
        if is_user_auction:
            owner_info = sql_message.get_user_info_with_id(get_user_auction_price_by_id(auction_id)['user_id'])
            owner_name = owner_info['user_name']
            msg += f"{idx + 1}号：{item_name}x{item_quantity}（由{owner_name}道友提供）\n"
        else:
            msg += f"{idx + 1}号：{item_name}x{item_quantity}（由拍卖场提供）\n"
    
    for gid in groups:
        bot = await assign_bot_group(group_id=gid)
        try:
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(gid), message=msg)
        except ActionFailed:  # 发送群消息失败
            continue
    
    auction_results = []  # 存储拍卖结果
    for i, (auction_id, item_quantity, start_price, is_user_auction) in enumerate(auction_items):
        auction_info = items.get_data_by_item_id(auction_id)

        auction = {
            'id': auction_id,
            'user_id': 0,
            'now_price': start_price,
            'name': auction_info['name'],
            'type': auction_info['type'],
            'quantity': item_quantity,
            'start_time': datetime.now(),
            'group_id': group_id
        }
        
        if i + 1 == len(auction_items):
            msg = "最后一件拍卖品为：\n{}\n".format(get_auction_msg(auction_id))
        else:
            msg = "第{}件拍卖品为：\n{}\n".format(i + 1, get_auction_msg(auction_id))
        msg += "\n底价为{}，加价不少于{}".format(start_price, int(start_price * 0.05))
        msg += "\n竞拍时间为:{}秒，请诸位道友发送 拍卖+金额 来进行拍卖吧！".format(AUCTIONSLEEPTIME)

        if auction['quantity'] > 1:
            msg += "\n注意：拍卖品共{}件，最终价为{} * 成交价。\n".format(auction['quantity'], auction['quantity'])

        if i + 1 < len(auction_items):
            next_item_name = items.get_data_by_item_id(auction_items[i + 1][0])['name']
            msg += "\n下一件拍卖品为：{}，请心仪的道友提前开始准备吧！".format(next_item_name)

        for gid in groups:
            bot = await assign_bot_group(group_id=gid)
            try:
                if XiuConfig().img:
                    pic = await get_msg_pic(msg)
                    await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
                else:
                    await bot.send_group_msg(group_id=int(gid), message=msg)
            except ActionFailed:  # 发送群消息失败
                continue
        
        remaining_time = AUCTIONSLEEPTIME
        while remaining_time > 0:
            await asyncio.sleep(10)
            remaining_time -= 10

        while auction_offer_flag:  # 有人拍卖
            if auction_offer_all_count == 0:
                auction_offer_flag = False
                break

            logger.opt(colors=True).info("<green>有人拍卖，本次等待时间：{}秒</green>".format(auction_offer_all_count * AUCTIONOFFERSLEEPTIME))
            first_time = auction_offer_all_count * AUCTIONOFFERSLEEPTIME
            auction_offer_all_count = 0
            auction_offer_flag = False
            await asyncio.sleep(first_time)
            logger.opt(colors=True).info("<green>总计等待时间{}秒，当前拍卖标志：{}，本轮等待时间：{}</green>".format(auction_offer_time_count * AUCTIONOFFERSLEEPTIME, auction_offer_flag, first_time))

        logger.opt(colors=True).info("<green>等待时间结束，总计等待时间{}秒</green>".format(auction_offer_time_count * AUCTIONOFFERSLEEPTIME))
        if auction['user_id'] == 0:
            msg = "很可惜，{}流拍了\n".format(auction['name'])
            if i + 1 == len(auction_items):
                msg += "本场拍卖会到此结束，开始整理拍卖会结果，感谢各位道友参与！"

            for gid in groups:
                bot = await assign_bot_group(group_id=gid)
                try:
                    if XiuConfig().img:
                        pic = await get_msg_pic(msg)
                        await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
                    else:
                        await bot.send_group_msg(group_id=int(gid), message=msg)
                except ActionFailed:  # 发送群消息失败
                    continue
            auction_results.append((auction_id, None, auction['group_id'], auction_info['type'], auction['now_price'], auction['quantity']))
            auction = {}
            continue
        
        user_info = sql_message.get_user_info_with_id(auction['user_id'])
        msg = "(拍卖锤落下)！！！\n"
        msg += "恭喜来自群{}的{}道友成功拍下：{}-{}x{}，将在拍卖会结算后送到您手中。\n".format(
            auction['group_id'], user_info['user_name'], auction['type'], auction['name'], auction['quantity'])
        if i + 1 == len(auction_items):
            msg += "本场拍卖会到此结束，开始整理拍卖会结果，感谢各位道友参与！"

        auction_results.append((auction_id, user_info['user_id'], auction['group_id'], 
                                auction_info['type'], auction['now_price'], auction['quantity']))
        auction = {}
        auction_offer_time_count = 0
        for gid in groups:
            bot = await assign_bot_group(group_id=gid)
            try:
                if XiuConfig().img:
                    pic = await get_msg_pic(msg)
                    await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
                else:
                    await bot.send_group_msg(group_id=int(gid), message=msg)
            except ActionFailed:  # 发送群消息失败
                continue
        
    # 拍卖会结算
    end_msg = "本场拍卖会结束！感谢各位道友的参与。\n拍卖结果整理如下：\n"
    print(auction_results)
    for idx, (auction_id, user_id, group_id, item_type, final_price, quantity) in enumerate(auction_results):
        item_name = items.get_data_by_item_id(auction_id)['name']
        final_user_info = sql_message.get_user_info_with_id(user_id)
        print(auction_id)
        if user_id:
            sql_message.update_ls(user_id, int(final_price) * quantity, 2)
            sql_message.send_back(user_id, auction_id, item_name, item_type, quantity)
            end_msg += "{}号拍卖品：{}x{}由群{}的{}道友成功拍下\n".format(
                idx + 1, item_name, quantity, group_id, final_user_info['user_name']
            )

            user_auction_info = get_user_auction_price_by_id(auction_id)
            if user_auction_info:
                seller_id = user_auction_info['user_id']
                auction_earnings = int(final_price) * quantity * 0.7
                sql_message.update_ls(seller_id, auction_earnings, 1)

            remove_auction_item(auction_id)

            auction = {}
            auction_offer_time_count = 0
        else:
            end_msg += "{}号拍卖品：{}x{} - 流拍了\n".format(
                idx + 1, item_name, quantity
            )

    for gid in groups:
        bot = await assign_bot_group(group_id=gid)
        try:
            if XiuConfig().img:
                pic = await get_msg_pic(end_msg)
                await bot.send_group_msg(group_id=int(gid), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(gid), message=end_msg)
        except ActionFailed:  # 发送群消息失败
            continue

    await creat_auction.finish()


@offer_auction.handle(parameterless=[Cooldown(1.4, at_sender=False, isolate_level=CooldownIsolateLevel.GLOBAL)])
async def offer_auction_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    group_id = str(event.group_id)
    bot = await assign_bot_group(group_id=group_id)
    isUser, user_info, msg = check_user(event)
    global auction, auction_offer_flag, auction_offer_all_count, auction_offer_time_count
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()

    if group_id not in groups:
        msg = '本群尚未开启拍卖会功能，请联系管理员开启！'
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()

    if not auction:
        msg = "本群不存在拍卖会，请等待拍卖会开启！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()

    price = args.extract_plain_text().strip()
    try:
        price = int(price)
    except ValueError:
        msg = "请发送正确的灵石数量"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()

    now_price = auction['now_price']
    min_price = int(now_price * 0.05)  # 最低加价5%
    if price <= 0 or price <= auction['now_price'] or price > user_info['stone']:
        msg = "走开走开，别捣乱！小心清空你灵石捏"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()
    if price - now_price < min_price:
        msg = "拍卖不得少于当前竞拍价的5%，目前最少加价为：{}灵石，目前竞拍价为：{}!".format(min_price, now_price)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()

    auction_offer_flag = True  # 有人拍卖
    auction_offer_time_count += 1
    auction_offer_all_count += 1

    auction['user_id'] = user_info['user_id']
    auction['now_price'] = price
    auction['group_id'] = group_id

    logger.opt(colors=True).info("<green>{}({})竞价了！！</green>".format(user_info['user_name'], auction['user_id']))

    now_time = datetime.now()
    dif_time = (now_time - auction['start_time']).total_seconds()
    remaining_time = int(AUCTIONSLEEPTIME - dif_time + AUCTIONOFFERSLEEPTIME * auction_offer_time_count)
    msg = (
        "来自群{}的{}道友拍卖：{}枚灵石！".format(group_id, user_info['user_name'], price) +
        "竞拍时间增加：{}秒，竞拍剩余时间：{}秒".format(
            AUCTIONOFFERSLEEPTIME, remaining_time
        )
    )
    error_msg = None
    for group_id in groups:
        bot = await assign_bot_group(group_id=group_id)
        try:
            if XiuConfig().img:
                pic = await get_msg_pic(msg)
                await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(group_id), message=msg)
        except ActionFailed:
            error_msg = "消息发送失败，可能被风控，当前拍卖物品金额为：{}！".format(auction['now_price'])
            continue
    logger.opt(colors=True).info(
        "<green>有人拍卖，拍卖标志：{}，当前等待时间：{}，总计拍卖次数：{}</green>".format(
            auction_offer_flag, auction_offer_all_count * AUCTIONOFFERSLEEPTIME, auction_offer_time_count)
            )
    if error_msg is None:
        await offer_auction.finish()
    else:
        msg = error_msg
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await creat_auction.finish()


@auction_add.handle(parameterless=[Cooldown(1.4, isolate_level=CooldownIsolateLevel.GROUP)])
async def auction_add_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """用户提交拍卖品"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    group_id = str(event.group_id)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_add.finish()

    if group_id not in groups:
        msg = '本群尚未开启拍卖会功能，请联系管理员开启！'
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
        await auction_add.finish()

    user_id = user_info['user_id']
    args = args.extract_plain_text().split()
    goods_name = args[0] if len(args) > 0 else None
    price_str = args[1] if len(args) > 1 else "1"
    quantity_str = args[2] if len(args) > 2 else "1"

    if not goods_name:
        msg = "请输入正确指令！例如：提交拍卖品 物品 可选参数为(金额 数量)"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_add.finish()

    back_msg = sql_message.get_back_msg(user_id)  # 获取背包信息
    if back_msg is None:
        msg = "道友的背包空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_add.finish()

    # 物品是否存在于背包中
    in_flag = False
    goods_id = None
    goods_type = None
    goods_state = None
    goods_num = None
    goods_bind_num = None
    for back in back_msg:
        if goods_name == back['goods_name']:
            in_flag = True
            goods_id = back['goods_id']
            goods_type = back['goods_type']
            goods_state = back['state']
            goods_num = back['goods_num']
            goods_bind_num = back['bind_num']
            break

    if not in_flag:
        msg = "请检查该道具 {} 是否在背包内！".format(goods_name)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_add.finish()

    try:
        price = int(price_str)
        quantity = int(quantity_str)
        if price <= 0 or quantity <= 0 or quantity > goods_num:
            raise ValueError("价格和数量必须为正数，或者超过了你拥有的数量!")
    except ValueError as e:
        msg = "请输入正确的金额和数量: {}".format(str(e))
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_add.finish()

    if goods_type == "装备" and int(goods_state) == 1 and int(goods_num) == 1:
        msg = "装备：{}已经被道友装备在身，无法提交！".format(goods_name)
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_add.finish()

    if int(goods_num) <= int(goods_bind_num):
        msg = "该物品是绑定物品，无法提交！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await auction_add.finish()
    if goods_type == "聚灵旗" or goods_type == "炼丹炉":
        if user_info['root'] == "器师":
            pass
        else:
            msg = "道友职业无法上架！"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await auction_add.finish()

    config = get_auction_config()

    user_auction = {
        goods_name: {
            'id': goods_id,
            'user_id': user_id,
            'start_price': price,
            'quantity': quantity
        }
    }
    config['user_auctions'].append(user_auction)

    savef_auction(config)
    sql_message.update_back_j(user_id, goods_id, num=quantity)

    msg = "道友的拍卖品：{}成功提交，底价：{}枚灵石，数量：{}".format(goods_name, price, quantity)
    msg += "\n下次拍卖将优先拍卖道友的拍卖品！！！"
    if XiuConfig().img:
        pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await auction_add.finish()


@set_auction.handle(parameterless=[Cooldown(at_sender=False)])
async def set_auction_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    mode = args.extract_plain_text().strip()
    group_id = str(event.group_id)
    is_in_group = is_in_groups(event)  # True在，False不在

    if mode == '开启':
        if is_in_group:
            msg = "本群已开启群拍卖会，请勿重复开启!"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await set_auction.finish()
        else:
            config['open'].append(group_id)
            savef_auction(config)
            msg = "已开启群拍卖会"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await set_auction.finish()

    elif mode == '关闭':
        if is_in_group:
            config['open'].remove(group_id)
            savef_auction(config)
            msg = "已关闭本群拍卖会!"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await set_auction.finish()
        else:
            msg = "本群未开启群拍卖会!"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
            await set_auction.finish()

    else:
        msg = __back_help__
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await set_auction.finish()


@chakan_wupin.handle(parameterless=[Cooldown(at_sender=False)])
async def chakan_wupin_(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """查看修仙界所有物品列表"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    args = args.extract_plain_text().strip()
    list_tp = []
    if args not in ["功法", "辅修功法", "神通", "丹药", "合成丹药", "法器", "防具"]:
        msg = "请输入正确类型【功法|辅修功法|神通|丹药|合成丹药|法器|防具】！！！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await chakan_wupin.finish()
    else:
        if args == "功法":
            gf_data = items.get_data_by_item_type(['功法'])
            for x in gf_data:
                name = gf_data[x]['name']
                rank = gf_data[x]['level']
                msg = "※{}:{}".format(rank, name)
                list_tp.append(
                    {"type": "node", "data": {"name": f"修仙界物品列表{args}", "uin": bot.self_id,
                                              "content": msg}})
        elif args == "辅修功法":
            gf_data = items.get_data_by_item_type(['辅修功法'])
            for x in gf_data:
                name = gf_data[x]['name']
                rank = gf_data[x]['level']
                msg = "※{}:{}".format(rank, name)
                list_tp.append(
                    {"type": "node", "data": {"name": f"修仙界物品列表{args}", "uin": bot.self_id,
                                              "content": msg}})
        elif args == "神通":
            st_data = items.get_data_by_item_type(['神通'])
            for x in st_data:
                name = st_data[x]['name']
                rank = st_data[x]['level']
                msg = "※{}:{}".format(rank, name)
                list_tp.append(
                    {"type": "node", "data": {"name": f"修仙界物品列表{args}", "uin": bot.self_id,
                                              "content": msg}})
        elif args == "丹药":
            dy_data = items.get_data_by_item_type(['丹药'])
            for x in dy_data:
                name = dy_data[x]['name']
                rank = dy_data[x]['境界']
                desc = dy_data[x]['desc']
                msg = "※{}丹药:{}，效果：{}\n".format(rank, name, desc)
                list_tp.append(
                    {"type": "node", "data": {"name": f"修仙界物品列表{args}", "uin": bot.self_id,
                                              "content": msg}})
        elif args == "合成丹药":
            hcdy_data = items.get_data_by_item_type(['合成丹药'])
            for x in hcdy_data:
                name = hcdy_data[x]['name']
                rank = hcdy_data[x]['境界']
                desc = hcdy_data[x]['desc']
                msg = "※{}丹药:{}，效果：{}\n\n".format(rank, name, desc)
                list_tp.append(
                    {"type": "node", "data": {"name": f"修仙界物品列表{args}", "uin": bot.self_id,
                                              "content": msg}})
        elif args == "法器":
            fq_data = items.get_data_by_item_type(['法器'])
            for x in fq_data:
                name = fq_data[x]['name']
                rank = fq_data[x]['level']
                msg = "※{}:{}".format(rank, name)
                list_tp.append(
                    {"type": "node", "data": {"name": f"修仙界物品列表{args}", "uin": bot.self_id,
                                              "content": msg}})
        elif args == "防具":
            fj_data = items.get_data_by_item_type(['防具'])
            for x in fj_data:
                name = fj_data[x]['name']
                rank = fj_data[x]['level']
                msg = "※{}:{}".format(rank, name)
                list_tp.append(
                    {"type": "node", "data": {"name": f"修仙界物品列表{args}", "uin": bot.self_id,
                                              "content": msg}})
        try:
            await send_msg_handler(bot, event, list_tp)
        except ActionFailed:
            msg = "未知原因，查看失败!"
            if XiuConfig().img:
                pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
                await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
            else:
                await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await chakan_wupin.finish()


@shop_off_all.handle(parameterless=[Cooldown(60, isolate_level=CooldownIsolateLevel.GROUP, parallel=1)])
async def shop_off_all_(bot: Bot, event: GroupMessageEvent):
    """坊市清空"""
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    isUser, user_info, msg = check_user(event)
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_off_all.finish()
    group_id = str(event.group_id)
    shop_data = get_shop_data(group_id)
    if shop_data[group_id] == {}:
        msg = "坊市目前空空如也！"
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await shop_off_all.finish()

    msg = "正在清空,稍等！"
    if XiuConfig().img:
        pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)

    list_msg = []
    msg = ""
    num = len(shop_data[group_id])
    for x in range(num):
        x = num - x
        if shop_data[group_id][str(x)]['user_id'] == 0:  # 这么写为了防止bot.send发送失败，不结算
            msg += "成功下架系统物品：{}!\n".format(shop_data[group_id][str(x)]['goods_name'])
            del shop_data[group_id][str(x)]
            save_shop(shop_data)
        else:
            sql_message.send_back(shop_data[group_id][str(x)]['user_id'], shop_data[group_id][str(x)]['goods_id'],
                                  shop_data[group_id][str(x)]['goods_name'],
                                  shop_data[group_id][str(x)]['goods_type'], shop_data[group_id][str(x)]['stock'])
            msg += "成功下架{}的{}个{}!\n".format(shop_data[group_id][str(x)]['user_name'], shop_data[group_id][str(x)]['stock'], shop_data[group_id][str(x)]['goods_name'])
            del shop_data[group_id][str(x)]
            save_shop(shop_data)
    shop_data[group_id] = reset_dict_num(shop_data[group_id])
    save_shop(shop_data)
    list_msg.append(
                    {"type": "node", "data": {"name": "执行清空坊市ing", "uin": bot.self_id,
                                              "content": msg}})
    try:
        await send_msg_handler(bot, event, list_msg)
    except ActionFailed:
        if XiuConfig().img:
            pic = await get_msg_pic("@{}\n".format(event.sender.nickname) + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
    await shop_off_all.finish()


def reset_dict_num(dict_):
    i = 1
    temp_dict = {}
    for k, v in dict_.items():
        temp_dict[i] = v
        temp_dict[i]['编号'] = i
        i += 1
    return temp_dict


def get_user_auction_id_list():
    user_auctions = config['user_auctions']
    user_auction_id_list = []
    for auction in user_auctions:
        for k, v in auction.items():
            user_auction_id_list.append(v['id'])
    return user_auction_id_list

def get_auction_id_list():
    auctions = config['auctions']
    auction_id_list = []
    for k, v in auctions.items():
        auction_id_list.append(v['id'])
    return auction_id_list

def get_user_auction_price_by_id(id):
    user_auctions = config['user_auctions']
    user_auction_info = None
    for auction in user_auctions:
        for k, v in auction.items():
            if int(v['id']) == int(id):
                user_auction_info = v
                break
        if user_auction_info:
            break
    return user_auction_info

def get_auction_price_by_id(id):
    auctions = config['auctions']
    auction_info = None
    for k, v in auctions.items():
        if int(v['id']) == int(id):
            auction_info = v
            break
    return auction_info


def is_in_groups(event: GroupMessageEvent):
    return str(event.group_id) in groups


def get_auction_msg(auction_id):
    item_info = items.get_data_by_item_id(auction_id)
    _type = item_info['type']
    msg = None
    if _type == "装备":
        if item_info['item_type'] == "防具":
            msg = get_armor_info_msg(auction_id, item_info)
        if item_info['item_type'] == '法器':
            msg = get_weapon_info_msg(auction_id, item_info)

    if _type == "技能":
        if item_info['item_type'] == '神通':
            msg = "{}-{}:\n".format(item_info['level'], item_info['name'])
            msg += "效果：{}".format(get_sec_msg(item_info))
        if item_info['item_type'] == '功法':
            msg = "{}-{}\n".format(item_info['level'], item_info['name'])
            msg += "效果：{}".format(get_main_info_msg(auction_id)[1])
        if item_info['item_type'] == '辅修功法': #辅修功法10
            msg = "{}-{}\n".format(item_info['level'], item_info['name'])
            msg += "效果：{}".format(get_sub_info_msg(auction_id)[1])
            
    if _type == "神物":
        msg = "{}\n".format(item_info['name'])
        msg += "效果：{}".format(item_info['desc'])

    if _type == "丹药":
        msg = "{}\n".format(item_info['name'])
        msg += "效果：{}".format(item_info['desc'])

    return msg
