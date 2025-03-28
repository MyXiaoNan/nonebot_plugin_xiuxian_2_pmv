import asyncio
import datetime
import io
import json
import math
import os
import unicodedata
from base64 import b64encode
from io import BytesIO
from pathlib import Path

from nonebot.adapters import MessageSegment
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    MessageSegment,
)
from nonebot.params import Depends
from PIL import Image, ImageDraw, ImageFont
from wcwidth import wcwidth

from ..xiuxian_config import XiuConfig
from .data_source import jsondata
from .xiuxian2_handle import XiuxianDateManage

sql_message = XiuxianDateManage()  # sql类
boss_img_path = Path() / "data" / "xiuxian" / "boss_img"


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, bytes):
            return str(obj, encoding="utf-8")
        if isinstance(obj, int):
            return int(obj)
        elif isinstance(obj, float):
            return float(obj)
        else:
            return super(MyEncoder, self).default(obj)


def check_user_type(user_id, need_type):
    """
    :说明: `check_user_type`
    > 匹配用户状态，返回是否状态一致
    :返回参数:
      * `isType: 是否一致
      * `msg: 消息体
    """
    isType = False
    msg = ""
    user_cd_message = sql_message.get_user_cd(user_id)
    if user_cd_message is None:
        user_type = 0
    else:
        user_type = user_cd_message["type"]

    if user_type == need_type:  # 状态一致
        isType = True
    else:
        if user_type == 1:
            msg = "道友现在在闭关呢，小心走火入魔！"

        elif user_type == 2:
            msg = "道友现在在做悬赏令呢，小心走火入魔！"

        elif user_type == 3:
            msg = "道友现在正在秘境中，分身乏术！"

        elif user_type == 0:
            msg = "道友现在什么都没干呢~"

    return isType, msg


def check_user(event: GroupMessageEvent):
    """
    判断用户信息是否存在
    :返回参数:
      * `isUser: 是否存在
      * `user_info: 用户
      * `msg: 消息体
    """

    isUser = False
    user_id = event.get_user_id()
    user_info = sql_message.get_user_info_with_id(user_id)
    if user_info is None:
        msg = "修仙界没有道友的信息，请输入【我要修仙】加入！"
    else:
        isUser = True
        msg = ""

    return isUser, user_info, msg


class Txt2Img:
    """文字转图片"""

    def __init__(self, size=32):
        self.font = str(jsondata.FONT_FILE)
        self.font_size = int(size)
        self.use_font = ImageFont.truetype(font=self.font, size=self.font_size)
        self.upper_size = 30
        self.below_size = 30
        self.left_size = 40
        self.right_size = 55
        self.padding = 12
        self.img_width = 780
        self.black_clor = (255, 255, 255)
        self.line_num = 0

        self.user_font_size = int(size * 1.5)
        self.lrc_font_size = int(size)
        self.font_family = str(jsondata.FONT_FILE)
        self.share_img_width = 1080
        self.line_space = int(size)
        self.lrc_line_space = int(size / 2)

    # 预处理
    def prepare(self, text, scale):
        text = unicodedata.normalize("NFKC", text)
        if scale:
            max_text_len = self.img_width - self.left_size - self.right_size
        else:
            max_text_len = 1080 - self.left_size - self.right_size
        use_font = self.use_font
        line_num = self.line_num
        text_len = 0
        text_new = ""
        for x in text:
            text_new += x
            text_len += use_font.getlength(x)
            if x == "\n":
                text_len = 0
            if text_len >= max_text_len:
                text_len = 0
                text_new += "\n"
        text_new = text_new.replace("\n\n", "\n")
        text_new = text_new.rstrip()
        line_num = line_num + text_new.count("\n")
        return text_new, line_num

    def sync_draw_to(self, text, boss_name="", scale=True):
        font_size = self.font_size
        black_clor = self.black_clor
        upper_size = self.upper_size
        below_size = self.below_size
        left_size = self.left_size
        padding = self.padding
        img_width = self.img_width
        use_font = self.use_font
        text, line_num = self.prepare(text=text, scale=scale)
        if scale:
            if line_num < 5:
                blank_space = int(5 - line_num)
                line_num = 5
                text += "\n"
                for k in range(blank_space):
                    text += "(^ ᵕ ^)\n"
            else:
                line_num = line_num
        else:
            img_width = 1080
            line_num = line_num
        img_hight = int(
            upper_size + below_size + font_size * (line_num + 1) + padding * line_num
        )
        out_img = Image.new(mode="RGB", size=(img_width, img_hight), color=black_clor)
        draw = ImageDraw.Draw(out_img, "RGBA")

        # 设置
        banner_size = 12
        border_color = (220, 211, 196)
        out_padding = 15
        mi_img = Image.open(jsondata.BACKGROUND_FILE)
        mi_banner = Image.open(jsondata.BANNER_FILE).resize(
            (banner_size, banner_size), resample=3
        )

        # 添加背景
        for x in range(int(math.ceil(img_hight / 100))):
            out_img.paste(mi_img, (0, x * 100))

        # 添加边框
        def draw_rectangle(draw, rect, width):
            for i in range(width):
                draw.rectangle(
                    (rect[0] + i, rect[1] + i, rect[2] - i, rect[3] - i),
                    outline=border_color,
                )

        draw_rectangle(
            draw,
            (
                out_padding,
                out_padding,
                img_width - out_padding,
                img_hight - out_padding,
            ),
            2,
        )

        # 添加banner
        out_img.paste(mi_banner, (out_padding, out_padding))
        out_img.paste(
            mi_banner.transpose(Image.FLIP_TOP_BOTTOM),
            (out_padding, img_hight - out_padding - banner_size + 1),
        )
        out_img.paste(
            mi_banner.transpose(Image.FLIP_LEFT_RIGHT),
            (img_width - out_padding - banner_size + 1, out_padding),
        )
        out_img.paste(
            mi_banner.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM),
            (
                img_width - out_padding - banner_size + 1,
                img_hight - out_padding - banner_size + 1,
            ),
        )

        # 绘制文字
        draw.text(
            (left_size, upper_size),
            text,
            font=use_font,
            fill=(125, 101, 89),
            spacing=padding,
        )
        # 贴boss图
        if boss_name:
            boss_img_path = jsondata.BOSS_IMG / f"{boss_name}.png"
            if os.path.exists(boss_img_path):
                boss_img = Image.open(boss_img_path)
                base_cc = boss_img.height / img_hight
                boss_img_w = int(boss_img.width / base_cc)
                boss_img_h = int(boss_img.height / base_cc)
                boss_img = boss_img.resize(
                    (int(boss_img_w), int(boss_img_h)), Image.Resampling.LANCZOS
                )
                out_img.paste(
                    boss_img,
                    (int(img_width - boss_img_w), int(img_hight - boss_img_h)),
                    boss_img,
                )
        if XiuConfig().img_send_type == "io":
            return out_img
        elif XiuConfig().img_send_type == "base64":
            return self.img2b64(out_img)

    def img2b64(self, out_img) -> str:
        """将图片转换为base64"""
        buf = BytesIO()
        out_img.save(buf, format="PNG")
        base64_str = "base64://" + b64encode(buf.getvalue()).decode()
        return base64_str

    async def io_draw_to(self, text, boss_name="", scale=True):  # draw_to
        loop = asyncio.get_running_loop()
        out_img = await loop.run_in_executor(
            None, self.sync_draw_to, text, boss_name, scale
        )
        return await loop.run_in_executor(
            None, self.save_image_with_compression, out_img
        )

    async def save(self, title, lrc):
        """保存图片,涉及title时使用"""
        border_color = (220, 211, 196)
        text_color = (125, 101, 89)

        out_padding = 30
        padding = 45
        banner_size = 20

        user_font = ImageFont.truetype(self.font_family, self.user_font_size)
        lyric_font = ImageFont.truetype(self.font_family, self.lrc_font_size)

        if title == " ":
            title = ""

        lrc = self.wrap(lrc)

        if lrc.find("\n") > -1:
            lrc_rows = len(lrc.split("\n"))
        else:
            lrc_rows = 1

        w = self.share_img_width

        if title:
            inner_h = (
                padding * 2
                + self.user_font_size
                + self.line_space
                + self.lrc_font_size * lrc_rows
                + (lrc_rows - 1) * (self.lrc_line_space)
            )
        else:
            inner_h = (
                padding * 2
                + self.lrc_font_size * lrc_rows
                + (lrc_rows - 1) * (self.lrc_line_space)
            )

        h = out_padding * 2 + inner_h

        out_img = Image.new(mode="RGB", size=(w, h), color=(255, 255, 255))
        draw = ImageDraw.Draw(out_img)

        mi_img = Image.open(jsondata.BACKGROUND_FILE)
        mi_banner = Image.open(jsondata.BANNER_FILE).resize(
            (banner_size, banner_size), resample=3
        )

        # add background
        for x in range(int(math.ceil(h / 100))):
            out_img.paste(mi_img, (0, x * 100))

        # add border
        def draw_rectangle(draw, rect, width):
            for i in range(width):
                draw.rectangle(
                    (rect[0] + i, rect[1] + i, rect[2] - i, rect[3] - i),
                    outline=border_color,
                )

        draw_rectangle(
            draw, (out_padding, out_padding, w - out_padding, h - out_padding), 2
        )

        # add banner
        out_img.paste(mi_banner, (out_padding, out_padding))
        out_img.paste(
            mi_banner.transpose(Image.FLIP_TOP_BOTTOM),
            (out_padding, h - out_padding - banner_size + 1),
        )
        out_img.paste(
            mi_banner.transpose(Image.FLIP_LEFT_RIGHT),
            (w - out_padding - banner_size + 1, out_padding),
        )
        out_img.paste(
            mi_banner.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM),
            (w - out_padding - banner_size + 1, h - out_padding - banner_size + 1),
        )

        if title:
            tmp_img = Image.new("RGB", (1, 1))
            tmp_draw = ImageDraw.Draw(tmp_img)
            user_bbox = tmp_draw.textbbox(
                (0, 0), title, font=user_font, spacing=self.line_space
            )
            # 四元组(left, top, right, bottom)
            user_w = user_bbox[2] - user_bbox[0]  # 宽度 = right - left
            user_h = user_bbox[3] - user_bbox[1]
            draw.text(
                ((w - user_w) // 2, out_padding + padding),
                title,
                font=user_font,
                fill=text_color,
                spacing=self.line_space,
            )
            draw.text(
                (
                    out_padding + padding,
                    out_padding + padding + self.user_font_size + self.line_space,
                ),
                lrc,
                font=lyric_font,
                fill=text_color,
                spacing=self.lrc_line_space,
            )
        else:
            draw.text(
                (out_padding + padding, out_padding + padding),
                lrc,
                font=lyric_font,
                fill=text_color,
                spacing=self.lrc_line_space,
            )
        if XiuConfig().img_send_type == "io":
            buf = BytesIO()
            if XiuConfig().img_type == "webp":
                out_img.save(buf, format="WebP")
            elif XiuConfig().img_type == "jpeg":
                out_img.save(buf, format="JPEG")
            buf.seek(0)
            return buf
        elif XiuConfig().img_send_type == "base64":
            return self.img2b64(out_img)

    def save_image_with_compression(self, out_img):
        """对传入图片进行压缩"""
        img_byte_arr = io.BytesIO()
        compression_quality = max(
            1, min(100, 100 - XiuConfig().img_compression_limit)
        )  # 质量从100到1

        if not (0 <= XiuConfig().img_compression_limit <= 100):
            compression_quality = 50

        # 转换为 RGB
        if out_img.mode in ("RGBA", "P"):
            out_img = out_img.convert("RGB")

        try:
            if XiuConfig().img_type == "webp":
                out_img.save(img_byte_arr, format="WebP", quality=compression_quality)
            elif XiuConfig().img_type == "jpeg":
                out_img.save(img_byte_arr, format="JPEG", quality=compression_quality)
            else:
                out_img.save(img_byte_arr, format="WebP", quality=compression_quality)
        except:
            # 尝试降级为 JPEG
            out_img.save(img_byte_arr, format="JPEG", quality=compression_quality)

        img_byte_arr.seek(0)
        return img_byte_arr

    def wrap(self, string):
        max_width = int(1850 / self.lrc_font_size)
        temp_len = 0
        result = ""
        for ch in string:
            result += ch
            temp_len += wcwidth(ch)
            if ch == "\n":
                temp_len = 0
            if temp_len >= max_width:
                temp_len = 0
                result += "\n"
        result = result.rstrip()
        return result


async def get_msg_pic(msg, boss_name="", scale=True):
    img = Txt2Img()
    if XiuConfig().img_send_type == "io":
        pic = await img.io_draw_to(msg, boss_name, scale)
    elif XiuConfig().img_send_type == "base64":
        pic = img.sync_draw_to(msg, boss_name, scale)
    return pic


async def send_msg_handler(bot, event, *args):
    """
    统一消息发送处理器
    :param bot: 机器人实例
    :param event: 事件对象
    :param name: 用户名称
    :param uin: 用户QQ号
    :param msgs: 消息内容列表
    :param messages: 合并转发的消息列表（字典格式）
    :param msg_type: 关键字参数，可用于传递特定命名参数
    """

    if XiuConfig().merge_forward_send:
        if len(args) == 3:
            name, uin, msgs = args
            messages = [
                {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}
                for msg in msgs
            ]
            if isinstance(event, GroupMessageEvent):
                await bot.call_api(
                    "send_group_forward_msg", group_id=event.group_id, messages=messages
                )
            else:
                await bot.call_api(
                    "send_private_forward_msg", user_id=event.user_id, messages=messages
                )
        elif len(args) == 1 and isinstance(args[0], list):
            messages = args[0]
            if isinstance(event, GroupMessageEvent):
                await bot.call_api(
                    "send_group_forward_msg", group_id=event.group_id, messages=messages
                )
            else:
                await bot.call_api(
                    "send_private_forward_msg", user_id=event.user_id, messages=messages
                )
        else:
            raise ValueError("参数数量或类型不匹配")
    else:
        if len(args) == 3:
            name, uin, msgs = args
            img = Txt2Img()
            messages = "\n".join(msgs)
            if XiuConfig().img_send_type == "io":
                img_data = await img.io_draw_to(messages)
            elif XiuConfig().img_send_type == "base64":
                img_data = img.sync_draw_to(messages)
            if isinstance(event, GroupMessageEvent):
                await bot.send_group_msg(
                    group_id=event.group_id, message=MessageSegment.image(img_data)
                )
            else:
                await bot.send_private_msg(
                    user_id=event.user_id, message=MessageSegment.image(img_data)
                )
        elif len(args) == 1 and isinstance(args[0], list):
            messages = args[0]
            img = Txt2Img()
            messages = "\n".join([str(msg["data"]["content"]) for msg in messages])
            if XiuConfig().img_send_type == "io":
                img_data = await img.io_draw_to(messages)
            elif XiuConfig().img_send_type == "base64":
                img_data = img.sync_draw_to(messages)
            if isinstance(event, GroupMessageEvent):
                await bot.send_group_msg(
                    group_id=event.group_id, message=MessageSegment.image(img_data)
                )
            else:
                await bot.send_private_msg(
                    user_id=event.user_id, message=MessageSegment.image(img_data)
                )
        else:
            raise ValueError("参数数量或类型不匹配")


def CommandObjectID() -> int:
    """
    根据消息事件的类型获取对象id
    私聊->用户id
    群聊->群id
    频道->子频道id
    :return: 对象id
    """

    def _event_id(event):
        if event.message_type == "private":
            return event.user_id
        elif event.message_type == "group":
            return event.group_id
        elif event.message_type == "guild":
            return event.channel_id

    return Depends(_event_id)


def number_to(num):
    """
    递归实现，精确为最大单位值 + 小数点后一位
    处理科学计数法表示的数值
    """

    def strofsize(num, level):
        if level >= 29:
            return num, level
        elif num >= 10000:
            num /= 10000
            level += 1
            return strofsize(num, level)
        else:
            return num, level

    units = [
        "",
        "万",
        "亿",
        "兆",
        "京",
        "垓",
        "秭",
        "穰",
        "沟",
        "涧",
        "正",
        "载",
        "极",
        "恒河沙",
        "阿僧祗",
        "那由他",
        "不思议",
        "无量大",
        "万无量大",
        "亿无量大",
        "兆无量大",
        "京无量大",
        "垓无量大",
        "秭无量大",
        "穰无量大",
        "沟无量大",
        "涧无量大",
        "正无量大",
        "载无量大",
        "极无量大",
    ]
    # 处理科学计数法
    if "e" in str(num):
        num = float(f"{num:.1f}")
    num, level = strofsize(num, 0)
    if level >= len(units):
        level = len(units) - 1
    return f"{round(num, 1)}{units[level]}"


async def pic_msg_format(msg, event):
    user_name = event.sender.card if event.sender.card else event.sender.nickname
    result = "@" + user_name + "\n" + msg
    return result


async def handle_send(bot, event, send_group_id, msg: str):
    """处理文本，根据配置发送文本或者图片消息"""
    if XiuConfig().img:
        pic = await get_msg_pic(f"@{event.sender.nickname}\n" + msg)
        await bot.send_group_msg(
            group_id=int(send_group_id),
            message=MessageSegment.image(pic),
        )
    else:
        await bot.send_group_msg(group_id=int(send_group_id), message=msg)


def append_draw_card_node(bot: Bot, list_tp: list, summary: str, content):
    """添加节点进转发消息

    Args:
        list_tp (list): 要制作的转发消息列表
        summary (str): 转发消息的标题
        content (_type_): 转发消息的内容
    """
    list_tp.append(
        {
            "type": "node",
            "data": {
                "name": summary,
                "uin": bot.self_id,
                "content": content,
            },
        }
    )
