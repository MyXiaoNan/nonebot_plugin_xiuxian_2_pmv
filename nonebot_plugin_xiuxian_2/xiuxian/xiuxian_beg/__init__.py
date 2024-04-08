import random
from datetime import datetime
from ..xiuxian_utils.lay_out import assign_bot, Cooldown
from nonebot import require, on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GROUP,
    GroupMessageEvent,
    MessageSegment
)
from nonebot.log import logger
from ..xiuxian_utils.xiuxian_config import USERRANK
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_utils.xiuxian_config import XiuConfig
from ..xiuxian_utils.utils import (
    check_user,
    get_msg_pic,
    CommandObjectID,
)


# 定时任务
scheduler = require("nonebot_plugin_apscheduler").scheduler
cache_help = {}
sql_message = XiuxianDateManage()  # sql类
# 重置奇缘
@scheduler.scheduled_job("cron", hour=0, minute=0)
async def xiuxian_beg_():
    sql_message.beg_remake()
    logger.opt(colors=True).info("仙途奇缘重置成功！")

__beg_help__ = f"""
奇缘帮助信息:
为了让初入仙途的道友们更顺利地踏上修炼之路，特别开辟了额外的机缘——发送“仙途奇缘”(先去看奇缘帮助)
便可天降灵石，助君一臂之力。
若有心人借此谋取不正之利，必将遭遇天道轮回，异象降临，后果自负。
诸位道友，若不信此言，可自行一试，便知天机不可泄露，天道不容欺。
""".strip()

beg_stone = on_command("仙途奇缘", permission=GROUP, priority=7, block=True)
beg_help = on_command("奇缘帮助", permission=GROUP, priority=7, block=True)

@beg_help.handle(parameterless=[Cooldown(at_sender=True)])
async def beg_help_(bot: Bot, event: GroupMessageEvent, session_id: int = CommandObjectID()):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    if session_id in cache_help:
        await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(cache_help[session_id]))
        await beg_help.finish()
    else:
        msg = __beg_help__
        if XiuConfig().img:
            pic = await get_msg_pic(msg)
            cache_help[session_id] = pic
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await beg_help.finish()

@beg_stone.handle(parameterless=[Cooldown(at_sender=True)])
async def beg_stone(bot: Bot, event: GroupMessageEvent):
    bot, send_group_id = await assign_bot(bot=bot, event=event)
    user_id = event.get_user_id()
    isUser, user_info, _ = check_user(event)
    user_msg = sql_message.get_user_message(user_id)
    user_root = user_msg.root_type
    user_rank = USERRANK[user_info.level]
    sect = user_info.sect_id

    # create_time = datetime.strptime(user_info.create_time, "%Y-%m-%d %H:%M:%S.%f")
    # now_time = datetime.now()
    # diff_time = now_time - create_time
    # diff_days = diff_time.days
    

    
    if not isUser:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=int(send_group_id), message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=int(send_group_id), message=msg)
        await beg_stone.finish()

    elif sect != None and user_root == "伪灵根":
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + "道友已有宗门庇佑，又何必来此寻求机缘呢？")
            await bot.send_group_msg(group_id=event.group_id, message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=event.group_id, message=msg)

    elif user_root in {"轮回道果", "真·轮回道果"}:
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + "道友已是转生大能，又何必来此寻求机缘呢？")
            await bot.send_group_msg(group_id=event.group_id, message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=event.group_id, message=msg)

    elif user_rank < 37:
        msg = f"道友已跻身于{user_info.level}层次的修行之人，可徜徉于四海八荒，自寻机缘与造化矣。"
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=event.group_id, message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=event.group_id, message=msg)

    else:
        stone = XiuxianDateManage().get_beg(user_id)
        if stone is None:
            msg = '贪心的人是不会有好运的！'
        else:
            msg = random.choice(
    [
        f"在一次深入古老森林的修炼旅程中，你意外地遇到了一位神秘的前辈高人。这位前辈不仅给予了你宝贵的修炼指导，还在临别时赠予了你 {stone} 枚灵石，以表达对你的认可和鼓励。",
        f"某日，在一个清澈的小溪边，一只珍稀的灵兽突然出现在你面前。它似乎对你的气息感到亲切，竟然留下了 {stone} 枚灵石，好像是在对你展示它的友好和感激。",
        f"在一次勇敢的探险中，你发现了一片被遗忘的灵石矿脉。通过采矿获得了 {stone} 枚灵石，这不仅是一次意外的惊喜，也是对你勇气和坚持的奖赏。",
        f"在一个宁静的夜晚，你抬头夜观星象，突然一颗流星划破夜空，落在你的附近。你跟随流星落下的轨迹找到了 {stone} 枚灵石，就像是来自天际的礼物。",
        f"在一次偶然的机会下，你在一座古老的山洞深处发现了一块充满灵气的巨大灵石，将它收入囊中并获得了 {stone} 枚灵石。这块灵石似乎蕴含着古老的力量，让你的修为有了不小的提升。",
        f"在一次探索未知禁地时，你解开了一个古老的阵法，这个阵法守护着数世纪的秘密。当最后一个符文点亮时，阵法缓缓散开，露出了其中藏有的 {stone} 枚灵石。",
        f"在一次河床淘金的经历中，你意外发现了一些隐藏在水流淤泥中的 {stone} 枚灵石。这些灵石对于修炼者来说极为珍贵，而你却在这样一个不经意的时刻发现了它们。这次发现让你更加相信，修炼之路上的每一次机缘都是命运的安排，值得你去珍惜和感激",
        f"在一次偶然的机会下，你在一座古墓的深处发现了一个隐藏的宝藏，其中藏有 {stone} 枚灵石。这些灵石可能是古时某位大能为后人留下的财富，而你，正是那位幸运的发现者。这次发现不仅大大增加了你的修为，也让你对探索古墓和古老传说充满了无尽的好奇和兴趣。",
        f"参加门派举办的比武大会，你凭借着出色的实力和智慧，一路过关斩将，但在最终对决中惜败萧炎。虽败犹荣，作为奖励，门派赠予了你 {stone} 枚灵石，这不仅是对你实力的认可，也是对你未来修炼的支持。",
        f"在一次对古老遗迹的探索中，你解开了一道埋藏已久的谜题。随着最后一个谜题的解开，一个密室缓缓打开，里面藏有的 {stone} 枚灵石作为奖励呈现在你面前。这些灵石对你来说，不仅是物质上的奖励，更是对你智慧和毅力的肯定。",
        f"修炼时，你意外地遇到了一次天降祥瑞的奇观，一朵灵花从天而降，化作了 {stone} 枚灵石落入你的背包中。这次祥瑞不仅让你的修为有了不小的提升，也让你深感天地之大，自己仍需不断努力，探索修炼的更高境界。",
        f"在一次门派分配的任务中，你表现出色，解决了一个困扰门派多时的难题。作为对你贡献的认可，门派特别奖励了你 {stone} 枚灵石。",
        f"一位神秘旅行者传授给你一张古老的地图，据说地图上标记的宝藏正是数量可观的灵石。经过一番冒险和探索，你终于找到了宝藏所在，获得了 {stone} 枚灵石!",
        f"在你帮助一位受伤的异兽后，作为感谢，它送给了你 {stone} 枚灵石。随后踏云而去，修炼之路上的每一个生命都值得尊重和帮助，而善行和仁心，往往能收获意想不到的回报。",
        f"在一次与妖兽的激战中胜出后，你发现了妖兽巢穴中藏有的 {stone} 枚灵石。这些灵石对你的修炼大有裨益，也让你对面对挑战时的勇气和决心有了更深的理解。",
        f"你在一次随机的交易中获得了一个外表不起眼的神秘盒子。当你好奇心驱使下打开它时，发现里面竟是一枚装满灵石的纳戒，收获了 {stone} 枚灵石！",
    ]
)
        if XiuConfig().img:
            pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
            await bot.send_group_msg(group_id=event.group_id, message=MessageSegment.image(pic))
        else:
            await bot.send_group_msg(group_id=event.group_id, message=msg)

    

