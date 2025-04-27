try:
    import ujson as json
except ImportError:
    import json
import os
import random
import asyncpg
from datetime import datetime, timedelta
from pathlib import Path
from nonebot.log import logger
from .data_source import jsondata
from ..xiuxian_config import XiuConfig, convert_rank
from .. import DRIVER
from .item_json import Items
from typing import Dict, List, Optional, Any
WORKDATA = Path() / "data" / "xiuxian" / "work"
PLAYERSDATA = Path() / "data" / "xiuxian" / "players"
DATABASE = Path() / "data" / "xiuxian"
DATABASE_IMPARTBUFF = Path() / "data" / "xiuxian"
SKILLPATHH = DATABASE / "功法"
WEAPONPATH = DATABASE / "装备"
SEX_VALUES = [
    {"text": "随机", "value": None},
    {"text": "女", "value": True},
    {"text": "男", "value": False}
]
RARITY_COLORS = {
    "common": "#CCCCCC",
    "uncommon": "#222A35",
    "rare": "#00A6A9",
    "epic": "#804DC8",
    "legendary": "#C5C660",
    "mythic": "#F28234",
    "exotic": "#C65043",
}
RARITY_LEVELS = [
    "common",
    "uncommon",
    "rare",
    "epic", 
    "legendary",
    "mythic",
    "exotic",
]
RARITY_VALUES = {
    "common": 1.0,     # 灰
    "uncommon": 0.35,  # 白
    "rare": 0.15,      # 蓝
    "epic": 0.075,     # 紫
    "legendary": 0.03, # 橙
    "mythic": 0.012,   # 金
    "exotic": 0.005,   # 虹
}
RARITY_NAMES = {
    "common": "凡品",
    "uncommon": "良品",
    "rare": "上品",
    "epic": "极品", 
    "legendary": "秘宝",
    "mythic": "灵宝",
    "exotic": "古宝",
}
CREATURE_CATEGORY = ["plant", "worm", "fish", "beast", "bird", "reptile", "insect"]
CREATURE_CATEGORY_NAMES = {
    "plant": "草木",
    "worm": "赢虫",
    "fish": "鱼",
    "beast": "兽",
    "bird": "鸟",
    "reptile": "爬虫",
    "insect": "甲虫",
}
ZONE_CATEGORIES = ["land", "water", "void"]
# 特殊符号常量
_PARENTHESIS_LEFT = "（"
_PARENTHESIS_RIGHT = "）"
_BOOK_LEFT = "《"
_BOOK_RIGHT = "》"
_LINK_WORD = "之"
_NUMBER_BEGIN_SUPPLEMENT = "路"
_NUMBER_END_SUPPLEMENT = "式"
_COUNTRY = "国"
_AGE1 = "百年"
_AGE10 = "千年"
_AGE100 = "万年"
xiuxian_num = "578043031" # 这里其实是修仙1作者的QQ号
items = Items()



class XiuxianDataManage:
    global xiuxian_num
    _instance = {}
    _has_init = {}
    _pool = None
    __slots__ = []

    def __new__(cls):
        if cls._instance.get(xiuxian_num) is None:
            cls._instance[xiuxian_num] = super(XiuxianDataManage, cls).__new__(cls)
        return cls._instance[xiuxian_num]

    def __init__(self):
        if not self._has_init.get(xiuxian_num):
            self._has_init[xiuxian_num] = True
    
    async def _init_db_and_pool(self):
        """初始化数据库和连接池"""
        if XiuxianDataManage._pool is None:
            try:
                pg_url = XiuConfig().postgresql_url
                pg_url_parts = pg_url.split('/')
                base_pg_url = '/'.join(pg_url_parts[:-1]) + '/postgres'
                conn = await asyncpg.connect(base_pg_url)
                try:
                    exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
                        "xiuxian"
                    )
                    
                    if not exists:
                        # 创建数据库
                        await conn.execute("CREATE DATABASE xiuxian")
                        logger.opt(colors=True).info(f"<green>数据库xiuxian创建成功！</green>")
                except Exception as e:
                    logger.opt(colors=True).error(f"<red>检查或创建数据库时出错：{e}</red>")
                    raise e
                finally:
                    await conn.close()
                    
                XiuxianDataManage._pool = await asyncpg.create_pool(
                    pg_url,
                    min_size=10,
                    max_size=50,
                    command_timeout=30.0,
                    max_inactive_connection_lifetime=600.0,
                    max_queries=50000,
                    statement_cache_size=1000,
                    timeout=30.0
                )
                logger.opt(colors=True).info(f"<green>修仙PostgreSQL数据库连接池已创建！</green>")
                await self._check_data()
            except Exception as e:
                logger.opt(colors=True).error(f"<red>PostgreSQL连接池创建失败：{e}</red>")
                raise e

    @property
    def pool(self):
        """获取连接池"""
        if XiuxianDataManage._pool is None:
            raise Exception("数据库连接池尚未初始化，请先调用_init_pool方法")
        return XiuxianDataManage._pool

    async def close(self):
        """关闭数据库连接池"""
        if XiuxianDataManage._pool:
            await XiuxianDataManage._pool.close()
            XiuxianDataManage._pool = None
            logger.opt(colors=True).info(f"<green>修仙PostgreSQL数据库连接池已关闭！</green>")

    @classmethod
    async def close_dbs(cls):
        """关闭所有数据库连接"""
        await XiuxianDataManage().close()

    async def _check_data(self):
        """检查数据完整性并创建必要的表和列"""
        import datetime
        from nonebot.log import logger

        current_time = datetime.datetime.now()
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("SELECT count(1) FROM xiuxian_user LIMIT 1")
            except asyncpg.exceptions.UndefinedTableError:
                logger.opt(colors=True).info(f"<yellow>xiuxian_user表不存在，开始创建</yellow>")
                await conn.execute("""
                CREATE TABLE xiuxian_user (
                  "id" SERIAL PRIMARY KEY,
                  "user_id" BIGINT NOT NULL,
                  "sect_id" BIGINT DEFAULT NULL,
                  "sect_position" BIGINT DEFAULT NULL,
                  "stone" BIGINT DEFAULT 0,
                  "root" TEXT,
                  "root_type" TEXT,
                  "level" TEXT,
                  "power" BIGINT DEFAULT 0,
                  "create_time" TIMESTAMP,
                  "is_sign" BIGINT DEFAULT 0,
                  "is_beg" BIGINT DEFAULT 0,
                  "is_ban" BIGINT DEFAULT 0,
                  "exp" BIGINT DEFAULT 0,
                  "user_name" TEXT DEFAULT NULL,
                  "level_up_cd" TIMESTAMP DEFAULT NULL,
                  "level_up_rate" BIGINT DEFAULT 0,
                  "hp" BIGINT DEFAULT 100,
                  "mp" BIGINT DEFAULT 100,
                  "atk" BIGINT DEFAULT 10,
                  "atkpractice" BIGINT DEFAULT 0,
                  "sect_task" BIGINT DEFAULT 0,
                  "sect_contribution" BIGINT DEFAULT 0,
                  "sect_elixir_get" BIGINT DEFAULT 0,
                  "blessed_spot_flag" BIGINT DEFAULT 0,
                  "blessed_spot_name" TEXT DEFAULT NULL,
                  "user_stamina" BIGINT DEFAULT 240,
                  "work_num" BIGINT DEFAULT 0
                )""")
                logger.opt(colors=True).info(f"<green>xiuxian_user表创建成功</green>")
                
                await conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_xiuxian_user_user_id ON xiuxian_user(user_id);
                CREATE INDEX IF NOT EXISTS idx_xiuxian_user_sect_id ON xiuxian_user(sect_id);
                CREATE INDEX IF NOT EXISTS idx_xiuxian_user_exp ON xiuxian_user(exp);
                CREATE INDEX IF NOT EXISTS idx_xiuxian_user_power ON xiuxian_user(power);
                CREATE INDEX IF NOT EXISTS idx_xiuxian_user_stone ON xiuxian_user(stone);
                CREATE INDEX IF NOT EXISTS idx_xiuxian_user_level ON xiuxian_user(level);
                CREATE INDEX IF NOT EXISTS idx_xiuxian_user_user_name ON xiuxian_user(user_name);
                """)
                logger.opt(colors=True).info(f"<green>xiuxian_user表索引创建成功</green>")

            try:
                await conn.execute("SELECT count(1) FROM xiuxian_time LIMIT 1")
            except asyncpg.exceptions.UndefinedTableError:
                logger.opt(colors=True).info(f"<yellow>xiuxian_time表不存在，开始创建</yellow>")
                await conn.execute("""
                CREATE TABLE xiuxian_time (
                  "id" SERIAL PRIMARY KEY,
                  "user_id" BIGINT DEFAULT 0,
                  "type" BIGINT DEFAULT 0,
                  "create_time" TIMESTAMP DEFAULT NULL,
                  "scheduled_time" BIGINT,
                  "last_check_info_time" TIMESTAMP DEFAULT NULL
                )""")
                logger.opt(colors=True).info(f"<green>xiuxian_time表创建成功</green>")
                
                await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_xiuxian_time_create_time ON xiuxian_time(create_time);
                CREATE INDEX IF NOT EXISTS idx_xiuxian_time_type ON xiuxian_time(type);
                """)
                logger.opt(colors=True).info(f"<green>xiuxian_time表索引创建成功</green>")
                
            try:
                await conn.execute("SELECT count(1) FROM xiuxian_buff LIMIT 1")
            except asyncpg.exceptions.UndefinedTableError:
                logger.opt(colors=True).info(f"<yellow>xiuxian_buff表不存在，开始创建</yellow>")
                await conn.execute("""
                CREATE TABLE xiuxian_buff (
                  "id" SERIAL PRIMARY KEY,
                  "user_id" BIGINT DEFAULT 0,
                  "main_buff" BIGINT DEFAULT 0,
                  "sec_buff" BIGINT DEFAULT 0,
                  "faqi_buff" BIGINT DEFAULT 0,
                  "fabao_weapon" BIGINT DEFAULT 0,
                  "armor_buff" BIGINT DEFAULT 0,
                  "atk_buff" BIGINT DEFAULT 0,
                  "sub_buff" BIGINT DEFAULT 0,
                  "blessed_spot" BIGINT DEFAULT 0
                )""")
                logger.opt(colors=True).info(f"<green>xiuxian_buff表创建成功</green>")
                
                await conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_xiuxian_buff_user_id ON xiuxian_buff(user_id);
                """)
                logger.opt(colors=True).info(f"<green>xiuxian_buff表索引创建成功</green>")
                
            for i in XiuConfig().sql_table:
                if i == "xiuxian_sect":
                    try:
                        await conn.execute("SELECT count(1) FROM xiuxian_sect LIMIT 1")
                    except asyncpg.exceptions.UndefinedTableError:
                        await conn.execute("""
                        CREATE TABLE xiuxian_sect (
                          "sect_id" SERIAL PRIMARY KEY,
                          "sect_name" TEXT NOT NULL,
                          "sect_owner" BIGINT,
                          "sect_scale" BIGINT NOT NULL,
                          "sect_used_stone" BIGINT,
                          "sect_fairyland" BIGINT DEFAULT 0,
                          "sect_materials" BIGINT DEFAULT 0,
                          "mainbuff" BIGINT DEFAULT 0,
                          "secbuff" BIGINT DEFAULT 0,
                          "elixir_room_level" BIGINT DEFAULT 0
                        )""")
                        
                        await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_xiuxian_sect_owner ON xiuxian_sect(sect_owner);
                        CREATE INDEX IF NOT EXISTS idx_xiuxian_sect_scale ON xiuxian_sect(sect_scale);
                        CREATE INDEX IF NOT EXISTS idx_xiuxian_sect_name ON xiuxian_sect(sect_name);
                        """)
                        logger.opt(colors=True).info(f"<green>xiuxian_sect表及索引创建成功</green>")
                        
                elif i == "xiuxian_back":
                    try:
                        await conn.execute("SELECT count(1) FROM xiuxian_back LIMIT 1")
                    except asyncpg.exceptions.UndefinedTableError:
                        await conn.execute("""
                        CREATE TABLE xiuxian_back (
                          "user_id" BIGINT NOT NULL,
                          "goods_id" BIGINT NOT NULL,
                          "goods_name" TEXT,
                          "goods_type" TEXT,
                          "goods_num" BIGINT,
                          "create_time" TIMESTAMP,
                          "update_time" TIMESTAMP,
                          "remake" TEXT,
                          "day_num" BIGINT DEFAULT 0,
                          "all_num" BIGINT DEFAULT 0,
                          "action_time" TIMESTAMP,
                          "state" BIGINT DEFAULT 0,
                          "bind_num" BIGINT DEFAULT 0
                        )""")
                        
                        await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_xiuxian_back_user_id ON xiuxian_back(user_id);
                        CREATE INDEX IF NOT EXISTS idx_xiuxian_back_goods_id ON xiuxian_back(goods_id);
                        CREATE INDEX IF NOT EXISTS idx_xiuxian_back_user_goods ON xiuxian_back(user_id, goods_id);
                        CREATE INDEX IF NOT EXISTS idx_xiuxian_back_goods_type ON xiuxian_back(goods_type);
                        CREATE INDEX IF NOT EXISTS idx_xiuxian_back_update_time ON xiuxian_back(update_time);
                        """)
                        logger.opt(colors=True).info(f"<green>xiuxian_back表及索引创建成功</green>")
                        
                elif i == "xiuxian_buff":
                    try:
                        await conn.execute("SELECT count(1) FROM xiuxian_buff LIMIT 1")
                    except asyncpg.exceptions.UndefinedTableError:
                        await conn.execute("""
                        CREATE TABLE xiuxian_buff (
                          "id" SERIAL PRIMARY KEY,
                          "user_id" BIGINT DEFAULT 0,
                          "main_buff" BIGINT DEFAULT 0,
                          "sec_buff" BIGINT DEFAULT 0,
                          "faqi_buff" BIGINT DEFAULT 0,
                          "fabao_weapon" BIGINT DEFAULT 0,
                          "sub_buff" BIGINT DEFAULT 0
                        )""")

                        await conn.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_xiuxian_buff_user_id ON xiuxian_buff(user_id);
                        """)
                        logger.opt(colors=True).info(f"<green>xiuxian_buff表索引创建成功</green>")
                        
                elif i == "xiuxian_impart":
                    try:
                        await conn.execute("SELECT count(1) FROM xiuxian_impart LIMIT 1")
                    except asyncpg.exceptions.UndefinedTableError:
                        await conn.execute("""
                        CREATE TABLE xiuxian_impart (
                          "user_id" BIGINT PRIMARY KEY,
                          "impart_hp_per" BIGINT DEFAULT 0,
                          "impart_atk_per" BIGINT DEFAULT 0,
                          "impart_mp_per" BIGINT DEFAULT 0,
                          "impart_exp_up" BIGINT DEFAULT 0,
                          "boss_atk" BIGINT DEFAULT 0,
                          "impart_know_per" BIGINT DEFAULT 0,
                          "impart_burst_per" BIGINT DEFAULT 0,
                          "impart_mix_per" BIGINT DEFAULT 0,
                          "impart_reap_per" BIGINT DEFAULT 0,
                          "impart_two_exp" BIGINT DEFAULT 0,
                          "impart_all_exp" BIGINT DEFAULT 0,
                          "impart_wish" BIGINT DEFAULT 0,
                          "stone_num" BIGINT DEFAULT 0,
                          "exp_day_num" BIGINT DEFAULT 0
                        )""")
                        
            # 检查列是否存在，若不存在则添加
            for i in XiuConfig().sql_user:
                try:
                    await conn.execute(f"SELECT {i} FROM xiuxian_user LIMIT 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info(f"<yellow>xiuxian_user表有字段不存在，开始创建: {i}</yellow>")
                    sql = f"ALTER TABLE xiuxian_user ADD COLUMN {i} BIGINT DEFAULT 0"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await conn.execute(sql)

            for d in XiuConfig().sql_time:
                try:
                    await conn.execute(f"SELECT {d} FROM xiuxian_time LIMIT 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info(f"<yellow>xiuxian_time表有字段不存在，开始创建: {d}</yellow>")
                    sql = f"ALTER TABLE xiuxian_time ADD COLUMN {d} BIGINT DEFAULT 0"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await conn.execute(sql)

            for s in XiuConfig().sql_sect:
                try:
                    await conn.execute(f"SELECT {s} FROM xiuxian_sect LIMIT 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info(f"<yellow>xiuxian_sect表有字段不存在，开始创建: {s}</yellow>")
                    sql = f"ALTER TABLE xiuxian_sect ADD COLUMN {s} BIGINT DEFAULT 0"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await conn.execute(sql)

            for m in XiuConfig().sql_buff:
                try:
                    await conn.execute(f"SELECT {m} FROM xiuxian_buff LIMIT 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info(f"<yellow>xiuxian_buff表有字段不存在，开始创建: {m}</yellow>")
                    sql = f"ALTER TABLE xiuxian_buff ADD COLUMN {m} BIGINT DEFAULT 0"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await conn.execute(sql)

            for b in XiuConfig().sql_back:
                try:
                    await conn.execute(f"SELECT {b} FROM xiuxian_back LIMIT 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info(f"<yellow>xiuxian_back表有字段不存在，开始创建: {b}</yellow>")
                    sql = f"ALTER TABLE xiuxian_back ADD COLUMN {b} BIGINT DEFAULT 0"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await conn.execute(sql)

            for col in XiuConfig().sql_impart:
                try:
                    await conn.execute(f"SELECT {col} FROM xiuxian_impart LIMIT 1")
                except asyncpg.exceptions.UndefinedColumnError:
                    logger.opt(colors=True).info(f"<yellow>xiuxian_impart表有字段不存在，开始创建: {col}</yellow>")
                    sql = f"ALTER TABLE xiuxian_impart ADD COLUMN {col} BIGINT DEFAULT 0"
                    logger.opt(colors=True).info(f"<green>{sql}</green>")
                    await conn.execute(sql)
            
            try:
                await conn.execute("""
                UPDATE xiuxian_time
                SET last_check_info_time = $1
                WHERE last_check_info_time IS NULL
                """, current_time)
            except asyncpg.exceptions.UndefinedTableError:
                pass

    @classmethod
    async def close_dbs(cls):
        """关闭所有数据库连接"""
        await XiuxianDataManage().close()

    async def _create_user(self, user_id: int, root: str, type: str, power: str, create_time: str, user_name: str) -> None:
        """在数据库中创建用户并初始化"""
        async with self.pool.acquire() as conn:
            sql = """
            INSERT INTO xiuxian_user 
            (user_id, stone, root, root_type, level, power, create_time, user_name, exp, sect_id, sect_position, user_stamina) 
            VALUES ($1, 0, $2, $3, '江湖好手', $4, $5, $6, 100, NULL, NULL, $7)
            """
            await conn.execute(sql, user_id, root, type, power, create_time, user_name, XiuConfig().max_stamina)


    async def get_user_info_with_name(self, user_name: str):
        """根据user_name获取用户信息"""
        async with self.pool.acquire() as conn:
            sql = "SELECT * FROM xiuxian_user WHERE user_name = $1"
            result = await conn.fetchrow(sql, user_name)
            if result:
                return dict(result)
            else:
                return None
        
    async def update_all_users_stamina(self, max_stamina: int, stamina: int):
        """更新所有用户体力"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    f"UPDATE xiuxian_user SET user_stamina = LEAST(user_stamina + {stamina}, {max_stamina})"
                )
                logger.opt(colors=True).info(f"<green>已为所有用户恢复体力：+{stamina}，最大值：{max_stamina}</green>")

    async def update_user_stamina(self, user_id: int, stamina_change: int, key: int):
        """更新用户体力值 0为增加，1为减少"""
        async with self.pool.acquire() as conn:
            if key == 0:
                sql = f"UPDATE xiuxian_user SET user_stamina = user_stamina + $1 WHERE user_id = $2"
                await conn.execute(sql, stamina_change, user_id)
            elif key == 1:
                sql = f"UPDATE xiuxian_user SET user_stamina = user_stamina - $1 WHERE user_id = $2"
                await conn.execute(sql, stamina_change, user_id)

    async def get_user_real_info(self, user_id: int):
        """根据USER_ID获取用户信息,获取功法加成"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT * FROM xiuxian_user WHERE user_id = $1"
            result = await conn.fetchrow(sql, int(user_id))
            if result:
                user_dict = dict(result)
                user_data_dict = await final_user_data(user_dict, None)
                return user_data_dict
            else:
                return None

    async def get_sect_info(self, sect_id: int):
        """
        通过宗门编号获取宗门信息
        :param sect_id: 宗门编号
        :return:
        """
        async with self.pool.acquire() as conn:
            sql = f"SELECT * from xiuxian_sect WHERE sect_id = $1"
            result = await conn.fetchrow(sql, sect_id)
            if result:
                return dict(result)
            else:
                return None
        
    async def get_sect_owners(self):
        """获取所有宗主的 user_id"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT user_id FROM xiuxian_user WHERE sect_position = 0"
            result = await conn.fetch(sql)
            return [row[0] for row in result]
    

    async def get_elders(self):
        """获取所有长老的user_id"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT user_id FROM xiuxian_user WHERE sect_position = 1"
            result = await conn.fetch(sql)
            return [row[0] for row in result]

    async def create_user(self, user_id: int, *args: str):
        """校验用户是否存在"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT * FROM xiuxian_user WHERE user_id = $1"
            result = await conn.fetchrow(sql, int(user_id))
            if not result:
                await self._create_user(user_id, args[0], args[1], args[2], args[3], args[4]) # root, type, power, create_time, user_name
                welcome_msg = f"欢迎进入修仙世界的，你的灵根为：{args[0]},类型是：{args[1]},你的战力为：{args[2]},当前境界：江湖好手"
                return True, welcome_msg
            else:
                return False, f"您已经迈入修仙世界\n输入【我的修仙信息】获取数据吧！"

    async def get_sign(self, user_id: int):
        """获取用户签到信息"""
        async with self.pool.acquire() as conn:
            sql = "SELECT is_sign FROM xiuxian_user WHERE user_id = $1"
            result = await conn.fetchval(sql, int(user_id))
            if result is None:
                return f"修仙界没有你的足迹，输入 我要修仙 加入修仙世界吧！"
            elif result == 0:
                ls = random.randint(XiuConfig().sign_in_lingshi_lower_limit, XiuConfig().sign_in_lingshi_upper_limit)
                sql2 = f"UPDATE xiuxian_user SET is_sign = 1, stone = stone + $1 WHERE user_id = $2"
                await conn.execute(sql2, ls, user_id)
                
                return f"签到成功，获取{ls}块灵石!"
            elif result == 1:
                return f"贪心的人是不会有好运的！"
        
    async def get_beg(self, user_id: int):
        """获取仙途奇缘信息"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT is_beg FROM xiuxian_user WHERE user_id = $1"
            is_beg = await conn.fetchval(sql, int(user_id))
            if is_beg == 0:
                ls = random.randint(XiuConfig().beg_lingshi_lower_limit, XiuConfig().beg_lingshi_upper_limit)
                sql2 = f"UPDATE xiuxian_user SET is_beg = 1, stone = stone + $1 WHERE user_id = $2"
                await conn.execute(sql2, ls, user_id)
                
                return ls
            elif is_beg == 1:
                return None

    async def ramaker(self, lg: str, type: str, user_id: int):
        """洗灵根"""
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_user SET root = $1, root_type = $2, stone = stone - $3 WHERE user_id = $4"
            await conn.execute(sql, lg, type, XiuConfig().remake, user_id)
            await self.update_power2(user_id)
            return f"逆天之行，重获新生，新的灵根为：{lg}，类型为：{type}"

    async def get_root_rate(self, name: str):
        """获取灵根倍率"""
        data = jsondata.root_data()
        return data[name]['type_speeds']

    async def get_level_power(self, name: str):
        """获取境界倍率|exp"""
        data = jsondata.level_data()
        return data[name]['power']
    
    async def get_level_cost(self, name: str):
        """获取炼体境界倍率"""
        data = jsondata.exercises_level_data()
        return data[name]['cost_exp'], data[name]['cost_stone']

    async def update_power2(self, user_id: int) -> None:
        """更新战力"""
        UserMessage = await self.get_user_infos_by_ids(user_id)
        if not UserMessage:
            return
            
        async with self.pool.acquire() as conn:
            level = jsondata.level_data()
            power = int(level[UserMessage['level']]['power']) * float(await self.get_root_rate(UserMessage['root_type']))
            sql = f"UPDATE xiuxian_user SET power = $1 WHERE user_id = $2"
            await conn.execute(sql, int(power), user_id)

    async def update_ls(self, user_id: int, price: int, key: int):
        """更新灵石  0为增加，1为减少"""
        price = int(price)
        
        async with self.pool.acquire() as conn:
            if key == 0:
                sql = f"UPDATE xiuxian_user SET stone = stone + $1 WHERE user_id = $2"
                await conn.execute(sql, price, user_id)
                
            elif key == 1:
                sql = f"UPDATE xiuxian_user SET stone = stone - $1 WHERE user_id = $2"
                await conn.execute(sql, price, user_id)
                

    async def update_root(self, user_id: int, key: int):
        """更新灵根  1为混沌,2为融合,3为超,4为龙,5为天,6为千世,7为万世"""
        async with self.pool.acquire() as conn:
            if int(key) == 1:
                sql = f"UPDATE xiuxian_user SET root = $1, root_type = $2 WHERE user_id = $3"
                await conn.execute(sql, "全属性灵根", "混沌灵根", user_id)
                root_name = "混沌灵根"
                
            
            elif int(key) == 2:
                sql = f"UPDATE xiuxian_user SET root = $1, root_type = $2 WHERE user_id = $3"
                await conn.execute(sql, "融合万物灵根", "融合灵根", user_id)
                root_name = "融合灵根"
                
                
            elif int(key) == 3:
                sql = f"UPDATE xiuxian_user SET root = $1, root_type = $2 WHERE user_id = $3"
                await conn.execute(sql, "月灵根", "超灵根", user_id)
                root_name = "超灵根"
                
                
            elif int(key) == 4:
                sql = f"UPDATE xiuxian_user SET root = $1, root_type = $2 WHERE user_id = $3"
                await conn.execute(sql, "言灵灵根", "龙灵根", user_id)
                root_name = "龙灵根"
                
                
            elif int(key) == 5:
                sql = f"UPDATE xiuxian_user SET root = $1, root_type = $2 WHERE user_id = $3"
                await conn.execute(sql, "金灵根", "天灵根", user_id)
                root_name = "天灵根"
                
                
            elif int(key) == 6:
                sql = f"UPDATE xiuxian_user SET root = $1, root_type = $2 WHERE user_id = $3"
                await conn.execute(sql, "轮回千次不灭，只为臻至巅峰", "轮回道果", user_id)
                root_name = "轮回道果"
                
                
            elif int(key) == 7:
                sql = f"UPDATE xiuxian_user SET root = $1, root_type = $2 WHERE user_id = $3"
                await conn.execute(sql, "轮回万次不灭，只为超越巅峰", "真·轮回道果", user_id)
                root_name = "真·轮回道果"
                

            return root_name
        
    async def update_ls_all(self, price: int):
        """所有用户增加灵石"""
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_user SET stone = stone + $1"
            await conn.execute(sql, price)
            
    
    async def get_exp_rank(self, user_id: int):
        """修为排行"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT rank from(SELECT user_id,exp,dense_rank() over (ORDER BY exp desc) as rank FROM xiuxian_user) WHERE user_id = $1"
            rank = await conn.fetchval(sql, int(user_id))
            return rank

    async def get_stone_rank(self, user_id: int):
        """灵石排行"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT rank from(SELECT user_id,stone,dense_rank() over (ORDER BY stone desc) as rank FROM xiuxian_user) WHERE user_id = $1"
            rank = await conn.fetchval(sql, int(user_id))
            return rank
    
    async def get_ls_rank(self):
        """灵石排行榜"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT user_id,stone FROM xiuxian_user  WHERE stone > 0 ORDER BY stone DESC LIMIT 5"
            result = await conn.fetch(sql, )
            return result

    async def sign_remake(self):
        """重置签到"""
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_user SET is_sign = 0"
            await conn.execute(sql, )
            

    async def beg_remake(self):
        """重置仙途奇缘"""
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_user SET is_beg = 0"
            await conn.execute(sql, )
            

    async def ban_user(self, user_id: int):
        """小黑屋"""
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_user SET is_ban = 1 WHERE user_id = $1"
            await conn.execute(sql, int(user_id))
            

    async def update_user_name(self, user_id: int, user_name: str):
        """更新用户道号"""
        async with self.pool.acquire() as conn:
            get_name = f"SELECT user_name FROM xiuxian_user WHERE user_name = $1"
            result = await conn.fetchval(get_name, user_name)
            if result:
                return "已存在该道号！"
            else:
                sql = f"UPDATE xiuxian_user SET user_name = $1 WHERE user_id = $2"
                await conn.execute(sql, user_name, user_id)
                
                return '道友的道号更新成功拉~'

    async def updata_level_cd(self, user_id: int):
        """更新突破境界CD"""
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_user SET level_up_cd = $1 WHERE user_id = $2"
            await conn.execute(sql, datetime.now(), user_id)
            
    
    async def update_last_check_info_time(self, user_id: int):
        """更新查看修仙信息时间"""
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_time SET last_check_info_time = $1 WHERE user_id = $2"
            await conn.execute(sql, datetime.now(), user_id)
            

    async def get_last_check_info_time(self, user_id: int):
        """获取最后一次查看修仙信息时间"""
        async with self.pool.acquire() as conn:
            sql = f"SELECT last_check_info_time FROM xiuxian_time WHERE user_id = $1"
            time_str = await conn.fetchval(sql, int(user_id))
            if time_str:
                if isinstance(time_str, datetime):
                    return time_str
                else:
                    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
            else:
                return None


    async def updata_level(self, user_id: int, level_name: str):
        """更新境界"""
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_user SET level = $1 WHERE user_id = $2"
            await conn.execute(sql, level_name, user_id)
            


    async def get_user_cd(self, user_id: int):
        """
        获取用户操作CD
        :param user_id: QQ
        :return: 用户CD信息的字典
        """
        async with self.pool.acquire() as conn:
            sql = f"SELECT * FROM xiuxian_time WHERE user_id = $1"
            result = await conn.fetchrow(sql, int(user_id))
            if result:
                return dict(result)
            else:
                await self.insert_user_cd(user_id)
                return None

    async def insert_user_cd(self, user_id: int) -> None:
        """
        添加用户至CD表
        :param user_id: qq
        :return:
        """
        async with self.pool.acquire() as conn:
            sql = f"INSERT INTO xiuxian_time (user_id) VALUES ($1)"
            await conn.execute(sql, int(user_id))
            


    async def create_sect(self, user_id: int, sect_name: str) -> None:
        """
        创建宗门
        :param user_id:qq
        :param sect_name:宗门名称
        :return:
        """
        async with self.pool.acquire() as conn:
            sql = f"INSERT INTO xiuxian_sect(sect_name, sect_owner, sect_scale, sect_used_stone) VALUES ($1,$2,0,0)"
            await conn.execute(sql, sect_name, user_id)
            

    async def update_sect_name(self, sect_id: int, sect_name: str) -> None:
        """
        修改宗门名称
        :param sect_id: 宗门id
        :param sect_name: 宗门名称
        :return: 返回是否更新成功的标志，True表示更新成功，False表示更新失败（已存在同名宗门）
        """
        async with self.pool.acquire() as conn:
            get_sect_name = f"SELECT sect_name from xiuxian_sect WHERE sect_name = $1"
            result = await conn.fetchrow(get_sect_name, sect_name)
            if result:
                return False
            else:
                sql = f"UPDATE xiuxian_sect SET sect_name = $1 WHERE sect_id = $2"
                await conn.execute(sql, sect_name, sect_id)
                
                return True

    async def get_sect_info_by_qq(self, user_id: int):
        """
        通过用户id获取所在宗门信息
        :param user_id:
        :return:
        """
        async with self.pool.acquire() as conn:
            sql = f"SELECT * from xiuxian_sect WHERE sect_owner = $1"
            result = await conn.fetchrow(sql, int(user_id))
            if result:
                return dict(result)
            else:
                return None

    async def get_sect_info_by_id(self, sect_id: int):
        """
        通过宗门id获取宗门信息
        :param sect_id:
        :return:
        """
        async with self.pool.acquire() as conn:
            sql = f"SELECT * from xiuxian_sect WHERE sect_id = $1"
            result = await conn.fetchrow(sql, sect_id)
            if result:
                return dict(result)
            else:
                return None
        

    async def update_usr_sect(self, user_id: int, usr_sect_id: int, usr_sect_position: int):
        """
        更新用户信息表的宗门信息字段
        :param user_id:
        :param usr_sect_id:
        :param usr_sect_position:
        :return:
        """
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_user SET sect_id = $1,sect_position = $2 WHERE user_id = $3"
            await conn.execute(sql, usr_sect_id, usr_sect_position, user_id)
            

    async def update_sect_owner(self, user_id: int, sect_id: int):
        """
        更新宗门所有者
        :param user_id:
        :param usr_sect_id:
        :return:
        """
        async with self.pool.acquire() as conn:
            sql = f"UPDATE xiuxian_sect SET sect_owner = $1 WHERE sect_id = $2"
            await conn.execute(sql, user_id, sect_id)
            

    async def get_highest_contrib_user_except_current(self, sect_id: int, current_owner_id: int):
        """
        获取指定宗门的贡献最高的人，排除当前宗主
        :param sect_id: 宗门ID
        :param current_owner_id: 当前宗主的ID
        :return: 贡献最高的人的ID，如果没有则返回None
        """
        async with self.pool.acquire() as conn:
            sql = """
            SELECT user_id
            FROM xiuxian_user
            WHERE sect_id = $1 AND sect_position = 1 AND user_id != $2
            ORDER BY sect_contribution DESC
            LIMIT 1
        """
            result = await conn.fetchval(sql, sect_id, current_owner_id)
            return result

    async def get_highest_contrib_active_user_except_current(self, sect_id: int, current_owner_id: int):
        """
        获取指定宗门的贡献最高且最近7天内活跃的成员，排除当前宗主
        :param sect_id: 宗门ID
        :param current_owner_id: 当前宗主的ID
        :return: 贡献最高且活跃的成员ID，如果没有则返回None
        """
        async with self.pool.acquire() as conn:
            days_ago = datetime.now() - timedelta(days=XiuConfig().auto_change_sect_owner_cd)
            
            sql = """
            SELECT u.user_id
            FROM xiuxian_user u
            JOIN xiuxian_time c ON u.user_id = c.user_id
            WHERE u.sect_id = $1 
            AND u.sect_position = 1 
            AND u.user_id != $2
            AND c.last_check_info_time > $3
            ORDER BY u.sect_contribution DESC
            LIMIT 1
            """
            result = await conn.fetchval(sql, sect_id, current_owner_id, days_ago)
            return result


    async def get_all_sect_id(self):
        """获取全部宗门id"""
        async with self.pool.acquire() as conn:
            sql = "SELECT sect_id FROM xiuxian_sect"
            result = await conn.fetch(sql)
            if result:
                return result
            else:
                return None

    async def get_all_user_id(self):
        """获取全部用户id"""
        async with self.pool.acquire() as conn:
            sql = "SELECT user_id FROM xiuxian_user"
            result = await conn.fetch(sql)
            if result:
                return [row[0] for row in result]
            else:
                return None


    async def in_closing(self, user_id: int, the_type: int):
        """
        更新用户操作CD
        :param user_id: qq
        :param the_type: 0:无状态  1:闭关中  2:历练中
        :return:
        """
        now_time = None
        if the_type == 1:
            now_time = datetime.now()
        elif the_type == 0:
            now_time = None
        elif the_type == 2:
            now_time = datetime.now()
        async with self.pool.acquire() as conn:
            sql = "UPDATE xiuxian_time SET type = $1, create_time = $2 WHERE user_id = $3"
            await conn.execute(sql, the_type, now_time, user_id)
            


    async def update_exp(self, user_id: int, exp: int, key: int):
        """更新修为，key=0增加修为，key=1减少修为"""
        async with self.pool.acquire() as conn:
            if key == 0:
                sql = "UPDATE xiuxian_user SET exp = exp + $1 WHERE user_id = $2"
            elif key == 1:
                sql = "UPDATE xiuxian_user SET exp = exp - $1 WHERE user_id = $2"
            await conn.execute(sql, int(exp), user_id)
            


    async def del_exp_decimal(self, user_id: int, exp: float):
        """去浮点"""
        async with self.pool.acquire() as conn:
            sql = "UPDATE xiuxian_user SET exp = exp - $1 WHERE user_id = $2"
            await conn.execute(sql, int(exp), user_id)
            

    
    async def realm_top(self):
        """境界排行榜前50"""
        rank_mapping = {rank: idx for idx, rank in enumerate(convert_rank('江湖好手')[1])}
    
        sql = """SELECT user_name, level, exp FROM xiuxian_user 
            WHERE user_name IS NOT NULL
            ORDER BY exp DESC, (CASE level """
    
        for level, value in sorted(rank_mapping.items(), key=lambda x: x[1], reverse=True):
            sql += f"WHEN '{level}' THEN '{value:02}' "
    
        sql += """ELSE level END) ASC LIMIT 50"""
    
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql)
            return result


    async def stone_top(self):
        """这也是灵石排行榜"""
        sql = f"SELECT user_name,stone FROM xiuxian_user WHERE user_name is NOT NULL ORDER BY stone DESC LIMIT 50"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql)
            return result

    async def power_top(self):
        """战力排行榜"""
        sql = f"SELECT user_name,power FROM xiuxian_user WHERE user_name is NOT NULL ORDER BY power DESC LIMIT 50"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql)
            return result

    async def scale_top(self):
        """
        宗门建设度排行榜
        :return:
        """
        sql = f"SELECT sect_id, sect_name, sect_scale FROM xiuxian_sect WHERE sect_owner is NOT NULL ORDER BY sect_scale DESC"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql)
            return result


    async def get_all_sects(self):
        """
        获取所有宗门信息
        :return: 宗门信息字典列表
        """
        sql = f"SELECT * FROM xiuxian_sect WHERE sect_owner is NOT NULL"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql)
            results = []
            columns = [column[0] for column in result.description]
            for row in result:
                sect_dict = dict(zip(columns, row))
                results.append(sect_dict)
            return results


    async def get_all_sects_with_member_count(self):
        """
        获取所有宗门及其各个宗门成员数
        """
        async with self.pool.acquire() as conn:
            sql = """
            SELECT s.sect_id, s.sect_name, s.sect_scale, (SELECT user_name FROM xiuxian_user WHERE user_id = s.sect_owner) as user_name, COUNT(ux.user_id) as member_count
            FROM xiuxian_sect s LEFT JOIN user_xiuxian ux ON s.sect_id = ux.sect_id GROUP BY s.sect_id
            """
            results = await conn.fetch(sql)
            return results


    async def update_user_is_beg(self, user_id: int, is_beg: int):
        """
        更新用户的最后奇缘时间

        :param user_id: 用户ID
        :param is_beg: 'YYYY-MM-DD HH:MM:SS'
        """
        async with self.pool.acquire() as conn:
            sql = "UPDATE xiuxian_user SET is_beg = $1 WHERE user_id = $2"
            await conn.execute(sql, is_beg, user_id)
            


    async def get_top1_user(self):
        """
        获取修为第一的用户
        """
        async with self.pool.acquire() as conn:
            sql = f"SELECT * FROM xiuxian_user ORDER BY exp DESC LIMIT 1"
            result = await conn.fetch(sql)
            if result:
                return dict(result[0])
            else:
                return None
        
    async def get_realm_top1_user(self):
        """
        获取境界第一的用户
        """
        rank_mapping = {rank: idx for idx, rank in enumerate(convert_rank('江湖好手')[1])}
    
        sql = """SELECT user_name, level, exp FROM xiuxian_user 
            WHERE user_name IS NOT NULL
            ORDER BY exp DESC, (CASE level """
    
        for level, value in sorted(rank_mapping.items(), key=lambda x: x[1], reverse=True):
            sql += f"WHEN '{level}' THEN '{value:02}' "
    
        sql += """ELSE level END) ASC LIMIT 1"""
    
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql)
            if result:
                return dict(result[0])
            else:
                return None
        

    async def donate_update(self, sect_id: int, stone_num: int):
        """宗门捐献更新建设度及可用灵石"""
        sql = f"UPDATE xiuxian_sect SET sect_used_stone=sect_used_stone + $1,sect_scale=sect_scale + $2 WHERE sect_id = $3"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, stone_num, stone_num * 1, sect_id)
            


    async def update_sect_used_stone(self, sect_id: int, sect_used_stone: int, key: int):
        """更新宗门灵石储备  0为增加,1为减少"""
        async with self.pool.acquire() as conn:
            if key == 0:
                sql = f"UPDATE xiuxian_sect SET sect_used_stone=sect_used_stone + $1 WHERE sect_id = $2"
                await conn.execute(sql, sect_used_stone, sect_id)
                
            elif key == 1:
                sql = f"UPDATE xiuxian_sect SET sect_used_stone=sect_used_stone - $1 WHERE sect_id = $2"
                await conn.execute(sql, sect_used_stone, sect_id)
                


    async def update_sect_materials(self, sect_id: int, sect_materials: int, key: int):
        """更新资材  0为增加,1为减少"""
        async with self.pool.acquire() as conn:
            if key == 0:
                sql = f"UPDATE xiuxian_sect SET sect_materials=sect_materials + $1 WHERE sect_id = $2"
                await conn.execute(sql, sect_materials, sect_id)
                
            elif key == 1:
                sql = f"UPDATE xiuxian_sect SET sect_materials=sect_materials - $1 WHERE sect_id = $2"
                await conn.execute(sql, sect_materials, sect_id)
                

    async def get_all_sects_id_scale(self):
        """
        获取所有宗门信息
        :return
        :result[0] = sect_id   
        :result[1] = 建设度 sect_scale,
        :result[2] = 丹房等级 elixir_room_level 
        """
        sql = f"SELECT sect_id, sect_scale, elixir_room_level FROM xiuxian_sect WHERE sect_owner is NOT NULL ORDER BY sect_scale DESC"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql)
            return result

    async def get_all_users_by_sect_id(self, sect_id: int):
        """
        获取宗门所有成员信息
        :return: 成员列表
        """
        sql = f"SELECT * FROM xiuxian_user WHERE sect_id = $1"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql, sect_id)
            results = []
            for user in result:
                user_dict = dict(user)
                results.append(user_dict)
            return results

    async def do_work(self, user_id: int, the_type: int, sc_time: str | None = None):
        """
        更新用户操作CD
        :param sc_time: 任务
        :param user_id: qq
        :param the_type: 0:无状态  1:闭关中  2:历练中  3:探索秘境中
        :param the_time: 本次操作的时长
        :return:
        """
        now_time = None
        if the_type == 1:
            now_time = datetime.now()
        elif the_type == 0:
            now_time = None
        elif the_type == 2:
            now_time = datetime.now()
        elif the_type == 3:
            now_time = datetime.now()
            
        # 确保sc_time是正确的类型，修复整数类型转换错误
        sql = f"UPDATE xiuxian_time SET type = $1, create_time = $2, scheduled_time = $3 WHERE user_id = $4"
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(sql, the_type, now_time, sc_time, user_id)
            except Exception as e:
                # 在出现类型转换错误时，尝试将sc_time设为None
                if "cannot be interpreted as an integer" in str(e):
                    await conn.execute(sql, the_type, now_time, None, user_id)
                else:
                    raise e

    async def update_levelrate(self, user_id: int, rate: int):
        """更新突破成功率"""
        sql = f"UPDATE xiuxian_user SET level_up_rate = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, rate, user_id)
            

    async def update_user_attribute(self, user_id: int, hp: int, mp: int, atk: int):
        """更新用户HP,MP,ATK信息"""
        sql = f"UPDATE xiuxian_user SET hp = $1,mp = $2,atk = $3 WHERE user_id = $4"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, hp, mp, atk, user_id)
            

    async def update_user_hp_mp(self, user_id: int, hp: int, mp: int):
        """更新用户HP,MP信息"""
        sql = f"UPDATE xiuxian_user SET hp = $1,mp = $2 WHERE user_id = $3"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, hp, mp, user_id)
            

    async def update_user_sect_contribution(self, user_id: int, sect_contribution: int):
        """更新用户宗门贡献度"""
        sql = f"UPDATE xiuxian_user SET sect_contribution = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, sect_contribution, user_id)
            

    async def update_user_hp(self, user_id: int):
        """重置用户hp,mp信息"""
        sql = f"UPDATE xiuxian_user SET hp = exp / 2,mp = exp, atk = exp / 10 WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, int(user_id))
            

    async def restate(self, user_id: int = None):
        """重置所有用户状态或重置对应人状态"""
        if user_id is None:
            sql = f"UPDATE xiuxian_user SET hp = exp / 2,mp = exp, atk = exp / 10"
            async with self.pool.acquire() as conn:
                await conn.execute(sql, )
                
        else:
            sql = f"UPDATE xiuxian_user SET hp = exp / 2,mp = exp, atk = exp / 10 WHERE user_id = $1"
            async with self.pool.acquire() as conn:
                await conn.execute(sql, int(user_id))
    

    async def get_user_infos_by_ids(self, user_ids):
        """批量获取用户信息，优化高并发场景下的多用户查询
        
        Args:
            user_ids: 用户ID或用户ID列表
            
        Returns:
            Dict[int, dict]或单个dict: 用户ID到用户信息的映射字典，如果输入单个ID则返回单个用户信息
        """
        # 处理单个ID的情况
        is_single_id = False
        if isinstance(user_ids, int) or (isinstance(user_ids, str) and user_ids.isdigit()):
            is_single_id = True
            user_ids = [int(user_ids)]
            
        if not user_ids:
            return {} if not is_single_id else None
            
        async with self.pool.acquire() as conn:
            placeholders = ','.join(f'${i+1}' for i in range(len(user_ids)))
            
            sql = f"""
            SELECT * FROM xiuxian_user 
            WHERE user_id IN ({placeholders})
            """
            
            rows = await conn.fetch(sql, *user_ids)

            result = {}
            for row in rows:
                user_id = row["user_id"]
                result[user_id] = dict(row)
                
            # 如果是单个ID，直接返回对应的用户信息字典或None
            if is_single_id:
                return result.get(int(user_ids[0])) if result else None
                
            return result

    async def auto_recover_hp(self):
        """自动回血函数"""
        sql = f"""
        UPDATE xiuxian_user 
        SET hp = LEAST(hp + exp * 0.001, exp / 2)
        WHERE hp < exp / 2
        """
        async with self.pool.acquire() as conn:
            await conn.execute(sql)

    async def get_back_msg(self, user_id: int):
        """获取用户背包信息"""
        sql = f"SELECT * FROM xiuxian_back WHERE user_id = $1 and goods_num >= 1"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql, int(user_id))
            if not result:
                return None
    
            results = []
            for row in result:
                back_dict = dict(row)
                results.append(back_dict)
            return results


    async def get_goods_num(self, user_id: int, goods_id: int):
        """
        判断用户物品数量
        :param user_id: 用户qq
        :param goods_id: 物品id
        :return: 物品数量
        """
        sql = "SELECT num FROM xiuxian_back WHERE user_id = $1 and goods_id = $2"
        async with self.pool.acquire() as conn:
            result = await conn.fetchmany(sql, user_id, goods_id)
            if result:
                return result[0]
            else:
                return 0

    async def get_all_user_exp(self, level: str):
        """查询所有对应大境界玩家的修为"""
        sql = f"SELECT exp FROM xiuxian_user  WHERE level like '{level}%'"
        async with self.pool.acquire() as conn:
            result = await conn.fetch(sql, )
            return result

    async def update_user_atkpractice(self, user_id: int, atkpractice: int):
        """更新用户攻击修炼等级"""
        sql = f"UPDATE xiuxian_user SET atkpractice = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, atkpractice, user_id)
            

    async def update_user_sect_task(self, user_id: int, sect_task: int):
        """更新用户宗门任务次数"""
        sql = f"UPDATE xiuxian_user SET sect_task = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, sect_task, user_id)
            

    async def sect_task_reset(self):
        """重置宗门任务次数"""
        sql = f"UPDATE xiuxian_user SET sect_task = 0"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, )
            

    async def update_sect_scale_and_used_stone(self, sect_id: int, sect_used_stone: int, sect_scale: int):
        """更新宗门灵石、建设度"""
        sql = f"UPDATE xiuxian_sect SET sect_used_stone = $1, sect_scale = $2 WHERE sect_id = $3"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, sect_used_stone, sect_scale, sect_id)
            

    async def update_sect_elixir_room_level(self, sect_id: int, level: int):
        """更新宗门丹房等级"""
        sql = f"UPDATE xiuxian_sect SET elixir_room_level = $1 WHERE sect_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, level, sect_id)
            

    async def update_user_sect_elixir_get_num(self, user_id: int):
        """更新用户每日领取丹药领取次数"""
        sql = f"UPDATE xiuxian_user SET sect_elixir_get = 1 WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, int(user_id))
            

    async def sect_elixir_get_num_reset(self):
        """重置宗门丹药领取次数"""
        sql = f"UPDATE xiuxian_user SET sect_elixir_get = 0"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, )
            

    async def update_sect_mainbuff(self, sect_id: int, mainbuffid: int):
        """更新宗门当前的主修功法"""
        sql = f"UPDATE xiuxian_sect SET mainbuff = $1 WHERE sect_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, mainbuffid, sect_id)
            

    async def update_sect_secbuff(self, sect_id: int, secbuffid: int):
        """更新宗门当前的神通"""
        sql = f"UPDATE xiuxian_sect SET secbuff = $1 WHERE sect_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, secbuffid, sect_id)
            

    async def initialize_user_buff_info(self, user_id: int):
        """初始化用户buff信息"""
        sql = f"INSERT INTO xiuxian_buff (user_id,main_buff,sec_buff,faqi_buff,fabao_weapon) VALUES ($1,0,0,0,0)"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, int(user_id))
            

    async def get_user_buff_info(self, user_id: int):
        """获取用户buff信息"""
        sql = f"SELECT * from xiuxian_buff WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(sql, int(user_id))
            if result:
                return dict(result)
            else:
                return None
        
    async def updata_user_main_buff(self, user_id: int, id: int):
        """更新用户主功法信息"""
        sql = f"UPDATE xiuxian_buff SET main_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, id, user_id)
            
    
    async def updata_user_sub_buff(self, user_id: int, id: int): #辅修功法3
        """更新用户辅修功法信息"""
        sql = f"UPDATE xiuxian_buff SET sub_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, id, user_id)
            
    
    async def updata_user_sec_buff(self, user_id: int, id: int):
        """更新用户副功法信息"""
        sql = f"UPDATE xiuxian_buff SET sec_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, id, user_id)
            

    async def updata_user_faqi_buff(self, user_id: int, id: int):
        """更新用户法器信息"""
        sql = f"UPDATE xiuxian_buff SET faqi_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, id, user_id)
            

    async def updata_user_fabao_weapon(self, user_id: int, id: int):
        """更新用户法宝信息"""
        sql = f"UPDATE xiuxian_buff SET fabao_weapon = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, id, user_id)
            

    async def updata_user_armor_buff(self, user_id: int, id: int):
        """更新用户防具信息"""
        sql = f"UPDATE xiuxian_buff SET armor_buff = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, id, user_id)
            

    async def updata_user_atk_buff(self, user_id: int, buff: int):
        """更新用户永久攻击buff信息"""
        sql = f"UPDATE xiuxian_buff SET atk_buff = atk_buff + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, buff, user_id)
            

    async def updata_user_blessed_spot(self, user_id: int, blessed_spot: int):
        """更新用户洞天福地等级"""
        sql = f"UPDATE xiuxian_buff SET blessed_spot = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, blessed_spot, user_id)
            

    async def update_user_blessed_spot_flag(self, user_id: int):
        """更新用户洞天福地是否开启"""
        sql = f"UPDATE xiuxian_user SET blessed_spot_flag = 1 WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, int(user_id))
            

    async def update_user_blessed_spot_name(self, user_id: int, blessed_spot_name: str):
        """更新用户洞天福地的名字"""
        sql = f"UPDATE xiuxian_user SET blessed_spot_name = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, blessed_spot_name, user_id)
            

    async def day_num_reset(self):
        """重置丹药每日使用次数"""
        sql = f"UPDATE xiuxian_back SET day_num = 0 WHERE goods_type = '丹药'"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, )
            

    async def reset_work_num(self):
        """重置用户悬赏令刷新次数"""
        sql = f"UPDATE xiuxian_user SET work_num = 0"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, )
            

    async def get_work_num(self, user_id: int):
        """获取用户悬赏令刷新次数"""
        sql = f"SELECT work_num FROM xiuxian_user WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            work_num = await conn.fetchval(sql, int(user_id))
            return work_num
    
    
    async def update_work_num(self, user_id: int, work_num: int):
        sql = f"UPDATE xiuxian_user SET work_num = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, work_num, user_id)
            

    async def send_back(self, user_id: int, goods_id: int, goods_name: str, goods_type: str, goods_num: int, bind_flag: int = 0):
        """
        插入物品至背包
        :param user_id: 用户qq
        :param goods_id: 物品id
        :param goods_name: 物品名称
        :param goods_type: 物品类型
        :param goods_num: 物品数量
        :param bind_flag: 是否绑定物品,0-非绑定,1-绑定
        :return: None
        """
        now_time = datetime.now()
        goods_id = int(goods_id)
        # 检查物品是否存在，存在则update
        back = await self.get_item_by_good_id_and_user_id(user_id, goods_id)
        if back:
            # 判断是否存在，存在则update
            if bind_flag == 1:
                bind_num = back['bind_num'] + goods_num
            else:
                bind_num = back['bind_num']
            goods_nums = back['goods_num'] + goods_num
            sql = f"UPDATE xiuxian_back set goods_num = $1,update_time = $2,bind_num = $3 WHERE user_id = $4 and goods_id = $5"
            async with self.pool.acquire() as conn:
                await conn.execute(sql, goods_nums, now_time, bind_num, user_id, goods_id)
                
        else:
            # 判断是否存在，不存在则INSERT
            if bind_flag == 1:
                bind_num = goods_num
            else:
                bind_num = 0
            sql = f"""INSERT INTO xiuxian_back (user_id, goods_id, goods_name, goods_type, goods_num, create_time, update_time, bind_num)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)"""
            async with self.pool.acquire() as conn:
                await conn.execute(sql, user_id, goods_id, goods_name, goods_type, goods_num, now_time, now_time, bind_num)
                


    async def get_item_by_good_id_and_user_id(self, user_id: int, goods_id: int):
        """根据物品id、用户id获取物品信息"""
        # 确保goods_id是整数类型
        goods_id = int(goods_id)
        sql = f"SELECT * FROM xiuxian_back WHERE user_id = $1 and goods_id = $2"
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(sql, user_id, goods_id)
            if not result:
                return None
            else:
                return dict(result)


    async def update_back_equipment(self, sql_str: str):
        """更新背包,传入sql"""
        async with self.pool.acquire() as conn:
            await conn.execute(sql_str)
            

    async def reset_user_drug_resistance(self, user_id: int):
        """重置用户耐药性"""
        sql = f"UPDATE xiuxian_back SET all_num = 0 WHERE goods_type = '丹药' and user_id = $1"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, int(user_id))
            

    async def update_back_j(self, user_id: int, goods_id: int, num: int = 1, use_key: int = 0):
        """
        使用物品
        :num 减少数量  默认1
        :use_key 是否使用，丹药使用才传 默认0
        """
        back = await self.get_item_by_good_id_and_user_id(user_id, goods_id)
        if back['goods_type'] == "丹药" and use_key == 1:  # 丹药要判断耐药性、日使用上限
            if back['bind_num'] >= 1:
                bind_num = back['bind_num'] - num  # 优先使用绑定物品
            else:
                bind_num = back['bind_num']
            day_num = back['day_num'] + num
            all_num = back['all_num'] + num
        else:
            bind_num = back['bind_num']
            day_num = back['day_num']
            all_num = back['all_num']
        goods_num = back['goods_num'] - num
        now_time = datetime.now()
        sql = f"UPDATE xiuxian_back set update_time = $1,action_time = $2,goods_num = $3,day_num = $4,all_num = $5,bind_num = $6 WHERE user_id = $7 and goods_id = $8"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, now_time, now_time, goods_num, day_num, all_num, bind_num, user_id, goods_id)
            
    

    # 从这里开始是虚神界部分
    async def create_impart_user(self, user_id: str) -> None:
        """在数据库中创建用户并初始化"""
        sql = f"INSERT INTO xiuxian_impart (user_id, impart_hp_per, impart_atk_per, impart_mp_per, impart_exp_up ,boss_atk,impart_know_per,impart_burst_per,impart_mix_per,impart_reap_per,impart_two_exp,stone_num,exp_day,wish) VALUES($1, 0, 0, 0, 0 ,0, 0, 0, 0, 0 ,0 ,0 ,0, 0)"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, int(user_id))
            
            

    async def get_user_impart_info_with_id(self, user_id: int):
        """根据USER_ID获取用户impart_buff信息"""
        sql = f"SELECT * from xiuxian_impart WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(sql, int(user_id))
            if result:
                return dict(result)
            else:
                return None
        

    async def update_impart_hp_per(self, impart_num: int, user_id: int):
        """更新impart_hp_per"""
        sql = f"UPDATE xiuxian_impart SET impart_hp_per = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_hp_per(self, impart_num: int, user_id: int):
        """add impart_hp_per"""
        sql = f"UPDATE xiuxian_impart SET impart_hp_per = impart_hp_per + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_atk_per(self, impart_num: int, user_id: int):
        """更新impart_atk_per"""
        sql = f"UPDATE xiuxian_impart SET impart_atk_per = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_atk_per(self, impart_num: int, user_id: int):
        """增加impart_atk_per"""
        sql = f"UPDATE xiuxian_impart SET impart_atk_per=impart_atk_per + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_mp_per(self, impart_num: int, user_id: int):
        """更新impart_mp_per"""
        sql = f"UPDATE xiuxian_impart SET impart_mp_per = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_mp_per(self, impart_num: int, user_id: int):
        """增加impart_mp_per"""
        sql = f"UPDATE xiuxian_impart SET impart_mp_per=impart_mp_per + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_exp_up(self, impart_num: int, user_id: int):
        """更新impart_exp_up"""
        sql = f"UPDATE xiuxian_impart SET impart_exp_up = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_exp_up(self, impart_num: int, user_id: int):
        """增加impart_exp_up"""
        sql = f"UPDATE xiuxian_impart SET impart_exp_up=impart_exp_up + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_boss_atk(self, impart_num: int, user_id: int):
        """更新boss_atk"""
        sql = f"UPDATE xiuxian_impart SET boss_atk = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_boss_atk(self, impart_num: int, user_id: int):
        """增加boss_atk"""
        sql = f"UPDATE xiuxian_impart SET boss_atk=boss_atk + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_know_per(self, impart_num: int, user_id: int):
        """更新impart_know_per"""
        sql = f"UPDATE xiuxian_impart SET impart_know_per = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_know_per(self, impart_num: int, user_id: int):
        """增加impart_know_per"""
        sql = f"UPDATE xiuxian_impart SET impart_know_per = impart_know_per + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_burst_per(self, impart_num: int, user_id: int):
        """更新impart_burst_per"""
        sql = f"UPDATE xiuxian_impart SET impart_burst_per = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_burst_per(self, impart_num: int, user_id: int):
        """增加impart_burst_per"""
        sql = f"UPDATE xiuxian_impart SET impart_burst_per = impart_burst_per + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_mix_per(self, impart_num: int, user_id: int):
        """更新impart_mix_per"""
        sql = f"UPDATE xiuxian_impart SET impart_mix_per = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_mix_per(self, impart_num: int, user_id: int):
        """增加impart_mix_per"""
        sql = f"UPDATE xiuxian_impart SET impart_mix_per = impart_mix_per + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_reap_per(self, impart_num: int, user_id: int):
        """更新impart_reap_per"""
        sql = f"UPDATE xiuxian_impart SET impart_reap_per = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_reap_per(self, impart_num: int, user_id: int):
        """增加impart_reap_per"""
        sql = f"UPDATE xiuxian_impart SET impart_reap_per = impart_reap_per + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_two_exp(self, impart_num: int, user_id: int):
        """更新双修经验"""
        sql = f"UPDATE xiuxian_impart SET impart_two_exp = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_two_exp(self, impart_num: int, user_id: int):
        """增加双修经验"""
        sql = f"UPDATE xiuxian_impart SET impart_two_exp = impart_two_exp + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_impart_wish(self, impart_num: int, user_id: int):
        """更新抽卡次数"""
        sql = f"UPDATE xiuxian_impart SET wish = $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def add_impart_wish(self, impart_num: int, user_id: int):
        """增加抽卡次数"""
        sql = f"UPDATE xiuxian_impart SET wish = wish + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_num, user_id)
            
        return True

    async def update_stone_num(self, impart_num: int, user_id: int, type_: int):
        """更新结晶数量, 0为增加, 1为减少"""
        if type_ == 0:
            sql = f"UPDATE xiuxian_impart SET stone_num = stone_num + $1 WHERE user_id = $2"
            async with self.pool.acquire() as conn:
                await conn.execute(sql, impart_num, user_id)
                
            return True
        if type_ == 1:
            sql = f"UPDATE xiuxian_impart SET stone_num = stone_num - $1 WHERE user_id = $2"
            async with self.pool.acquire() as conn:
                await conn.execute(sql, impart_num, user_id)
                
            return True

    async def update_impart_stone_all(self, impart_stone: int):
        """所有用户增加结晶"""
        sql = f"UPDATE xiuxian_impart SET stone_num = stone_num + $1"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, impart_stone)
            
        return True

    async def add_impart_exp_day(self, impart_num: int, user_id: int):
        """增加虚神界经验"""
        sql = f"UPDATE xiuxian_impart SET exp_day = exp_day + $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, int(impart_num), int(user_id))
            
        return True

    async def use_impart_exp_day(self, impart_num: int, user_id: int):
        """使用虚神界经验"""
        sql = f"UPDATE xiuxian_impart SET exp_day = exp_day - $1 WHERE user_id = $2"
        async with self.pool.acquire() as conn:
            await conn.execute(sql, int(impart_num), int(user_id))
            
        return True


class XiuxianJsonDate:
    def __init__(self):
        self.root_jsonpath = DATABASE / "灵根.json"
        self.level_jsonpath = DATABASE / "突破概率.json"

    def beifen_linggen_get(self):
        with open(self.root_jsonpath, 'r', encoding='utf-8') as e:
            a = e.read()
            data = json.loads(a)
            lg = random.choice(data)
            return lg['name'], lg['type']

    def level_rate(self, level):
        with open(self.level_jsonpath, 'r', encoding='utf-8') as e:
            a = e.read()
            data = json.loads(a)
            return data[0][level]

    def linggen_get(self):
        """获取灵根信息"""
        data = jsondata.root_data()
        rate_dict = {}
        for i, v in data.items():
            rate_dict[i] = v["type_rate"]
        lgen = OtherSet().calculated(rate_dict)
        if data[lgen]["type_flag"]:
            flag = random.choice(data[lgen]["type_flag"])
            root = random.sample(data[lgen]["type_list"], flag)
            msg = ""
            for j in root:
                if j == root[-1]:
                    msg += j
                    break
                msg += (j + "、")

            return msg + '属性灵根', lgen
        else:
            root = random.choice(data[lgen]["type_list"])
            return root, lgen



class OtherSet(XiuConfig):

    def __init__(self):
        super().__init__()

    async def set_closing_type(self, user_level):
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if list_all == now_index:
            need_exp = 0.001
        else:
            is_updata_level = self.level[now_index + 1]
            need_exp = await XiuxianDataManage().get_level_power(is_updata_level)
        return need_exp

    async def get_type(self, user_exp, rate, user_level):
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if list_all == now_index:
            return "道友已是最高境界，无法突破！"

        is_updata_level = self.level[now_index + 1]
        need_exp = await XiuxianDataManage().get_level_power(is_updata_level)

        # 判断修为是否足够突破
        if user_exp >= need_exp:
            pass
        else:
            return f"道友的修为不足以突破！距离下次突破需要{need_exp - user_exp}修为！突破境界为：{is_updata_level}"

        success_rate = True if random.randint(0, 100) < rate else False

        if success_rate:
            return [self.level[now_index + 1]]
        else:
            return '失败'

    def calculated(self, rate: dict) -> str:
        """
        根据概率计算，轮盘型
        :rate:格式{"数据名":"获取几率"}
        :return: 数据名
        """

        get_list = []  # 概率区间存放

        n = 1
        for name, value in rate.items():  # 生成数据区间
            value_rate = int(value)
            list_rate = [_i for _i in range(n, value_rate + n)]
            get_list.append(list_rate)
            n += value_rate

        now_n = n - 1
        get_random = random.randint(1, now_n)  # 抽取随机数

        index_num = None
        for list_r in get_list:
            if get_random in list_r:  # 判断随机在那个区间
                index_num = get_list.index(list_r)
                break

        return list(rate.keys())[index_num]

    def date_diff(self, new_time, old_time):
        """计算日期差"""
        if isinstance(new_time, datetime):
            pass
        else:
            new_time = datetime.strptime(new_time, '%Y-%m-%d %H:%M:%S.%f')

        if isinstance(old_time, datetime):
            pass
        else:
            old_time = datetime.strptime(old_time, '%Y-%m-%d %H:%M:%S.%f')

        day = (new_time - old_time).days
        sec = (new_time - old_time).seconds

        return (day * 24 * 60 * 60) + sec

    def get_power_rate(self, mind, other):
        """获取修为差距"""
        power_rate = mind / (other + mind)
        if power_rate >= 0.8:
            return "道友偷窃小辈实属天道所不齿！"
        elif power_rate <= 0.05:
            return "道友请不要不自量力！"
        else:
            return int(power_rate * 100)

    async def player_fight(self, player1: dict, player2: dict):
        """
        回合制战斗
        type_in : 1 为完整返回战斗过程（未加）
        2：只返回战斗结果
        数据示例：
        {"道号": None, "气血": None, "攻击": None, "真元": None, '会心':None}
        """
        msg1 = "{}发起攻击，造成了{}伤害\n"
        msg2 = "{}发起攻击，造成了{}伤害\n"

        play_list = []
        suc = None
        if player1['气血'] <= 0:
            player1['气血'] = 1
        if player2['气血'] <= 0:
            player2['气血'] = 1
        while True:
            player1_gj = int(round(random.uniform(0.95, 1.05), 2) * player1['攻击'])
            if random.randint(0, 100) <= player1['会心']:
                player1_gj = int(player1_gj * player1['爆伤'])
                msg1 = "{}发起会心一击，造成了{}伤害\n"

            player2_gj = int(round(random.uniform(0.95, 1.05), 2) * player2['攻击'])
            if random.randint(0, 100) <= player2['会心']:
                player2_gj = int(player2_gj * player2['爆伤'])
                msg2 = "{}发起会心一击，造成了{}伤害\n"

            play1_sh: int = int(player1_gj * (1 - player2['防御']))
            play2_sh: int = int(player2_gj * (1 - player1['防御']))

            play_list.append(msg1.format(player1['道号'], play1_sh))
            player2['气血'] = player2['气血'] - play1_sh
            play_list.append(f"{player2['道号']}剩余血量{player2['气血']}")
            await XiuxianDataManage().update_user_hp_mp(player2['user_id'], player2['气血'], player2['真元'])

            if player2['气血'] <= 0:
                play_list.append(f"{player1['道号']}胜利")
                suc = f"{player1['道号']}"
                await XiuxianDataManage().update_user_hp_mp(player2['user_id'], 1, player2['真元'])
                break

            play_list.append(msg2.format(player2['道号'], play2_sh))
            player1['气血'] = player1['气血'] - play2_sh
            play_list.append(f"{player1['道号']}剩余血量{player1['气血']}\n")
            await XiuxianDataManage().update_user_hp_mp(player1['user_id'], player1['气血'], player1['真元'])

            if player1['气血'] <= 0:
                play_list.append(f"{player2['道号']}胜利")
                suc = f"{player2['道号']}"
                await XiuxianDataManage().update_user_hp_mp(player1['user_id'], 1, player1['真元'])
                break
            if player1['气血'] <= 0 or player2['气血'] <= 0:
                play_list.append("逻辑错误！！！")
                break

        return play_list, suc

    async def send_hp_mp(self, user_id, hp, mp):
        user_msg = await XiuxianDataManage().get_user_infos_by_ids(user_id)
        max_hp = int(user_msg['exp'] / 2)
        max_mp = int(user_msg['exp'])

        msg = []
        hp_mp = []

        if user_msg['hp'] < max_hp:
            if user_msg['hp'] + hp < max_hp:
                new_hp = user_msg['hp'] + hp
                msg.append(f',回复气血：{hp}')
            else:
                new_hp = max_hp
                msg.append(',气血已回满！')
        else:
            new_hp = user_msg['hp']
            msg.append('')

        if user_msg['mp'] < max_mp:
            if user_msg['mp'] + mp < max_mp:
                new_mp = user_msg['mp'] + mp
                msg.append(f',回复真元：{mp}')
            else:
                new_mp = max_mp
                msg.append(',真元已回满！')
        else:
            new_mp = user_msg['mp']
            msg.append('')

        hp_mp.append(new_hp)
        hp_mp.append(new_mp)
        hp_mp.append(user_msg['exp'])

        return msg, hp_mp

# 这里是buff部分
class BuffJsonData:

    def __init__(self):
        """json文件路径"""
        self.mainbuff_jsonpath = SKILLPATHH / "主功法.json"
        self.secbuff_jsonpath = SKILLPATHH / "神通.json"
        self.gfpeizhi_jsonpath = SKILLPATHH / "功法概率设置.json"
        self.weapon_jsonpath = WEAPONPATH / "法器.json"
        self.armor_jsonpath = WEAPONPATH / "防具.json"

    def get_main_buff(self, id):
        return readf(self.mainbuff_jsonpath)[str(id)]

    def get_sec_buff(self, id):
        return readf(self.secbuff_jsonpath)[str(id)]

    def get_gfpeizhi(self):
        return readf(self.gfpeizhi_jsonpath)

    def get_weapon_data(self):
        return readf(self.weapon_jsonpath)

    def get_weapon_info(self, id):
        return readf(self.weapon_jsonpath)[str(id)]

    def get_armor_data(self):
        return readf(self.armor_jsonpath)

    def get_armor_info(self, id):
        return readf(self.armor_jsonpath)[str(id)]


class UserBuffData:
    def __init__(self, user_id):
        """用户Buff数据"""
        self.user_id = user_id
        self._buff_info = None
        self._main_buff_data = None
        self._sub_buff_data = None
        self._sec_buff_data = None
        self._weapon_data = None
        self._armor_buff_data = None

    @property
    async def BuffInfo(self):
        """获取最新的 Buff 信息"""
        if self._buff_info is None:
            self._buff_info = await get_user_buff(self.user_id)
        return self._buff_info

    async def get_user_main_buff_data(self):
        """获取用户主功法数据"""
        if self._main_buff_data is None:
            buff_info = await self.BuffInfo
            main_buff_id = buff_info.get('main_buff', 0)
            if main_buff_id != 0:
                self._main_buff_data = items.get_data_by_item_id(main_buff_id)
        return self._main_buff_data
    
    async def get_user_sub_buff_data(self):
        """获取用户辅修功法数据"""
        if self._sub_buff_data is None:
            buff_info = await self.BuffInfo
            sub_buff_id = buff_info.get('sub_buff', 0)
            if sub_buff_id != 0:
                self._sub_buff_data = items.get_data_by_item_id(sub_buff_id)
        return self._sub_buff_data

    async def get_user_sec_buff_data(self):
        """获取用户神通数据"""
        if self._sec_buff_data is None:
            buff_info = await self.BuffInfo
            sec_buff_id = buff_info.get('sec_buff', 0)
            if sec_buff_id != 0:
                self._sec_buff_data = items.get_data_by_item_id(sec_buff_id)
        return self._sec_buff_data

    async def get_user_weapon_data(self):
        """获取用户法器数据"""
        if self._weapon_data is None:
            buff_info = await self.BuffInfo
            weapon_id = buff_info.get('faqi_buff', 0)
            if weapon_id != 0:
                self._weapon_data = items.get_data_by_item_id(weapon_id)
        return self._weapon_data

    async def get_user_armor_buff_data(self):
        """获取用户防具数据"""
        if self._armor_buff_data is None:
            buff_info = await self.BuffInfo
            armor_buff_id = buff_info.get('armor_buff', 0)
            if armor_buff_id != 0:
                self._armor_buff_data = items.get_data_by_item_id(armor_buff_id)
        return self._armor_buff_data
    

class XiuXianNameGenerator:
    def __init__(self, data_dir: str = ""):
        """初始化修仙名称生成器
        
        Args:
            data_dir: 数据文件目录路径
        """
        self.data_dir = data_dir
        self.data = self._load_data()
        self._validate_data()
        
    def _load_data(self) -> Dict[str, Any]:
        """加载所有JSON数据文件"""
        data = {}
        
        # 加载共享数据
        data["common"] = self._load_json_file("shared/common.json")
        data["strange"] = self._load_json_file("shared/strange.json")
        data["color"] = self._load_json_file("shared/color.json")
        data["spirit"] = self._load_json_file("shared/spirit.json")
        
        # 加载人名数据
        data["family"] = self._load_json_file("name/family.json")
        data["female"] = self._load_json_file("name/female.json")
        data["male"] = self._load_json_file("name/male.json")
        data["middle"] = self._load_json_file("name/middle.json")
        
        # 加载道号数据
        data["dao"] = self._load_json_file("dao/dao.json")
        data["dao_title_male"] = self._load_json_file("dao/title_male.json")
        data["dao_title_female"] = self._load_json_file("dao/title_female.json")
        
        # 加载技能数据
        data["skill"] = self._load_json_file("skill/skill.json")
        data["skill_prefix"] = self._load_json_file("skill/prefix.json")
        data["skill_numfix"] = self._load_json_file("skill/numfix.json")
        
        # 加载书籍数据
        data["book"] = self._load_json_file("book/book.json")
        data["book_prefix"] = self._load_json_file("book/prefix.json")
        data["book_postfix"] = self._load_json_file("book/postfix.json")
        
        # 加载符箓数据
        data["talisman"] = self._load_json_file("talisman/talisman.json")
        data["talisman_material"] = self._load_json_file("talisman/material.json")
        data["talisman_postfix"] = self._load_json_file("talisman/postfix.json")
        
        # 加载组织数据
        data["clan"] = self._load_json_file("organization/clan.json")
        data["nation"] = self._load_json_file("organization/nation.json")
        
        # 加载地点数据
        data["place"] = self._load_json_file("place/place.json")
        data["place_prefix"] = self._load_json_file("place/prefix.json")
        data["place_postfix"] = self._load_json_file("place/postfix.json")
        data["location"] = self._load_json_file("place/location.json")
        data["zone"] = self._load_json_file("place/zone.json")
        
        # 加载材料数据
        data["material"] = self._load_json_file("material/material.json")
        data["material_postfix"] = self._load_json_file("material/postfix.json")
        
        # 加载生物数据
        data["creature"] = self._load_json_file("creature/creature.json")
        data["creature_prefix"] = self._load_json_file("creature/prefix.json")
        data["strange_creature"] = self._load_json_file("creature/strange.json")
        
        # 加载丹药数据
        data["alchemy"] = self._load_json_file("alchemy/alchemy.json")
        
        return data
    
    def _load_json_file(self, file_path: str) -> Any:
        """加载单个JSON文件
        
        Args:
            file_path: 相对于data_dir的文件路径
        
        Returns:
            加载的JSON数据
        """
        full_path = os.path.join(self.data_dir, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"无法加载 {full_path}: {e}")
            return {} if file_path.endswith(".json") else []
    
    def _validate_data(self):
        """验证加载的数据是否完整有效"""
        required_data = [
            "common", "strange", "color", "spirit", 
            "family", "female", "male", "middle",
            "dao", "dao_title_male", "dao_title_female",
            "skill", "skill_prefix", "skill_numfix",
            "book", "book_prefix", "book_postfix",
            "talisman", "talisman_material", "talisman_postfix",
            "clan", "nation",
            "place", "place_prefix", "place_postfix", "location", "zone",
            "material", "material_postfix",
            "creature", "creature_prefix", "strange_creature",
            "alchemy"
        ]
        missing = []
        for item in required_data:
            if not self.data.get(item):
                missing.append(item)
        
        if missing:
            print(f"警告: 以下数据不完整或缺失: {', '.join(missing)}")
    
    @property
    def dao_titles(self) -> List[str]:
        """获取所有道号称号列表"""
        titles = []
        for gender in ["dao_title_male", "dao_title_female"]:
            for rarity in RARITY_LEVELS:
                if gender in self.data and rarity in self.data[gender]:
                    titles.extend(self.data[gender][rarity])
        return list(set(titles))  # 去重
    
    @property
    def book_prefixes(self) -> List[str]:
        """获取所有书籍前缀列表"""
        prefixes = []
        for rarity in ["epic", "legendary", "mythic", "exotic"]:
            if "book_prefix" in self.data and rarity in self.data["book_prefix"]:
                prefixes.extend(self.data["book_prefix"][rarity])
        return prefixes
    
    @property
    def talisman_kind(self) -> List[str]:
        """获取所有符箓类型列表"""
        kinds = []
        for rarity in RARITY_LEVELS:
            if "talisman" in self.data and rarity in self.data["talisman"]:
                kinds.extend(self.data["talisman"][rarity])
        return kinds
    
    @property
    def material_kind(self) -> List[str]:
        """获取所有材料类型列表"""
        kinds = []
        for rarity in RARITY_LEVELS:
            if "material" in self.data and rarity in self.data["material"]:
                kinds.extend(self.data["material"][rarity])
        return kinds
    
    @property
    def material_postfixes(self) -> List[str]:
        """获取所有材料后缀列表"""
        postfixes = []
        for kind in ["broken", "handmade"]:
            if "material_postfix" in self.data and kind in self.data["material_postfix"]:
                postfixes.extend(self.data["material_postfix"][kind])
        return postfixes
    
    @property
    def talisman_postfixes(self) -> List[str]:
        """获取所有符箓后缀列表"""
        postfixes = []
        for kind in ["broken", "handmade"]:
            if "talisman_postfix" in self.data and kind in self.data["talisman_postfix"]:
                postfixes.extend(self.data["talisman_postfix"][kind])
        return postfixes
    
    @property
    def zone_kind(self) -> List[str]:
        """获取所有区域类型列表"""
        kinds = []
        for category in ZONE_CATEGORIES:
            if "zone" in self.data and category in self.data["zone"]:
                kinds.extend(self.data["zone"][category])
        return kinds
    
    @property
    def book_postfixes(self) -> List[str]:
        """获取所有书籍后缀列表"""
        postfixes = []
        for rarity in ["uncommon", "rare"]:
            if "book_postfix" in self.data and rarity in self.data["book_postfix"]:
                postfixes.extend(self.data["book_postfix"][rarity])
        return postfixes
    
    def _get_rarity(self, max_value: float = 1.0) -> Dict[str, str]:
        """获取随机稀有度
        
        Args:
            max_value: 随机值上限
            
        Returns:
            包含稀有度和随机值的字典
        """
        value = random.random() * (max_value or 1.0)
        if value < RARITY_VALUES["exotic"]:
            rarity = "exotic"
        elif value < RARITY_VALUES["mythic"]:
            rarity = "mythic"
        elif value < RARITY_VALUES["legendary"]:
            rarity = "legendary"
        elif value < RARITY_VALUES["epic"]:
            rarity = "epic"
        elif value < RARITY_VALUES["rare"]:
            rarity = "rare"
        elif value < RARITY_VALUES["uncommon"]:
            rarity = "uncommon"
        else:
            rarity = "common"
        return {"rarity": rarity, "value": value}
    
    def get_name(self, number: int = 1, options: Dict = None) -> List[str]:
        """生成人名
        
        Args:
            number: 生成名字的数量
            options: 选项参数，可包含:
                    familyName: 指定姓氏
                    isFemale: 是否女性
                    style: 命名风格('single', 'double', 'combine')
                    middleCharacter: 中间字符
        
        Returns:
            生成的名字列表
        """
        options = options or {}
        names = []
        
        for _ in range(number):
            if options.get("familyName"):
                the_family_name = options["familyName"]
            else:
                family_index = random.randint(0, len(self.data["family"]) - 1)
                the_family_name = self.data["family"][family_index]
            
            is_female = options.get("isFemale", random.randint(0, 1) == 0)
            names_of_a_sex = self.data["female"] if is_female else self.data["male"]
            
            r = random.random()
            style = options.get("style")
            if not style:
                if r < 0.33333333:
                    style = "single"
                elif r < 0.66666666:
                    style = "double"
                else:
                    style = "combine"
            
            name = ""
            if style == "single":
                if options.get("middleCharacter"):
                    name = options["middleCharacter"]
                else:
                    name_index = random.randint(0, len(names_of_a_sex) - 1)
                    name = names_of_a_sex[name_index]
            elif style == "double":
                if options.get("middleCharacter"):
                    the_middle_character = options["middleCharacter"]
                else:
                    name_index = random.randint(0, len(names_of_a_sex) - 1)
                    the_middle_character = names_of_a_sex[name_index]
                
                name_index = random.randint(0, len(names_of_a_sex) - 1)
                the_last_character = names_of_a_sex[name_index]
                name = the_middle_character + the_last_character
            else:
                if options.get("middleCharacter"):
                    the_middle_character = options["middleCharacter"]
                else:
                    name_index = random.randint(0, len(self.data["middle"]) - 1)
                    the_middle_character = self.data["middle"][name_index]
                
                name_index = random.randint(0, len(names_of_a_sex) - 1)
                the_last_character = names_of_a_sex[name_index]
                name = the_middle_character + the_last_character
            
            names.append(the_family_name + name)
        
        return names
    
    def get_dao(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成道号
        
        Args:
            number: 生成道号的数量
            options: 选项参数，可包含:
                    firstCharacter: 第一个字符
                    isFemale: 是否女性
                    title: 称号
        
        Returns:
            生成的道号列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        
        for _ in range(number):
            if options.get("firstCharacter"):
                the_first_character = options["firstCharacter"]
            else:
                name_index1 = random.randint(0, len(self.data["dao"]) - 1)
                the_first_character = self.data["dao"][name_index1]
            
            name_index2 = random.randint(0, len(self.data["dao"]) - 1)
            name = the_first_character + self.data["dao"][name_index2]
            
            is_female = options.get("isFemale", random.randint(0, 1) == 0)
            title_group = self.data["dao_title_female"] if is_female else self.data["dao_title_male"]
            
            t = options.get("title", "")
            rarity = "common"
            
            if not t:
                rarity_info = self._get_rarity()
                rarity = rarity_info["rarity"]
                
                if rarity == "exotic" and title_group.get("exotic"):
                    t = random.choice(title_group["exotic"])
                elif rarity == "mythic" and title_group.get("mythic"):
                    t = random.choice(title_group["mythic"])
                elif rarity == "legendary" and title_group.get("legendary"):
                    t = random.choice(title_group["legendary"])
                elif rarity == "epic" and title_group.get("epic"):
                    t = random.choice(title_group["epic"])
                elif rarity == "rare" and title_group.get("rare"):
                    t = random.choice(title_group["rare"])
                elif rarity == "uncommon" and title_group.get("uncommon"):
                    t = random.choice(title_group["uncommon"])
            else:
                if t in (title_group.get("exotic", []) + self.data["dao_title_male"].get("exotic", [])):
                    rarity = "exotic"
                elif t in (title_group.get("mythic", []) + self.data["dao_title_male"].get("mythic", [])):
                    rarity = "mythic"
                elif t in (title_group.get("legendary", []) + self.data["dao_title_male"].get("legendary", [])):
                    rarity = "legendary"
                elif t in (title_group.get("epic", []) + self.data["dao_title_male"].get("epic", [])):
                    rarity = "epic"
                elif t in (title_group.get("rare", []) + self.data["dao_title_male"].get("rare", [])):
                    rarity = "rare"
                elif t in (title_group.get("uncommon", []) + self.data["dao_title_male"].get("uncommon", [])):
                    rarity = "uncommon"
            
            names.append({"name": name + t, "rarity": rarity})
        
        return names
    
    def _get_skill_name(self, length: Optional[int] = None, kind: Optional[str] = None, 
                       prefix: Optional[str] = None, numfix: Optional[str] = None) -> Dict:
        """生成单个技能名称
        
        Args:
            length: 名称长度
            kind: 技能类型
            prefix: 前缀
            numfix: 数字后缀
            
        Returns:
            包含name和rarity的字典
        """
        l = length or 1
        rarity = "common"
        
        if not length:
            r = self._get_rarity()
            if r["value"] < RARITY_VALUES["rare"]:
                l = 3
            elif r["value"] < RARITY_VALUES["uncommon"]:
                l = 2
            rarity = r["rarity"]
        else:
            if length > 2:
                rarity = "rare"
            elif length > 1:
                rarity = "uncommon"

        common = []
        for category in ["dao", "element", "creature", "thing", "color", "place", 
                         "adj", "number", "gesture", "action"]:
            if category in self.data.get("common", {}):
                common.extend(self.data["common"][category])
        
        name = ""
        for _ in range(l):
            name += random.choice(common)
        
        pre = prefix or ""
        if not pre and random.random() < RARITY_VALUES["epic"]:
            pre = random.choice(self.data["skill_prefix"])
        
        n = numfix or ""
        if not n and random.random() < RARITY_VALUES["epic"]:
            n = random.choice(self.data["skill_numfix"])
        
        k = kind or random.choice(self.data["skill"])
        
        if random.random() < 0.5:
            name = (n + _NUMBER_BEGIN_SUPPLEMENT if n else "") + pre + name + k
        else:
            if len(k) > 1:
                name = pre + name + k + (n + _NUMBER_END_SUPPLEMENT if n else "")
            else:
                name = pre + name + n + k
        
        return {"name": name, "rarity": rarity}
    
    def get_skill(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成功法名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    length: 技能名称长度
                    kind: 技能类型
                    prefix: 前缀
                    numfix: 数字后缀
        
        Returns:
            生成的功法名称列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        
        for _ in range(number):
            name = self._get_skill_name(
                options.get("length"),
                options.get("kind"),
                options.get("prefix"),
                options.get("numfix")
            )
            names.append(name)
        
        return names
    
    def get_book(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成秘籍名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    length: 书名长度
                    mainkind: 主要类型
                    prefix: 前缀
                    postkind: 后缀类型
                    postfix: 后缀
        
        Returns:
            生成的秘籍名称列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        
        for _ in range(number):
            skillname = self._get_skill_name(options.get("length"), options.get("mainkind"))
            rarity = skillname["rarity"]
            
            pre = options.get("prefix", "")
            if not pre:
                if rarity == "exotic" and "exotic" in self.data["book_prefix"]:
                    pre = random.choice(self.data["book_prefix"]["exotic"])
                elif rarity == "mythic" and "mythic" in self.data["book_prefix"]:
                    pre = random.choice(self.data["book_prefix"]["mythic"])
                elif rarity == "legendary" and "legendary" in self.data["book_prefix"]:
                    pre = random.choice(self.data["book_prefix"]["legendary"])
                elif rarity == "epic" and "epic" in self.data["book_prefix"]:
                    pre = random.choice(self.data["book_prefix"]["epic"])
            
            pk = options.get("postkind", "")
            if pre and not pk:
                pk = random.choice(self.data["book"])
            
            post = options.get("postfix", "")
            if not post:
                r1 = random.random()
                r2 = random.random()
                if r1 < RARITY_VALUES["rare"] and r2 < RARITY_VALUES["rare"] and "rare" in self.data["book_postfix"]:
                    post = _PARENTHESIS_LEFT + random.choice(self.data["book_postfix"]["rare"]) + _PARENTHESIS_RIGHT
                elif r1 < RARITY_VALUES["uncommon"] and r2 < RARITY_VALUES["uncommon"] and "uncommon" in self.data["book_postfix"]:
                    post = _PARENTHESIS_LEFT + random.choice(self.data["book_postfix"]["uncommon"]) + _PARENTHESIS_RIGHT
            else:
                post = _PARENTHESIS_LEFT + post + _PARENTHESIS_RIGHT
            
            names.append({
                "name": _BOOK_LEFT + skillname["name"] + pre + pk + post + _BOOK_RIGHT,
                "rarity": rarity
            })
        
        return names
    
    def get_creature(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成生灵名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    category: 生物种类
                    rarity: 稀有度
        
        Returns:
            生成的生灵名称列表，每个元素包含name，rarity和category
        """
        options = options or {}
        names = []
        common_creature_names = []
        for category in ["dao", "element", "thing", "color", "number", "action"]:
            if category in self.data.get("common", {}):
                common_creature_names.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            pre = random.choice(common_creature_names)
            c = random.choice(self.data["color"])
            s = random.choice(self.data["creature_prefix"])
            
            cat = options.get("category")
            if not cat:
                cat = random.choice(CREATURE_CATEGORY)
            
            k = random.choice(self.data["creature"][cat])
            r = options.get("rarity") or self._get_rarity(RARITY_VALUES["uncommon"])["rarity"]
            
            if r == "exotic":
                name = random.choice(self.data["strange_creature"])
            elif r == "mythic":
                name = pre + c + s + k
            elif r == "legendary":
                name = pre + s + k
            elif r == "epic":
                name = pre + c + k
            elif r == "rare":
                name = pre + k
            elif r == "uncommon":
                name = c + s + k
            elif r == "common":
                name = c + k
            
            names.append({"name": name, "rarity": r, "category": cat})
        
        return names
    
    def get_material(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成材料名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    kind: 材料类型
                    rarity: 稀有度
                    postfix: 后缀
        
        Returns:
            生成的材料名称列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            age = ""
            pre = random.choice(common)
            c = random.choice(self.data["color"])
            s = random.choice(self.data["spirit"])
            
            k = options.get("kind")
            r = options.get("rarity") or self._get_rarity(RARITY_VALUES["uncommon"])["rarity"]
            
            if r == "exotic":
                all_materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in self.data["material"]:
                        all_materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(all_materials)
                age = _AGE100
                name = age + pre + c + s + k
            elif r == "mythic":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["mythic", "legendary", "epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                age = _AGE10
                name = age + pre + c + s + k
            elif r == "legendary":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["legendary", "epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                age = _AGE1
                name = age + pre + c + s + k
            elif r == "epic":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                name = pre + c + s + k
            elif r == "rare":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["rare", "uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                name = pre + s + k
            elif r == "uncommon":
                materials = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["uncommon", "common"]:
                        if rarity_level in self.data["material"]:
                            materials.extend(self.data["material"][rarity_level])
                k = k or random.choice(materials)
                name = c + s + k
            elif r == "common":
                if "common" in self.data["material"]:
                    k = k or random.choice(self.data["material"]["common"])
                name = c + k
            
            post = options.get("postfix", "")
            if not post:
                r1 = random.random()
                r2 = random.random()
                if (r1 < RARITY_VALUES["rare"] and r2 < RARITY_VALUES["rare"] and 
                    "broken" in self.data["material_postfix"]):
                    post = (_PARENTHESIS_LEFT + 
                           random.choice(self.data["material_postfix"]["broken"]) + 
                           _PARENTHESIS_RIGHT)
                elif (r1 < RARITY_VALUES["uncommon"] and r2 < RARITY_VALUES["uncommon"] and 
                      "handmade" in self.data["material_postfix"]):
                    post = (_PARENTHESIS_LEFT + 
                           random.choice(self.data["material_postfix"]["handmade"]) + 
                           _PARENTHESIS_RIGHT)
            else:
                post = _PARENTHESIS_LEFT + post + _PARENTHESIS_RIGHT
            
            names.append({"name": name + post, "rarity": r})
        
        return names
    
    def get_talisman(self, number: int = 1, options: Dict = None) -> List[Dict]:
        """生成法宝名称
        
        Args:
            number: 生成名称的数量
            options: 选项参数，可包含:
                    kind: 符箓类型
                    rarity: 稀有度
                    postfix: 后缀
        
        Returns:
            生成的法宝名称列表，每个元素包含name和rarity
        """
        options = options or {}
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            prefix = random.choice(common)
            c = random.choice(self.data["color"])
            m = random.choice(self.data["talisman_material"])
            s = random.choice(self.data["spirit"])
            
            k = options.get("kind")
            r = options.get("rarity") or self._get_rarity(RARITY_VALUES["uncommon"])["rarity"]
            
            if r == "exotic":
                all_talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in self.data["talisman"]:
                        all_talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(all_talismans)
                name = prefix + s + k
            elif r == "mythic":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["mythic", "legendary", "epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = prefix + s + k
            elif r == "legendary":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["legendary", "epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = prefix + c + m + k
            elif r == "epic":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["epic", "rare", "uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = prefix + m + k
            elif r == "rare":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["rare", "uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = prefix + k
            elif r == "uncommon":
                talismans = []
                for rarity_level in RARITY_LEVELS:
                    if rarity_level in ["uncommon", "common"]:
                        if rarity_level in self.data["talisman"]:
                            talismans.extend(self.data["talisman"][rarity_level])
                k = k or random.choice(talismans)
                name = c + m + k
            elif r == "common":
                if "common" in self.data["talisman"]:
                    k = k or random.choice(self.data["talisman"]["common"])
                name = m + k
            
            post = options.get("postfix", "")
            if not post:
                r1 = random.random()
                r2 = random.random()
                if (r1 < RARITY_VALUES["rare"] and r2 < RARITY_VALUES["rare"] and 
                    "broken" in self.data["talisman_postfix"]):
                    post = (_PARENTHESIS_LEFT + 
                           random.choice(self.data["talisman_postfix"]["broken"]) + 
                           _PARENTHESIS_RIGHT)
                elif (r1 < RARITY_VALUES["uncommon"] and r2 < RARITY_VALUES["uncommon"] and 
                      "handmade" in self.data["talisman_postfix"]):
                    post = (_PARENTHESIS_LEFT + 
                           random.choice(self.data["talisman_postfix"]["handmade"]) + 
                           _PARENTHESIS_RIGHT)
            else:
                post = _PARENTHESIS_LEFT + post + _PARENTHESIS_RIGHT
            
            names.append({"name": name + post, "rarity": r})
        
        return names
    
    def get_alchemy(self, number: int = 1, kind: Optional[str] = None) -> List[Dict]:
        """生成丹药名称
        
        Args:
            number: 生成名称的数量
            kind: 丹药类型
        
        Returns:
            生成的丹药名称列表，每个元素包含name和rarity
        """
        names = []
        common_alchemy_names = []
        for category in ["dao", "element", "color", "number", "action"]:
            if category in self.data.get("common", {}):
                common_alchemy_names.extend(self.data["common"][category])
        
        for _ in range(number):
            rarity = "common"
            pre = random.choice(common_alchemy_names)
            s = ""
            
            r = self._get_rarity()
            if r["value"] < RARITY_VALUES["rare"]:
                s = random.choice(self.data["spirit"])
            
            rarity = r["rarity"]
            k = kind or ""
            if not kind:
                k = random.choice(self.data["alchemy"])
            
            names.append({"name": pre + s + k, "rarity": rarity})
        
        return names
    
    def get_clan(self, number: int = 1, kind: Optional[str] = None) -> List[str]:
        """生成门派名称
        
        Args:
            number: 生成名称的数量
            kind: 门派类型
        
        Returns:
            生成的门派名称列表
        """
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = random.choice(common)
            k = kind
            if not k:
                k = random.choice(self.data["clan"])
            
            names.append(name + k)
        
        return names
    
    def get_nation(self, number: int = 1, kind: Optional[str] = None) -> List[Dict]:
        """生成国家名称
        
        Args:
            number: 生成名称的数量
            kind: 国家类型
        
        Returns:
            生成的国家名称列表，每个元素包含name和rarity
        """
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            k = kind or ""
            rarity = "common"
            
            r = random.random()
            if r < RARITY_VALUES["rare"]:
                name = random.choice(self.data["strange"])
                rarity = "rare"
                if not kind:
                    if len(name) == 1:
                        k = _COUNTRY
                    else:
                        k = random.choice(self.data["nation"])
            elif r < RARITY_VALUES["uncommon"]:
                name = random.choice(common)
                rarity = "uncommon"
                if not kind:
                    if len(name) == 1:
                        k = _COUNTRY
                    else:
                        k = random.choice(self.data["nation"])
            else:
                prefix = ""
                if random.random() < RARITY_VALUES["rare"]:
                    prefix = random.choice(self.data["place_prefix"])
                
                name = prefix + random.choice(self.data["place"])
                if not kind:
                    k = _COUNTRY
            
            names.append({"name": name + k, "rarity": rarity})
        
        return names
    
    def get_location(self, number: int = 1, kind: Optional[str] = None) -> List[Dict]:
        """生成据点名称
        
        Args:
            number: 生成名称的数量
            kind: 地点类型
        
        Returns:
            生成的据点名称列表，每个元素包含name和rarity
        """
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            k = kind or ""
            rarity = "common"
            
            r = random.random()
            if r < RARITY_VALUES["rare"]:
                name = random.choice(self.data["strange"])
                rarity = "rare"
            elif r < RARITY_VALUES["uncommon"]:
                name = random.choice(common)
                rarity = "uncommon"
            else:
                place_index = random.randint(0, len(self.data["place"]) - 1)
                postfix = ""
                if random.random() < RARITY_VALUES["uncommon"]:
                    postfix_index = random.randint(0, len(self.data["place_postfix"]) - 1)
                    postfix = self.data["place_postfix"][postfix_index]
                
                name = self.data["place"][place_index] + postfix
            
            if not kind:
                k = random.choice(self.data["location"])
            
            names.append({"name": name + k, "rarity": rarity})
        
        return names
    
    def _get_zone_kind(self, category: Optional[str] = None) -> str:
        """获取地域类型
        
        Args:
            category: 区域类别
        
        Returns:
            地域类型字符串
        """
        category = category or random.choice(ZONE_CATEGORIES)
        group = self.data["zone"][category]
        return random.choice(group)
    
    def get_zone(self, number: int = 1, options_or_kind=None) -> List[Dict]:
        """生成地域名称
        
        Args:
            number: 生成名称的数量
            options_or_kind: 可以是区域类型字符串或包含以下键的选项字典:
                    kind: 区域类型
                    category: 区域类别
        
        Returns:
            生成的地域名称列表，每个元素包含name和rarity
        """
        options = {}
        if isinstance(options_or_kind, str):
            options = {"kind": options_or_kind}
        elif isinstance(options_or_kind, dict):
            options = options_or_kind
        
        names = []
        common = []
        for category in self.data.get("common", {}):
            common.extend(self.data["common"][category])
        
        for _ in range(number):
            name = ""
            k = options.get("kind") or self._get_zone_kind(options.get("category"))
            rarity = "common"
            
            r = random.random()
            if r < RARITY_VALUES["rare"]:
                name = random.choice(self.data["strange"])
                rarity = "rare"
            elif r < RARITY_VALUES["uncommon"]:
                name = random.choice(common)
                rarity = "uncommon"
            else:
                prefix = ""
                if random.random() < RARITY_VALUES["rare"]:
                    prefix = random.choice(self.data["place_prefix"])
                
                name = prefix + random.choice(self.data["place"])
                if len(name) == 1:
                    if len(k) > 1:
                        name += _LINK_WORD
                    else:
                        if random.random() < RARITY_VALUES["rare"]:
                            name += _LINK_WORD
            
            names.append({"name": name + k, "rarity": rarity})
        
        return names



async def final_user_data(user_data, columns):
    """传入用户当前信息、buff信息,返回最终信息"""
    user_dict = user_data
    
    # 通过字段名称获取相应的值
    impart_data = await XiuxianDataManage().get_user_impart_info_with_id(user_dict['user_id'])
    if impart_data is None:
        await XiuxianDataManage().create_impart_user(user_dict['user_id'])

    impart_data = await XiuxianDataManage().get_user_impart_info_with_id(user_dict['user_id'])
    impart_hp_per = impart_data['impart_hp_per'] if impart_data is not None else 0
    impart_mp_per = impart_data['impart_mp_per'] if impart_data is not None else 0
    impart_atk_per = impart_data['impart_atk_per'] if impart_data is not None else 0
    
    user_buff_data = await get_user_buff(user_dict['user_id'])
    
    armor_atk_buff = 0
    if int(user_buff_data['armor_buff']) != 0:
        armor_info = items.get_data_by_item_id(user_buff_data['armor_buff'])
        armor_atk_buff = armor_info['atk_buff']
        
    weapon_atk_buff = 0
    if int(user_buff_data['faqi_buff']) != 0:
        weapon_info = items.get_data_by_item_id(user_buff_data['faqi_buff'])
        weapon_atk_buff = weapon_info['atk_buff']
    
    main_buff_data = await UserBuffData(user_dict['user_id']).get_user_main_buff_data()
    main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
    main_mp_buff = main_buff_data['mpbuff'] if main_buff_data is not None else 0
    main_atk_buff = main_buff_data['atkbuff'] if main_buff_data is not None else 0
    
    # 改成字段名称来获取相应的值
    user_dict['hp'] = int(user_dict['hp'] * (1 + main_hp_buff + impart_hp_per))
    user_dict['mp'] = int(user_dict['mp'] * (1 + main_mp_buff + impart_mp_per))
    user_dict['atk'] = int((user_dict['atk'] * (user_dict['atkpractice'] * 0.04 + 1) * (1 + main_atk_buff) * (
            1 + weapon_atk_buff) * (1 + armor_atk_buff)) * (1 + impart_atk_per)) + int(user_buff_data['atk_buff'])
    
    return user_dict


async def leave_harm_time(user_id):
    """重伤恢复时间"""
    hp_speed = 25
    user_mes = await XiuxianDataManage().get_user_infos_by_ids(user_id)
    level = user_mes['level']
    level_rate = await XiuxianDataManage().get_root_rate(user_mes['root_type']) # 灵根倍率
    realm_rate = jsondata.level_data()[level]["spend"] # 境界倍率
    
    # 获取buff信息并处理主功法数据
    user_buff_data = await get_user_buff(user_id)
    main_buff_data = None
    main_buff_id = user_buff_data.get('main_buff', 0)
    if main_buff_id != 0:
        main_buff_data = items.get_data_by_item_id(main_buff_id)
    main_buff_rate_buff = main_buff_data['ratebuff'] if main_buff_data else 0 # 主功法修炼倍率
    
    try:
       time = int(((user_mes['exp'] / 1.5) - user_mes['hp']) / ((XiuConfig().closing_exp * level_rate * realm_rate * (
                    1 + main_buff_rate_buff)) * hp_speed))
    except ZeroDivisionError:
        time = "无穷大"
    except OverflowError:
        time = "溢出"
    return time


async def impart_check(user_id):
    if await XiuxianDataManage().get_user_impart_info_with_id(user_id) is None:
        await XiuxianDataManage().create_impart_user(user_id)
        return await XiuxianDataManage().get_user_impart_info_with_id(user_id)
    else:
        return await XiuxianDataManage().get_user_impart_info_with_id(user_id)


def get_weapon_info_msg(weapon_id, weapon_info=None):
    """
    获取一个法器(武器)信息msg
    :param weapon_id:法器(武器)ID
    :param weapon_info:法器(武器)信息json,可不传
    :return 法器(武器)信息msg
    """
    msg = ''
    if weapon_info is None:
        weapon_info = items.get_data_by_item_id(weapon_id)
    atk_buff_msg = f"提升{int(weapon_info['atk_buff'] * 100)}%攻击力！" if weapon_info['atk_buff'] != 0 else ''
    crit_buff_msg = f"提升{int(weapon_info['crit_buff'] * 100)}%会心率！" if weapon_info['crit_buff'] != 0 else ''
    crit_atk_msg = f"提升{int(weapon_info['critatk'] * 100)}%会心伤害！" if weapon_info['critatk'] != 0 else ''
    def_buff_msg = f"{'提升' if weapon_info['def_buff'] > 0 else '降低'}{int(abs(weapon_info['def_buff']) * 100)}%减伤率！" if weapon_info['def_buff'] != 0 else ''
    zw_buff_msg = f"装备专属武器时提升伤害！！" if weapon_info['zw'] != 0 else ''
    mp_buff_msg = f"降低真元消耗{int(weapon_info['mp_buff'] * 100)}%！" if weapon_info['mp_buff'] != 0 else ''
    msg += f"名字：{weapon_info['name']}\n"
    msg += f"品阶：{weapon_info['level']}\n"
    msg += f"效果：{atk_buff_msg}{crit_buff_msg}{crit_atk_msg}{def_buff_msg}{mp_buff_msg}{zw_buff_msg}"
    return msg


def get_armor_info_msg(armor_id, armor_info=None):
    """
    获取一个法宝(防具)信息msg
    :param armor_id:法宝(防具)ID
    :param armor_info;法宝(防具)信息json,可不传
    :return 法宝(防具)信息msg
    """
    msg = ''
    if armor_info is None:
        armor_info = items.get_data_by_item_id(armor_id)
    def_buff_msg = f"提升{int(armor_info['def_buff'] * 100)}%减伤率！"
    atk_buff_msg = f"提升{int(armor_info['atk_buff'] * 100)}%攻击力！" if armor_info['atk_buff'] != 0 else ''
    crit_buff_msg = f"提升{int(armor_info['crit_buff'] * 100)}%会心率！" if armor_info['crit_buff'] != 0 else ''
    msg += f"名字：{armor_info['name']}\n"
    msg += f"品阶：{armor_info['level']}\n"
    msg += f"效果：{def_buff_msg}{atk_buff_msg}{crit_buff_msg}"
    return msg


def get_main_info_msg(id):
    """获取一个主功法信息msg"""
    mainbuff = items.get_data_by_item_id(id)
    hpmsg = f"提升{round(mainbuff['hpbuff'] * 100, 0)}%气血" if mainbuff['hpbuff'] != 0 else ''
    mpmsg = f"，提升{round(mainbuff['mpbuff'] * 100, 0)}%真元" if mainbuff['mpbuff'] != 0 else ''
    atkmsg = f"，提升{round(mainbuff['atkbuff'] * 100, 0)}%攻击力" if mainbuff['atkbuff'] != 0 else ''
    ratemsg = f"，提升{round(mainbuff['ratebuff'] * 100, 0)}%修炼速度" if mainbuff['ratebuff'] != 0 else ''
    
    cri_tmsg = f"，提升{round(mainbuff['crit_buff'] * 100, 0)}%会心率" if mainbuff['crit_buff'] != 0 else ''
    def_msg = f"，{'提升' if mainbuff['def_buff'] > 0 else '降低'}{round(abs(mainbuff['def_buff']) * 100, 0)}%减伤率" if mainbuff['def_buff'] != 0 else ''
    dan_msg = f"，增加炼丹产出{round(mainbuff['dan_buff'])}枚" if mainbuff['dan_buff'] != 0 else ''
    dan_exp_msg = f"，每枚丹药额外增加{round(mainbuff['dan_exp'])}炼丹经验" if mainbuff['dan_exp'] != 0 else ''
    reap_msg = f"，提升药材收取数量{round(mainbuff['reap_buff'])}个" if mainbuff['reap_buff'] != 0 else ''
    exp_msg = f"，突破失败{round(mainbuff['exp_buff'] * 100, 0)}%经验保护" if mainbuff['exp_buff'] != 0 else ''
    critatk_msg = f"，提升{round(mainbuff['critatk'] * 100, 0)}%会心伤害" if mainbuff['critatk'] != 0 else ''
    two_msg = f"，增加{round(mainbuff['two_buff'])}次双修次数" if mainbuff['two_buff'] != 0 else ''
    number_msg = f"，提升{round(mainbuff['number'])}%突破概率" if mainbuff['number'] != 0 else ''
    
    clo_exp_msg = f"，提升{round(mainbuff['clo_exp'] * 100, 0)}%闭关经验" if mainbuff['clo_exp'] != 0 else ''
    clo_rs_msg = f"，提升{round(mainbuff['clo_rs'] * 100, 0)}%闭关生命回复" if mainbuff['clo_rs'] != 0 else ''
    random_buff_msg = f"，战斗时随机获得一个战斗属性" if mainbuff['random_buff'] != 0 else ''
    ew_msg =  f"，使用专属武器时伤害增加50%！" if mainbuff['ew'] != 0 else ''
    msg = f"{mainbuff['name']}: {hpmsg}{mpmsg}{atkmsg}{ratemsg}{cri_tmsg}{def_msg}{dan_msg}{dan_exp_msg}{reap_msg}{exp_msg}{critatk_msg}{two_msg}{number_msg}{clo_exp_msg}{clo_rs_msg}{random_buff_msg}{ew_msg}！"
    return mainbuff, msg

def get_sub_info_msg(id): #辅修功法8
    """获取辅修信息msg"""
    subbuff = items.get_data_by_item_id(id)
    submsg = ""
    if subbuff['buff_type'] == '1':
        submsg = "提升" + subbuff['buff'] + "%攻击力"
    if subbuff['buff_type'] == '2':
        submsg = "提升" + subbuff['buff'] + "%暴击率"
    if subbuff['buff_type'] == '3':
        submsg = "提升" + subbuff['buff'] + "%暴击伤害"
    if subbuff['buff_type'] == '4':
        submsg = "提升" + subbuff['buff'] + "%每回合气血回复"
    if subbuff['buff_type'] == '5':
        submsg = "提升" + subbuff['buff'] + "%每回合真元回复"
    if subbuff['buff_type'] == '6':
        submsg = "提升" + subbuff['buff'] + "%气血吸取"
    if subbuff['buff_type'] == '7':
        submsg = "提升" + subbuff['buff'] + "%真元吸取"
    if subbuff['buff_type'] == '8':
        submsg = "给对手造成" + subbuff['buff'] + "%中毒"
    if subbuff['buff_type'] == '9':
        submsg = f"提升{subbuff['buff']}%气血吸取,提升{subbuff['buff2']}%真元吸取"

    stone_msg  = "提升{}%boss战灵石获取".format(round(subbuff['stone'] * 100, 0)) if subbuff['stone'] != 0 else ''
    integral_msg = "，提升{}点boss战积分获取".format(round(subbuff['integral'])) if subbuff['integral'] != 0 else ''
    jin_msg = "禁止对手吸取" if subbuff['jin'] != 0 else ''
    drop_msg = "，提升boss掉落率" if subbuff['drop'] != 0 else ''
    fan_msg = "使对手发出的debuff失效" if subbuff['fan'] != 0 else ''
    break_msg = "获得战斗破甲" if subbuff['break'] != 0 else ''
    exp_msg = "，增加战斗获得的修为" if subbuff['exp'] != 0 else ''
    

    msg = f"{subbuff['name']}：{submsg}{stone_msg}{integral_msg}{jin_msg}{drop_msg}{fan_msg}{break_msg}{exp_msg}"
    return subbuff, msg

async def get_user_buff(user_id):
    BuffInfo = await XiuxianDataManage().get_user_buff_info(user_id)
    if BuffInfo is None:
        await XiuxianDataManage().initialize_user_buff_info(user_id)
        return await XiuxianDataManage().get_user_buff_info(user_id)
    else:
        return BuffInfo


def readf(FILEPATH):
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def get_sec_msg(secbuffdata):
    msg = None
    if secbuffdata is None:
        msg = "无"
        return msg
    hpmsg = f"，消耗当前血量{int(secbuffdata['hpcost'] * 100)}%" if secbuffdata['hpcost'] != 0 else ''
    mpmsg = f"，消耗真元{int(secbuffdata['mpcost'] * 100)}%" if secbuffdata['mpcost'] != 0 else ''

    if secbuffdata['skill_type'] == 1:
        shmsg = ''
        for value in secbuffdata['atkvalue']:
            shmsg += f"{value}倍、"
        if secbuffdata['turncost'] == 0:
            msg = f"攻击{len(secbuffdata['atkvalue'])}次，造成{shmsg[:-1]}伤害{hpmsg}{mpmsg}，释放概率：{secbuffdata['rate']}%"
        else:
            msg = f"连续攻击{len(secbuffdata['atkvalue'])}次，造成{shmsg[:-1]}伤害{hpmsg}{mpmsg}，休息{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%"
    elif secbuffdata['skill_type'] == 2:
        msg = f"持续伤害，造成{secbuffdata['atkvalue']}倍攻击力伤害{hpmsg}{mpmsg}，持续{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%"
    elif secbuffdata['skill_type'] == 3:
        if secbuffdata['bufftype'] == 1:
            msg = f"增强自身，提高{secbuffdata['buffvalue']}倍攻击力{hpmsg}{mpmsg}，持续{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%"
        elif secbuffdata['bufftype'] == 2:
            msg = f"增强自身，提高{secbuffdata['buffvalue'] * 100}%减伤率{hpmsg}{mpmsg}，持续{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%"
    elif secbuffdata['skill_type'] == 4:
        msg = f"封印对手{hpmsg}{mpmsg}，持续{secbuffdata['turncost']}回合，释放概率：{secbuffdata['rate']}%，命中成功率{secbuffdata['success']}%"

    return msg


def get_player_info(user_id, info_name):
    player_info = None
    if info_name == "mix_elixir_info":  # 灵田信息
        mix_elixir_infoconfigkey = ["收取时间", "收取等级", "灵田数量", '药材速度', "丹药控火", "丹药耐药性", "炼丹记录", "炼丹经验"]
        nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # str
        MIXELIXIRINFOCONFIG = {
            "收取时间": nowtime,
            "收取等级": 0,
            "灵田数量": 1,
            '药材速度': 0,
            "丹药控火": 0,
            "丹药耐药性": 0,
            "炼丹记录": {},
            "炼丹经验": 0
        }
        try:
            player_info = read_player_info(user_id, info_name)
            for key in mix_elixir_infoconfigkey:
                if key not in list(player_info.keys()):
                    player_info[key] = MIXELIXIRINFOCONFIG[key]
            save_player_info(user_id, player_info, info_name)
        except:
            player_info = MIXELIXIRINFOCONFIG
            save_player_info(user_id, player_info, info_name)
    return player_info


def read_player_info(user_id, info_name):
    user_id = str(user_id)
    FILEPATH = PLAYERSDATA / user_id / f"{info_name}.json"
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def save_player_info(user_id, data, info_name):
    user_id = str(user_id)

    if not os.path.exists(PLAYERSDATA / user_id):
        logger.opt(colors=True).info(f"<green>用户目录不存在，创建目录</green>")
        os.makedirs(PLAYERSDATA / user_id)

    FILEPATH = PLAYERSDATA / user_id / f"{info_name}.json"
    data = json.dumps(data, ensure_ascii=False, indent=4)
    save_mode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=save_mode, encoding="UTF-8") as f:
        f.write(data)
        f.close()


@DRIVER.on_shutdown
async def close_db():
    await XiuxianDataManage().close()

@DRIVER.on_startup
async def init_db():
    """初始化数据库连接和表结构"""
    data_manager = XiuxianDataManage()
    await data_manager._init_db_and_pool()
    logger.opt(colors=True).info(f"<green>修仙数据库初始化完成！</green>")