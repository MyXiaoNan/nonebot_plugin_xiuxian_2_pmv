try:
    import ujson as json
except ImportError:
    import json
import os
import random
import sqlite3
from datetime import datetime, timedelta
from collections import namedtuple
from pathlib import Path
from nonebot.log import logger
from .data_source import jsondata
from .xiuxian_config import XiuConfig
from .. import DRIVER
from .item_json import Items
from .xn_xiuxian_impart_config import config_impart

DATABASE = Path() / "data" / "xiuxian"
DATABASE_IMPARTBUFF = Path() / "data" / "xiuxian"

impart_buff = namedtuple("xiuxian_impart",
                         ["id", "user_id", "impart_hp_per", "impart_atk_per", "impart_mp_per", "impart_exp_up",
                          "boss_atk", "impart_know_per", "impart_burst_per", "impart_mix_per", "impart_reap_per",
                          "impart_two_exp", "stone_num", "exp_day", "wish"])

SKILLPATHH = DATABASE / "功法"
WEAPONPATH = DATABASE / "装备"
num = "578043031"
impart_num = "123451234"
items = Items()

xiuxian_data = namedtuple("xiuxian_data", ["no", "user_id", "linggen", "level"])
UserDate = namedtuple("UserDate",
                      ["id", "user_id", "stone", "root", "root_type", "level", "power", "create_time", "is_sign", "exp",
                       "user_name", "level_up_cd", "level_up_rate", "sect_id", "sect_position", "hp", "mp", "atk",
                       "atkpractice",
                       "sect_task", "sect_contribution", "sect_elixir_get", "blessed_spot_flag", "blessed_spot_name", "is_beg", "is_ban"])

UserCd = namedtuple("UserCd", ["user_id", "type", "create_time", "scheduled_time"])
SectInfo = namedtuple("SectInfo",
                      ["sect_id", "sect_name", "sect_owner", "sect_scale", "sect_used_stone", "sect_fairyland",
                       "sect_materials", "mainbuff", "secbuff", "elixir_room_level"])
BuffInfo = namedtuple("BuffInfo",
                      ["id", "user_id", "main_buff", "sec_buff", "faqi_buff", "fabao_weapon", "armor_buff", "atk_buff",
                       "blessed_spot", "sub_buff"])#辅修功法2
back = namedtuple("back", ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
                           "remake", "day_num", "all_num", "action_time", "state", "bind_num"])

class XiuxianDateManage:
    global num
    _instance = {}
    _has_init = {}

    def __new__(cls):
        if cls._instance.get(num) is None:
            cls._instance[num] = super(XiuxianDateManage, cls).__new__(cls)
        return cls._instance[num]

    def __init__(self):
        if not self._has_init.get(num):
            self._has_init[num] = True
            self.database_path = DATABASE
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "xiuxian.db"
                self.conn = sqlite3.connect(self.database_path)
                # self._create_file()
            else:
                self.database_path /= "xiuxian.db"
                self.conn = sqlite3.connect(self.database_path)
            logger.opt(colors=True).info(f"<green>修仙数据库已连接！</green>")
            self._check_data()

    def close(self):
        self.conn.close()
        logger.opt(colors=True).info(f"<green>修仙数据库关闭！</green>")

    def _create_file(self) -> None:
        """创建数据库文件"""
        c = self.conn.cursor()
        c.execute('''CREATE TABLE User_xiuxian
                           (NO            INTEGER PRIMARY KEY UNIQUE,
                           USERID         TEXT     ,
                           level          INTEGER  ,
                           root           INTEGER
                           );''')
        c.execute('''''')
        c.execute('''''')
        self.conn.commit()

    def _check_data(self):
        """检查数据完整性"""
        c = self.conn.cursor()

        for i in XiuConfig().sql_table:
            if i == "user_xiuxian":
                try:
                    c.execute(f"select count(1) from {i}")
                except sqlite3.OperationalError:
                    c.execute("""CREATE TABLE "user_xiuxian" (
      "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
      "user_id" INTEGER NOT NULL,
      "stone" integer DEFAULT 0,
      "root" TEXT,
      "root_type" TEXT,
      "level" TEXT,
      "power" integer DEFAULT 0,
      "create_time" integer,
      "is_sign" integer DEFAULT 0,
      "exp" integer DEFAULT 0,
      "user_name" TEXT DEFAULT NULL,
      "level_up_cd" integer DEFAULT NULL,
      "level_up_rate" integer DEFAULT 0,
      "is_beg" integer DEFAULT 0,
      "is_ban" integer DEFAULT 0
    );""")
            elif i == "user_cd":
                try:
                    c.execute(f"select count(1) from {i}")
                except sqlite3.OperationalError:
                    c.execute("""CREATE TABLE "user_cd" (
  "user_id" INTEGER NOT NULL,
  "type" integer DEFAULT 0,
  "create_time" integer DEFAULT NULL,
  "scheduled_time" integer,
  PRIMARY KEY ("user_id")
);""")
            elif i == "sects":
                try:
                    c.execute(f"select count(1) from {i}")
                except sqlite3.OperationalError:
                    c.execute("""CREATE TABLE "sects" (
  "sect_id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "sect_name" TEXT NOT NULL,
  "sect_owner" integer,
  "sect_scale" integer NOT NULL,
  "sect_used_stone" integer,
  "sect_fairyland" integer
);""")
            elif i == "back":
                try:
                    c.execute(f"select count(1) from {i}")
                except sqlite3.OperationalError:
                    pass
                    c.execute("""CREATE TABLE "back" (
  "user_id" INTEGER NOT NULL,
  "goods_id" INTEGER NOT NULL,
  "goods_name" TEXT,
  "goods_type" TEXT,
  "goods_num" INTEGER,
  "create_time" TEXT,
  "update_time" TEXT,
  "remake" TEXT,
  "day_num" INTEGER DEFAULT 0,
  "all_num" INTEGER DEFAULT 0,
  "action_time" TEXT,
  "state" INTEGER DEFAULT 0
);""")

            elif i == "BuffInfo":
                try:
                    c.execute(f"select count(1) from {i}")
                except sqlite3.OperationalError:
                    c.execute("""CREATE TABLE "BuffInfo" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "user_id" integer DEFAULT 0,
  "main_buff" integer DEFAULT 0,
  "sec_buff" integer DEFAULT 0,
  "faqi_buff" integer DEFAULT 0,
  "fabao_weapon" integer DEFAULT 0,
  "sub_buff" integer DEFAULT 0
);""")

        for i in XiuConfig().sql_user_xiuxian:
            try:
                c.execute(f"select {i} from user_xiuxian")
            except sqlite3.OperationalError:
                sql = f"ALTER TABLE user_xiuxian ADD COLUMN {i} INTEGER DEFAULT 0;"
                print(sql)
                c.execute(sql)

        for s in XiuConfig().sql_sects:
            try:
                c.execute(f"select {s} from sects")
            except sqlite3.OperationalError:
                sql = f"ALTER TABLE sects ADD COLUMN {s} INTEGER DEFAULT 0;"
                print(sql)
                c.execute(sql)

        for m in XiuConfig().sql_buff:
            try:
                c.execute(f"select {m} from BuffInfo")
            except sqlite3.OperationalError:
                sql = f"ALTER TABLE BuffInfo ADD COLUMN {m} INTEGER DEFAULT 0;"
                print(sql)
                c.execute(sql)

        for b in XiuConfig().sql_back:
            try:
                c.execute(f"select {b} from back")
            except sqlite3.OperationalError:
                sql = f"ALTER TABLE back ADD COLUMN {b} INTEGER DEFAULT 0;"
                print(sql)
                c.execute(sql)

        self.conn.commit()

    @classmethod
    def close_dbs(cls):
        XiuxianDateManage().close()

    def _create_user(self, user_id: str, root: str, type: str, power: str, create_time, user_name) -> None:
        """在数据库中创建用户并初始化"""
        c = self.conn.cursor()
        sql = f"INSERT INTO user_xiuxian (user_id,stone,root,root_type,level,power,create_time,user_name,exp,is_ban) VALUES (?,0,?,?,'江湖好手',?,?,?,100,0)"
        c.execute(sql, (user_id, root, type, power, create_time, user_name))
        self.conn.commit()

    def get_user_message(self, user_id):
        """根据USER_ID获取用户信息,不获取功法加成"""
        cur = self.conn.cursor()
        sql = f"select * from user_xiuxian where user_id=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return UserDate(*result)

    def get_user_real_info(self, user_id):
        """根据USER_ID获取用户信息,获取功法加成"""
        cur = self.conn.cursor()
        sql = f"select * from user_xiuxian where user_id=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return UserDate(*final_user_data(result))

    def get_sect_info(self, sect_id):
        """
        通过宗门编号获取宗门信息
        :param sect_id: 宗门编号
        :return:
        """
        cur = self.conn.cursor()
        sql = f"select * from sects where sect_id=?"
        cur.execute(sql, (sect_id,))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return SectInfo(*result)

    def get_user_message2(self, user_id):
        """根据user_name获取用户信息"""
        cur = self.conn.cursor()
        sql = f"select * from user_xiuxian where user_name=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return UserDate(*result)

    def create_user(self, user_id, *args):
        """校验用户是否存在"""
        cur = self.conn.cursor()
        sql = f"select * from user_xiuxian where user_id=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            self._create_user(user_id, args[0], args[1], args[2], args[3], args[4])
            self.conn.commit()
            welcome_msg = '欢迎进入修仙世界的，你的灵根为：{},类型是：{},你的战力为：{},当前境界：江湖好手'.format(args[0], args[1], args[2], args[3])
            return True, welcome_msg
        else:
            return False, '您已迈入修仙世界，输入【我的修仙信息】获取数据吧！'

    def get_sign(self, user_id):
        """获取用户签到信息"""
        cur = self.conn.cursor()
        sql = f"select is_sign from user_xiuxian where user_id=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return '修仙界没有你的足迹，输入 我要修仙 加入修仙世界吧！'
        elif result[0] == 0:
            ls = random.randint(XiuConfig().sign_in_lingshi_lower_limit, XiuConfig().sign_in_lingshi_upper_limit)
            sql2 = f"UPDATE user_xiuxian SET is_sign=1,stone=stone+? WHERE user_id=?"
            cur.execute(sql2, (ls,user_id))
            self.conn.commit()
            return '签到成功，获取{}块灵石!'.format(ls)
        elif result[0] == 1:
            return '贪心的人是不会有好运的！'
        
    def get_beg(self, user_id):
        """获取今日奇缘信息"""
        cur = self.conn.cursor()
        sql = f"select is_beg from user_xiuxian where user_id=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return '修仙界没有你的足迹，输入 我要修仙 加入修仙世界吧！'
        elif result[0] == 0:
            ls = random.randint(XiuConfig().beg_lingshi_lower_limit, XiuConfig().beg_lingshi_upper_limit)
            sql2 = f"UPDATE user_xiuxian SET is_beg=1,stone=stone+? WHERE user_id=?"
            cur.execute(sql2, (ls,user_id))
            self.conn.commit()
            return ls
        elif result[0] == 1:
            return None

    def ramaker(self, lg, type, user_id):
        """洗灵根"""
        cur = self.conn.cursor()

        # 查灵石
        sql_s = f"SELECT stone FROM user_xiuxian WHERE user_id=?"
        cur.execute(sql_s, (user_id,))
        result = cur.fetchone()
        if result[0] >= XiuConfig().remake:
            sql = f"UPDATE user_xiuxian SET root=?,root_type=?,stone=stone-? WHERE user_id=?"
            cur.execute(sql, (lg, type, XiuConfig().remake, user_id))
            self.conn.commit()

            self.update_power2(user_id)
            return "逆天之行，重获新生，新的灵根为：{}，类型为：{}".format(lg, type)
        else:
            return "你的灵石还不够呢，快去赚点灵石吧！"

    def get_root_rate(self, name):
        """获取灵根倍率"""
        data = jsondata.root_data()
        return data[name]['type_speeds']

    def get_level_power(self, name):
        """获取境界倍率|exp"""
        data = jsondata.level_data()
        return data[name]['power']
    
    def get_level_cost(self, name):
        """获取炼体境界倍率"""
        data = jsondata.exercises_level_data()
        return data[name]['cost_exp'], data[name]['cost_stone']

    def update_power2(self, user_id) -> None:
        """更新战力"""
        UserMessage = self.get_user_message(user_id)
        cur = self.conn.cursor()
        level = jsondata.level_data()
        root = jsondata.root_data()
        sql = f"UPDATE user_xiuxian SET power=round(exp*?*?,0) WHERE user_id=?"
        cur.execute(sql, (root[UserMessage.root_type]["type_speeds"], level[UserMessage.level]["spend"], user_id))
        self.conn.commit()

    def update_ls(self, user_id, price, key):
        """更新灵石  1为增加，2为减少"""
        cur = self.conn.cursor()

        if key == 1:
            sql = f"UPDATE user_xiuxian SET stone=stone+? WHERE user_id=?"
            cur.execute(sql, (price, user_id))
            self.conn.commit()
        elif key == 2:
            sql = f"UPDATE user_xiuxian SET stone=stone-? WHERE user_id=?"
            cur.execute(sql, (price, user_id))
            self.conn.commit()

    def update_root(self, user_id, key):
        """更新灵根  1为混沌,2为融合,3为超,4为龙,5为天,6为千世,7为万世"""
        cur = self.conn.cursor()
        if int(key) == 1:
            sql = f"UPDATE user_xiuxian SET root=?,root_type=? WHERE user_id=?"
            cur.execute(sql, ("全属性灵根", "混沌灵根", user_id))
            root_name = "混沌灵根"
            self.conn.commit()
            
        elif int(key) == 2:
            sql = f"UPDATE user_xiuxian SET root=?,root_type=? WHERE user_id=?"
            cur.execute(sql, ("融合万物灵根", "融合灵根", user_id))
            root_name = "融合灵根"
            self.conn.commit()
            
        elif int(key) == 3:
            sql = f"UPDATE user_xiuxian SET root=?,root_type=? WHERE user_id=?"
            cur.execute(sql, ("月灵根", "超灵根", user_id))
            root_name = "超灵根"
            self.conn.commit()
            
        elif int(key) == 4:
            sql = f"UPDATE user_xiuxian SET root=?,root_type=? WHERE user_id=?"
            cur.execute(sql, ("言灵灵根", "龙灵根", user_id))
            root_name = "龙灵根"
            self.conn.commit()
            
        elif int(key) == 5:
            sql = f"UPDATE user_xiuxian SET root=?,root_type=? WHERE user_id=?"
            cur.execute(sql, ("金灵根", "天灵根", user_id))
            root_name = "天灵根"
            self.conn.commit()
            
        elif int(key) == 6:
            sql = f"UPDATE user_xiuxian SET root=?,root_type=? WHERE user_id=?"
            cur.execute(sql, ("轮回千次不灭，只为臻至巅峰", "轮回道果", user_id))
            root_name = "轮回道果"
            self.conn.commit()
            
        elif int(key) == 7:
            sql = f"UPDATE user_xiuxian SET root=?,root_type=? WHERE user_id=?"
            cur.execute(sql, ("轮回万次不灭，只为超越巅峰", "真·轮回道果", user_id))
            root_name = "真·轮回道果"
            self.conn.commit()

        return root_name  # 返回灵根名称

    def update_ls_all(self, price):
        """所有用户增加灵石"""
        cur = self.conn.cursor()
        sql = f"UPDATE user_xiuxian SET stone=stone+?"
        cur.execute(sql, (price,))
        self.conn.commit()
    
    def get_exp_rank(self, user_id):
        """修为排行"""
        sql = f"select rank from(select user_id,exp,dense_rank() over (ORDER BY exp desc) as 'rank' FROM user_xiuxian) where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        return result

    def get_stone_rank(self, user_id):
        """灵石排行"""
        sql = f"select rank from(select user_id,stone,dense_rank() over (ORDER BY stone desc) as 'rank' FROM user_xiuxian) where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        return result
    
    def get_ls_rank(self):
        """灵石排行榜"""
        sql = f"SELECT user_id,stone FROM user_xiuxian  WHERE stone>0 ORDER BY stone DESC LIMIT 5"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        return result

    def sign_remake(self):
        """重置签到"""
        sql = f"UPDATE user_xiuxian SET is_sign=0"
        cur = self.conn.cursor()
        cur.execute(sql, )
        self.conn.commit()

    def beg_remake(self):
        """重置仙途奇缘"""
        sql = f"UPDATE user_xiuxian SET is_beg=0"
        cur = self.conn.cursor()
        cur.execute(sql, )
        self.conn.commit()

    def ban_user(self, user_id):
        """小黑屋，暂时没用"""
        sql = f"UPDATE user_xiuxian SET is_ban=1 where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        self.conn.commit()

    def update_user_name(self, user_id, user_name):
        """更新用户道号"""
        cur = self.conn.cursor()
        get_name = f"select user_name from user_xiuxian where user_name=?"
        cur.execute(get_name, (user_name,))
        result = cur.fetchone()
        if result:
            return "已存在该道号！"
        else:
            sql = f"UPDATE user_xiuxian SET user_name=? where user_id=?"

            cur.execute(sql, (user_name, user_id))
            self.conn.commit()
            return '道友的道号更新成功拉~'

    def updata_level_cd(self, user_id):
        """更新破镜CD"""
        sql = f"UPDATE user_xiuxian SET level_up_cd=? where user_id=?"
        cur = self.conn.cursor()
        now_time = datetime.now()
        cur.execute(sql, (now_time, user_id))
        self.conn.commit()

    def updata_level(self, user_id, level_name):
        """更新境界"""
        sql = f"UPDATE user_xiuxian SET level=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (level_name, user_id))
        self.conn.commit()

    def get_user_cd(self, user_id):
        """
        获取用户操作CD
        :param user_id: QQ
        """
        sql = f"SELECT * FROM user_cd  WHERE user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if result:
            return UserCd(*result)
        else:
            self.insert_user_cd(user_id, )
            return None

    def insert_user_cd(self, user_id) -> None:
        """
        添加用户至CD表
        :param user_id: qq
        :return:
        """
        sql = f"INSERT INTO user_cd (user_id) VALUES (?)"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        self.conn.commit()

    def create_sect(self, user_id, sect_name) -> None:
        """
        创建宗门
        :param user_id:qq
        :param sect_name:宗门名称
        :return:
        """
        sql = f"INSERT INTO sects(sect_name, sect_owner, sect_scale, sect_used_stone) VALUES (?,?,0,0)"
        cur = self.conn.cursor()
        cur.execute(sql, (sect_name, user_id))
        self.conn.commit()

    def update_sect_name(self, sect_id, sect_name) -> None:
        """
        修改宗门名称
        :param sect_id: 宗门id
        :param sect_name: 宗门名称
        :return: 返回是否更新成功的标志，True表示更新成功，False表示更新失败（已存在同名宗门）
        """
        cur = self.conn.cursor()
        get_sect_name = f"select sect_name from sects where sect_name=?"
        cur.execute(get_sect_name, (sect_name,))
        result = cur.fetchone()
        if result:
            return False
        else:
            sql = f"UPDATE sects SET sect_name=? WHERE sect_id=?"
            cur = self.conn.cursor()
            cur.execute(sql, (sect_name, sect_id))
            self.conn.commit()
            return True

    def get_sect_info_by_qq(self, user_id):
        """
        通过用户qq获取宗门信息
        :param user_id:
        :return:
        """
        cur = self.conn.cursor()
        sql = f"select * from sects where sect_owner=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return SectInfo(*result)

    def get_sect_info_by_id(self, sect_id):
        """
        通过宗门id获取宗门信息
        :param sect_id:
        :return:
        """
        cur = self.conn.cursor()
        sql = f"select * from sects where sect_id=?"
        cur.execute(sql, (sect_id,))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return SectInfo(*result)

    def update_usr_sect(self, user_id, usr_sect_id, usr_sect_position):
        """
        更新用户信息表的宗门信息字段
        :param user_id:
        :param usr_sect_id:
        :param usr_sect_position:
        :return:
        """
        sql = f"UPDATE user_xiuxian SET sect_id=?,sect_position=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (usr_sect_id, usr_sect_position, user_id))
        self.conn.commit()

    def get_all_sect_id(self):
        """获取全部宗门id"""
        sql = f"SELECT sect_id FROM sects"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        return result

    def in_closing(self, user_id, the_type):
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
            now_time = 0
        elif the_type == 2:
            now_time = datetime.now()
        # scheduled_time = datetime.now() + datetime.timedelta(minutes=int(the_time))
        sql = f"UPDATE user_cd SET type=?,create_time=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (the_type, now_time, user_id))
        self.conn.commit()

    def out_closing(self, user_id, the_type):
        """出关状态更新"""
        pass

    def update_exp(self, user_id, exp):
        """增加修为"""
        sql = f"UPDATE user_xiuxian SET exp=exp+? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (int(exp), user_id))
        self.conn.commit()

    def update_j_exp(self, user_id, exp):
        """减少修为"""
        sql = f"UPDATE user_xiuxian SET exp=exp-? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (int(exp), user_id))
        self.conn.commit()

    def del_exp_decimal(self, user_id, exp):
        """去浮点"""
        sql = f"UPDATE user_xiuxian SET exp=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (int(exp), user_id))
        self.conn.commit()

    def realm_top(self):
        """境界排行榜前百"""
        sql = f"""SELECT user_name,level,exp FROM user_xiuxian 
        WHERE user_name is NOT NULL
        ORDER BY CASE
        WHEN level = '零始境圆满' THEN '00'
        WHEN level = '零始境中期' THEN '01'
        WHEN level = '零始境初期' THEN '02'
        WHEN level = '祭道境圆满' THEN '03'
        WHEN level = '祭道境中期' THEN '04'
        WHEN level = '祭道境初期' THEN '05'
        WHEN level = '仙帝境圆满' THEN '06'
        WHEN level = '仙帝境中期' THEN '07'
        WHEN level = '仙帝境初期' THEN '08'
        WHEN level = '准帝境圆满' THEN '09'
        WHEN level = '准帝境中期' THEN '10'
        WHEN level = '准帝境初期' THEN '11'
        WHEN level = '仙王境圆满' THEN '12'
        WHEN level = '仙王境中期' THEN '13'
        WHEN level = '仙王境初期' THEN '14'
        WHEN level = '真仙境圆满' THEN '15'
        WHEN level = '真仙境中期' THEN '16'
        WHEN level = '真仙境初期' THEN '17'
        WHEN level = '至尊境圆满' THEN '18'
        WHEN level = '至尊境中期' THEN '19'
        WHEN level = '至尊境初期' THEN '20'
        WHEN level = '遁一境圆满' THEN '21'
        WHEN level = '遁一境中期' THEN '22'
        WHEN level = '遁一境初期' THEN '23'
        WHEN level = '斩我境圆满' THEN '24'
        WHEN level = '斩我境中期' THEN '25'
        WHEN level = '斩我境初期' THEN '26'
        WHEN level = '虚道境圆满' THEN '27'
        WHEN level = '虚道境中期' THEN '28'
        WHEN level = '虚道境初期' THEN '29'
        WHEN level = '天神境圆满' THEN '30'
        WHEN level = '天神境中期' THEN '31'
        WHEN level = '天神境初期' THEN '32'
        WHEN level = '圣祭境圆满' THEN '33'
        WHEN level = '圣祭境中期' THEN '34'
        WHEN level = '圣祭境初期' THEN '35'
        WHEN level = '真一境圆满' THEN '36'
        WHEN level = '真一境中期' THEN '37'
        WHEN level = '真一境初期' THEN '38'
        WHEN level = '神火境圆满' THEN '39'
        WHEN level = '神火境中期' THEN '40'
        WHEN level = '神火境初期' THEN '41'
        WHEN level = '尊者境圆满' THEN '42'
        WHEN level = '尊者境中期' THEN '43'
        WHEN level = '尊者境初期' THEN '44'
        WHEN level = '列阵境圆满' THEN '45'
        WHEN level = '列阵境中期' THEN '46'
        WHEN level = '列阵境初期' THEN '47'
        WHEN level = '铭纹境圆满' THEN '48'
        WHEN level = '铭纹境中期' THEN '49'
        WHEN level = '铭纹境初期' THEN '50'
        WHEN level = '化灵境圆满' THEN '51'
        WHEN level = '化灵境中期' THEN '52'
        WHEN level = '化灵境初期' THEN '53'
        WHEN level = '洞天境圆满' THEN '54'
        WHEN level = '洞天境中期' THEN '55'
        WHEN level = '洞天境初期' THEN '56'
        WHEN level = '搬血境圆满' THEN '57'
        WHEN level = '搬血境中期' THEN '58'
        WHEN level = '搬血境初期' THEN '59'
        WHEN level = '江湖好手' THEN '60'
        ELSE level END ASC,exp DESC LIMIT 50"""
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        return result

    def stone_top(self):
        """这也是灵石排行榜"""
        sql = f"SELECT user_name,stone FROM user_xiuxian WHERE user_name is NOT NULL ORDER BY stone DESC LIMIT 50"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        return result

    def power_top(self):
        """战力排行榜"""
        sql = f"SELECT user_name,power FROM user_xiuxian WHERE user_name is NOT NULL ORDER BY power DESC LIMIT 50"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        return result

    def scale_top(self):
        """
        宗门建设度排行榜
        :return:
        """
        sql = f"SELECT sect_id, sect_name, sect_scale FROM sects WHERE sect_owner is NOT NULL ORDER BY sect_scale DESC"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        return result

    def get_all_scale(self):
        """
        获取所有宗门信息
        :return:
        """
        sql = f"SELECT * FROM sects WHERE sect_owner is NOT NULL"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        results = []
        for r in result:
            results.append(SectInfo(*r))
        return results

    def get_all_sects_with_member_count(self):
        """
        获取所有宗门及其各个宗门成员数
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.sect_id, s.sect_name, s.sect_scale, (SELECT user_name FROM user_xiuxian WHERE user_id = s.sect_owner) as user_name, COUNT(ux.user_id) as member_count
            FROM sects s
            LEFT JOIN user_xiuxian ux ON s.sect_id = ux.sect_id
            GROUP BY s.sect_id
        """)
        results = cur.fetchall()
        return results

    def update_user_is_beg(self, user_id, is_beg):
        """
        更新用户的最后奇缘时间

        :param user_id: 用户ID
        :param is_beg: 'YYYY-MM-DD HH:MM:SS'
        """
        cur = self.conn.cursor()
        sql = "UPDATE user_xiuxian SET is_beg=? WHERE user_id=?"
        cur.execute(sql, (is_beg, user_id))
        self.conn.commit()


    def get_top1_user(self):
        """
        获取修为第一的用户
        """
        cur = self.conn.cursor()
        sql = f"select * from user_xiuxian ORDER BY exp DESC LIMIT 1"
        cur.execute(sql)
        result = cur.fetchone()
        if not result:
            return None
        else:
            return UserDate(*result)

    def donate_update(self, sect_id, stone_num):
        """宗门捐献更新建设度及可用灵石"""
        sql = f"UPDATE sects SET sect_used_stone=sect_used_stone+?,sect_scale=sect_scale+? where sect_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (stone_num, stone_num * 1, sect_id))
        self.conn.commit()

    def update_sect_used_stone(self, sect_id, sect_used_stone, key):
        """更新宗门灵石储备  1为增加,2为减少"""
        cur = self.conn.cursor()

        if key == 1:
            sql = f"UPDATE sects SET sect_used_stone=sect_used_stone+? WHERE sect_id=?"
            cur.execute(sql, (sect_used_stone, sect_id))
            self.conn.commit()
        elif key == 2:
            sql = f"UPDATE sects SET sect_used_stone=sect_used_stone-? WHERE sect_id=?"
            cur.execute(sql, (sect_used_stone, sect_id))
            self.conn.commit()

    def update_sect_materials(self, sect_id, sect_materials, key):
        """更新资材  1为增加,2为减少"""
        cur = self.conn.cursor()

        if key == 1:
            sql = f"UPDATE sects SET sect_materials=sect_materials+? WHERE sect_id=?"
            cur.execute(sql, (sect_materials, sect_id))
            self.conn.commit()
        elif key == 2:
            sql = f"UPDATE sects SET sect_materials=sect_materials-? WHERE sect_id=?"
            cur.execute(sql, (sect_materials, sect_id))
            self.conn.commit()

    def get_all_sects_id_scale(self):
        """
        获取所有宗门信息
        :return
        :result[0] = sect_id   
        :result[1] = 建设度 sect_scale,
        :result[2] = 丹房等级 elixir_room_level 
        """
        sql = f"SELECT sect_id, sect_scale, elixir_room_level FROM sects WHERE sect_owner is NOT NULL ORDER BY sect_scale DESC"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        return result

    def get_all_users_by_sect_id(self, sect_id):
        """
        获取宗门所有成员信息
        :return: 成员列表
        """
        sql = f"SELECT * FROM user_xiuxian WHERE sect_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (sect_id,))
        result = cur.fetchall()
        results = []
        for user in result:
            results.append(UserDate(*user))
        return results

    def do_work(self, user_id, the_type, sc_time=None):
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
            now_time = 0
        elif the_type == 2:
            now_time = datetime.now()
        elif the_type == 3:
            now_time = datetime.now()

        sql = f"UPDATE user_cd SET type=?,create_time=?,scheduled_time=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (the_type, now_time, sc_time, user_id))
        self.conn.commit()

    def update_levelrate(self, user_id, rate):
        """更新突破成功率"""
        sql = f"UPDATE user_xiuxian SET level_up_rate=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (rate, user_id))
        self.conn.commit()

    def update_user_attribute(self, user_id, hp, mp, atk):
        """更新用户HP,MP,ATK信息"""
        sql = f"UPDATE user_xiuxian SET hp=?,mp=?,atk=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (hp, mp, atk, user_id))
        self.conn.commit()

    def update_user_hp_mp(self, user_id, hp, mp):
        """更新用户HP,MP信息"""
        sql = f"UPDATE user_xiuxian SET hp=?,mp=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (hp, mp, user_id))
        self.conn.commit()

    def update_user_sect_contribution(self, user_id, sect_contribution):
        """更新用户宗门贡献度"""
        sql = f"UPDATE user_xiuxian SET sect_contribution=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (sect_contribution, user_id))
        self.conn.commit()

    def update_user_hp(self, user_id):
        """重置用户状态信息"""
        sql = f"UPDATE user_xiuxian SET hp=exp/2,mp=exp,atk=exp/10 where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        self.conn.commit()

    def restate(self, user_id=None):
        """restate重置所有用户状态或重置对应人状态"""
        if user_id is None:
            sql = f"UPDATE user_xiuxian SET hp=exp/2,mp=exp,atk=exp/10"
            cur = self.conn.cursor()
            cur.execute(sql, )
            self.conn.commit()
        else:
            sql = f"UPDATE user_xiuxian SET hp=exp/2,mp=exp,atk=exp/10 where user_id=?"
            cur = self.conn.cursor()
            cur.execute(sql, (user_id,))
            self.conn.commit()

    def get_back_msg(self, user_id):
        """获取用户背包信息"""
        sql = f"SELECT * FROM back where user_id=? and goods_num >= 1"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchall()
        # msg = f"你的背包\n"
        # for i in result:
        #     msg += f"{i},"
        results = []
        if not result:
            results = None
        for r in result:
            results.append(back(*r))
        return results

    def goods_num(self, user_id, goods_id):
        """
        判断用户物品数量
        :param user_id: 用户qq
        :param goods_id: 物品id
        :return: 物品数量
        """
        sql = f"SELECT num FROM back where user_id=? and goods_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id, goods_id))
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            return 0

    def get_all_user_exp(self, level):
        """查询所有对应大境界玩家的修为"""
        sql = f"SELECT exp FROM user_xiuxian  WHERE level like '{level}%'"
        cur = self.conn.cursor()
        cur.execute(sql, )
        result = cur.fetchall()
        return result

    def update_user_atkpractice(self, user_id, atkpractice):
        """更新用户攻击修炼等级"""
        sql = f"UPDATE user_xiuxian SET atkpractice={atkpractice} where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        self.conn.commit()

    def update_user_sect_task(self, user_id, sect_task):
        """更新用户宗门任务次数"""
        sql = f"UPDATE user_xiuxian SET sect_task=sect_task+? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (sect_task, user_id))
        self.conn.commit()

    def sect_task_reset(self):
        """重置宗门任务次数"""
        sql = f"UPDATE user_xiuxian SET sect_task=0"
        cur = self.conn.cursor()
        cur.execute(sql, )
        self.conn.commit()

    def update_sect_scale_and_used_stone(self, sect_id, sect_used_stone, sect_scale):
        """更新宗门灵石、建设度"""
        sql = f"UPDATE sects SET sect_used_stone=?,sect_scale=? where sect_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (sect_used_stone, sect_scale, sect_id))
        self.conn.commit()

    def update_sect_elixir_room_level(self, sect_id, level):
        """更新宗门丹房等级"""
        sql = f"UPDATE sects SET elixir_room_level=? where sect_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (level, sect_id))
        self.conn.commit()

    def update_user_sect_elixir_get_num(self, user_id):
        """更新用户每日领取丹药领取次数"""
        sql = f"UPDATE user_xiuxian SET sect_elixir_get=1 where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        self.conn.commit()

    def sect_elixir_get_num_reset(self):
        """重置宗门丹药领取次数"""
        sql = f"UPDATE user_xiuxian SET sect_elixir_get=0"
        cur = self.conn.cursor()
        cur.execute(sql, )
        self.conn.commit()

    def update_sect_mainbuff(self, sect_id, mainbuffid):
        """更新宗门当前的主修功法"""
        sql = f"UPDATE sects SET mainbuff=? where sect_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (mainbuffid, sect_id))
        self.conn.commit()

    def update_sect_secbuff(self, sect_id, secbuffid):
        """更新宗门当前的神通"""
        sql = f"UPDATE sects SET secbuff=? where sect_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (secbuffid, sect_id))
        self.conn.commit()

    def initialize_user_buff_info(self, user_id):
        """初始化用户buff信息"""
        sql = f"INSERT INTO BuffInfo (user_id,main_buff,sec_buff,faqi_buff,fabao_weapon) VALUES (?,0,0,0,0)"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        self.conn.commit()

    def get_user_buff_info(self, user_id):
        """获取用户buff信息"""
        sql = f"select * from BuffInfo where user_id =?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return BuffInfo(*result)

    def updata_user_main_buff(self, user_id, id):
        """更新用户主功法信息"""
        sql = f"UPDATE BuffInfo SET main_buff = ? where user_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (id, user_id,))
        self.conn.commit()
    
    def updata_user_sub_buff(self, user_id, id): #辅修功法3
        """更新用户辅修功法信息"""
        sql = f"UPDATE BuffInfo SET sub_buff = ? where user_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (id, user_id,))
        self.conn.commit()
    
    def updata_user_sec_buff(self, user_id, id):
        """更新用户副功法信息"""
        sql = f"UPDATE BuffInfo SET sec_buff = ? where user_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (id, user_id,))
        self.conn.commit()

    def updata_user_faqi_buff(self, user_id, id):
        """更新用户法器信息"""
        sql = f"UPDATE BuffInfo SET faqi_buff = ? where user_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (id, user_id,))
        self.conn.commit()

    def updata_user_fabao_weapon(self, user_id, id):
        """更新用户法宝信息"""
        sql = f"UPDATE BuffInfo SET fabao_weapon = ? where user_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (id, user_id,))
        self.conn.commit()

    def updata_user_armor_buff(self, user_id, id):
        """更新用户防具信息"""
        sql = f"UPDATE BuffInfo SET armor_buff = ? where user_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (id, user_id,))
        self.conn.commit()

    def updata_user_atk_buff(self, user_id, buff):
        """更新用户永久攻击buff信息"""
        sql = f"UPDATE BuffInfo SET atk_buff=atk_buff+? where user_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (buff, user_id,))
        self.conn.commit()

    def updata_user_blessed_spot(self, user_id, blessed_spot):
        """更新用户洞天福地等级"""
        sql = f"UPDATE BuffInfo SET blessed_spot=? where user_id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, (blessed_spot, user_id,))
        self.conn.commit()

    def update_user_blessed_spot_flag(self, user_id):
        """更新用户洞天福地是否开启"""
        sql = f"UPDATE user_xiuxian SET blessed_spot_flag=1 where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id,))
        self.conn.commit()

    def update_user_blessed_spot_name(self, user_id, blessed_spot_name):
        """更新用户洞天福地的名字"""
        sql = f"UPDATE user_xiuxian SET blessed_spot_name=? where user_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (blessed_spot_name, user_id,))
        self.conn.commit()

    def day_num_reset(self):
        """重置丹药每日使用次数"""
        sql = f"UPDATE back SET day_num=0 where goods_type='丹药'"
        cur = self.conn.cursor()
        cur.execute(sql, )
        self.conn.commit()

    def send_back(self, user_id, goods_id, goods_name, goods_type, goods_num, bind_flag=0):
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
        # 检查物品是否存在，存在则update
        cur = self.conn.cursor()
        back = self.get_item_by_good_id_and_user_id(user_id, goods_id)
        if back:
            # 判断是否存在，存在则update
            if bind_flag == 1:
                bind_num = back.bind_num + goods_num
            else:
                bind_num = back.bind_num
            goods_nums = back.goods_num + goods_num
            sql = f"UPDATE back set goods_num=?,update_time=?,bind_num={bind_num} WHERE user_id=? and goods_id=?"
            cur.execute(sql, (goods_nums, now_time, user_id, goods_id))
            self.conn.commit()
        else:
            # 判断是否存在，不存在则INSERT
            if bind_flag == 1:
                bind_num = goods_num
            else:
                bind_num = 0
            sql = """
                    INSERT INTO back (user_id, goods_id, goods_name, goods_type, goods_num, create_time, update_time, bind_num)
            VALUES (?,?,?,?,?,?,?,?)"""
            cur.execute(sql, (user_id, goods_id, goods_name, goods_type, goods_num, now_time, now_time, bind_num))
            self.conn.commit()

    def get_item_by_good_id_and_user_id(self, user_id, goods_id):
        """根据物品id、用户id获取物品信息"""
        sql = f"select * from back where user_id=? and goods_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (user_id, goods_id))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return back(*result)

    def update_back_equipment(self, sql_str):
        """更新背包,传入sql"""
        print(f"执行的sql:{sql_str}")
        cur = self.conn.cursor()
        cur.execute(sql_str)
        self.conn.commit()

    def update_back_j(self, user_id, goods_id, num=1, use_key=0):
        """
        使用物品
        :num 减少数量  默认1
        :use_key 是否使用，丹药使用才传 默认0
        """
        back = self.get_item_by_good_id_and_user_id(user_id, goods_id)
        if back.goods_type == "丹药" and use_key == 1:  # 丹药要判断耐药性、日使用上限
            if back.bind_num >= 1:
                bind_num = back.bind_num - num  # 优先使用绑定物品
            else:
                bind_num = back.bind_num
            day_num = back.day_num + num
            all_num = back.all_num + num
        else:
            bind_num = back.bind_num
            day_num = back.day_num
            all_num = back.all_num
        goods_num = back.goods_num - num
        now_time = datetime.now()
        sql_str = f"UPDATE back set update_time='{now_time}',action_time='{now_time}',goods_num={goods_num},day_num={day_num},all_num={all_num},bind_num={bind_num} WHERE user_id={user_id} and goods_id={goods_id}"
        cur = self.conn.cursor()
        cur.execute(sql_str)
        self.conn.commit()


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

    def set_closing_type(self, user_level):
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if list_all == now_index:
            need_exp = 0.001
        is_updata_level = self.level[now_index + 1]
        need_exp = XiuxianDateManage().get_level_power(is_updata_level)
        return need_exp

    def get_type(self, user_exp, rate, user_level):
        list_all = len(self.level) - 1
        now_index = self.level.index(user_level)
        if list_all == now_index:
            return "道友已是最高境界，无法突破！"

        is_updata_level = self.level[now_index + 1]
        need_exp = XiuxianDateManage().get_level_power(is_updata_level)

        # 判断修为是否足够突破
        if user_exp >= need_exp:
            pass
        else:
            return "道友的修为不足以突破！距离下次突破需要{}修为！突破境界为：{}".format(need_exp - user_exp, is_updata_level)

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
        power_rate = mind / (other + mind)
        if power_rate >= 0.8:
            return "道友偷窃小辈实属天道所不齿！"
        elif power_rate <= 0.05:
            return "道友请不要不自量力！"
        else:
            return int(power_rate * 100)

    def player_fight(self, player1: dict, player2: dict):
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
            XiuxianDateManage().update_user_hp_mp(player2['user_id'], player2['气血'], player2['真元'])

            if player2['气血'] <= 0:
                play_list.append("{}胜利".format(player1['道号']))
                suc = f"{player1['道号']}"
                XiuxianDateManage().update_user_hp_mp(player2['user_id'], 1, player2['真元'])
                break

            play_list.append(msg2.format(player2['道号'], play2_sh))
            player1['气血'] = player1['气血'] - play2_sh
            play_list.append(f"{player1['道号']}剩余血量{player1['气血']}\n")
            XiuxianDateManage().update_user_hp_mp(player1['user_id'], player1['气血'], player1['真元'])

            if player1['气血'] <= 0:
                play_list.append("{}胜利".format(player2['道号']))
                suc = f"{player2['道号']}"
                XiuxianDateManage().update_user_hp_mp(player1['user_id'], 1, player1['真元'])
                break
            if player1['气血'] <= 0 or player2['气血'] <= 0:
                play_list.append("逻辑错误！！！")
                break

        return play_list, suc

    def send_hp_mp(self, user_id, hp, mp):
        user_msg = XiuxianDateManage().get_user_message(user_id)
        max_hp = int(user_msg.exp / 2)
        max_mp = int(user_msg.exp)

        msg = []
        hp_mp = []

        if user_msg.hp < max_hp:
            if user_msg.hp + hp < max_hp:
                new_hp = user_msg.hp + hp
                msg.append(',回复气血：{}'.format(hp))
            else:
                new_hp = max_hp
                msg.append(',气血已回满！')
        else:
            new_hp = user_msg.hp
            msg.append('')

        if user_msg.mp < max_mp:
            if user_msg.mp + mp < max_mp:
                new_mp = user_msg.mp + mp
                msg.append(',回复真元：{}'.format(mp))
            else:
                new_mp = max_mp
                msg.append(',真元已回满！')
        else:
            new_mp = user_msg.mp
            msg.append('')

        hp_mp.append(new_hp)
        hp_mp.append(new_mp)
        hp_mp.append(user_msg.exp)

        return msg, hp_mp



sql_message = XiuxianDateManage()  # sql类

items = Items()



def final_user_data(user_data):
    """传入用户当前信息、buff信息,返回最终信息"""
    user_data = list(user_data)
    #
    impart_data = xiuxian_impart.get_user_message(user_data[1])
    if impart_data:
        pass
    else:
        xiuxian_impart._create_user(user_data[1])
    impart_data = xiuxian_impart.get_user_message(user_data[1])
    impart_hp_per = impart_data.impart_hp_per if impart_data is not None else 0
    impart_mp_per = impart_data.impart_mp_per if impart_data is not None else 0
    impart_atk_per = impart_data.impart_atk_per if impart_data is not None else 0
    #
    user_buff_data = UserBuffDate(user_data[1]).BuffInfo
    #
    if int(user_buff_data.armor_buff) == 0: #防具攻击
        armor_atk_buff = 0
    else:
        armor_info = items.get_data_by_item_id(user_buff_data.armor_buff) #防具攻击
        armor_atk_buff = armor_info['atk_buff'] 
    #
    if int(user_buff_data.faqi_buff) == 0:
        weapon_atk_buff = 0
    else:
        weapon_info = items.get_data_by_item_id(user_buff_data.faqi_buff)
        weapon_atk_buff = weapon_info['atk_buff']
    main_buff_data = UserBuffDate(user_data[1]).get_user_main_buff_data()
    main_hp_buff = main_buff_data['hpbuff'] if main_buff_data is not None else 0
    main_mp_buff = main_buff_data['mpbuff'] if main_buff_data is not None else 0
    main_atk_buff = main_buff_data['atkbuff'] if main_buff_data is not None else 0
    user_data[15] = int(user_data[15] * (1 + main_hp_buff + impart_hp_per))  # hp
    user_data[16] = int(user_data[16] * (1 + main_mp_buff + impart_mp_per))  # mp
    user_data[17] = int((user_data[17] * (user_data[18] * 0.04 + 1) * (1 + main_atk_buff) * (
            1 + weapon_atk_buff) * (1 + armor_atk_buff)) * (1 + impart_atk_per)) + int(user_buff_data.atk_buff)
    # 每级+4%攻击
    user_data = tuple(user_data)
    return user_data


@DRIVER.on_shutdown
async def close_db():
    XiuxianDateManage().close()



# 这里是虚神界部分
class XIUXIAN_IMPART_BUFF:
    global impart_num
    _instance = {}
    _has_init = {}

    def __new__(cls):
        if cls._instance.get(impart_num) is None:
            cls._instance[impart_num] = super(XIUXIAN_IMPART_BUFF, cls).__new__(cls)
        return cls._instance[impart_num]

    def __init__(self):
        if not self._has_init.get(impart_num):
            self._has_init[impart_num] = True
            self.database_path = DATABASE_IMPARTBUFF
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "xiuxian_impart.db"
                self.conn = sqlite3.connect(self.database_path)
                # self._create_file()
            else:
                self.database_path /= "xiuxian_impart.db"
                self.conn = sqlite3.connect(self.database_path)
            logger.opt(colors=True).info(f"<green>xiuxian_impart数据库已连接!</green>")
            self._check_data()

    def close(self):
        self.conn.close()
        logger.opt(colors=True).info(f"<green>xiuxian_impart数据库关闭!</green>")

    def _create_file(self) -> None:
        """创建数据库文件"""
        c = self.conn.cursor()
        c.execute('''CREATE TABLE xiuxian_impart
                           (NO            INTEGER PRIMARY KEY UNIQUE,
                           USERID         TEXT     ,
                           level          INTEGER  ,
                           root           INTEGER
                           );''')
        c.execute('''''')
        c.execute('''''')
        self.conn.commit()

    def _check_data(self):
        """检查数据完整性"""
        c = self.conn.cursor()

        for i in config_impart.sql_table:
            if i == "xiuxian_impart":
                try:
                    c.execute(f"select count(1) from {i}")
                except sqlite3.OperationalError:
                    c.execute("""CREATE TABLE "xiuxian_impart" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "user_id" integer DEFAULT 0,
    "impart_hp_per" integer DEFAULT 0,
    "impart_atk_per" integer DEFAULT 0,
    "impart_mp_per" integer DEFAULT 0,
    "impart_exp_up" integer DEFAULT 0,
    "boss_atk" integer DEFAULT 0,
    "impart_know_per" integer DEFAULT 0,
    "impart_burst_per" integer DEFAULT 0,
    "impart_mix_per" integer DEFAULT 0,
    "impart_reap_per" integer DEFAULT 0,
    "impart_two_exp" integer DEFAULT 0,
    "stone_num" integer DEFAULT 0,
    "exp_day" integer DEFAULT 0,
    "wish" integer DEFAULT 0
    );""")

        for s in config_impart.sql_table_impart_buff:
            try:
                c.execute(f"select {s} from xiuxian_impart")
            except sqlite3.OperationalError:
                sql = f"ALTER TABLE xiuxian_impart ADD COLUMN {s} integer DEFAULT 0;"
                print(sql)
                logger.opt(colors=True).info(f"<green>xiuxian_impart数据库核对成功!</green>")
                c.execute(sql)

        self.conn.commit()

    @classmethod
    def close_dbs(cls):
        XIUXIAN_IMPART_BUFF().close()

    def create_user(self, user_id):
        """校验用户是否存在"""
        cur = self.conn.cursor()
        sql = f"select * from xiuxian_impart where user_id=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return False
        else:
            return True

    def _create_user(self, user_id: str) -> None:
        """在数据库中创建用户并初始化"""
        if self.create_user(user_id):
            pass
        else:
            c = self.conn.cursor()
            sql = f"INSERT INTO xiuxian_impart (user_id, impart_hp_per, impart_atk_per, impart_mp_per, impart_exp_up ,boss_atk,impart_know_per,impart_burst_per,impart_mix_per,impart_reap_per,impart_two_exp,stone_num,exp_day,wish) VALUES(?, 0, 0, 0, 0 ,0, 0, 0, 0, 0 ,0 ,0 ,0, 0) "
            c.execute(sql, (user_id,))
            self.conn.commit()

    def get_user_message(self, user_id):
        """根据USER_ID获取用户impart_buff信息"""
        cur = self.conn.cursor()
        sql = f"select * from xiuxian_impart where user_id=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            return None
        else:
            return impart_buff(*result)

    def update_impart_hp_per(self, impart_num, user_id):
        """更新impart_hp_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_hp_per=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_hp_per(self, impart_num, user_id):
        """add impart_hp_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_hp_per=impart_hp_per+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_atk_per(self, impart_num, user_id):
        """更新impart_atk_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_atk_per=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_atk_per(self, impart_num, user_id):
        """add  impart_atk_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_atk_per=impart_atk_per+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_mp_per(self, impart_num, user_id):
        """impart_mp_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_mp_per=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_mp_per(self, impart_num, user_id):
        """add impart_mp_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_mp_per=impart_mp_per+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_exp_up(self, impart_num, user_id):
        """impart_exp_up"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_exp_up=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_exp_up(self, impart_num, user_id):
        """add impart_exp_up"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_exp_up=impart_exp_up+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_boss_atk(self, impart_num, user_id):
        """boss_atk"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET boss_atk=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_boss_atk(self, impart_num, user_id):
        """add boss_atk"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET boss_atk=boss_atk+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_know_per(self, impart_num, user_id):
        """impart_know_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_know_per=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_know_per(self, impart_num, user_id):
        """add impart_know_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_know_per=impart_know_per+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_burst_per(self, impart_num, user_id):
        """impart_burst_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_burst_per=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_burst_per(self, impart_num, user_id):
        """add impart_burst_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_burst_per=impart_burst_per+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_mix_per(self, impart_num, user_id):
        """impart_mix_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_mix_per=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_mix_per(self, impart_num, user_id):
        """add impart_mix_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_mix_per=impart_mix_per+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_reap_per(self, impart_num, user_id):
        """impart_reap_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_reap_per=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_reap_per(self, impart_num, user_id):
        """add impart_reap_per"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_reap_per=impart_reap_per+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_two_exp(self, impart_num, user_id):
        """impart_two_exp"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_two_exp=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_two_exp(self, impart_num, user_id):
        """add impart_two_exp"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET impart_two_exp=impart_two_exp+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_impart_wish(self, impart_num, user_id):
        """update impart_wish"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET wish=? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def add_impart_wish(self, impart_num, user_id):
        """add impart_wish"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET wish=wish+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def update_stone_num(self, impart_num, user_id, type_):
        """impart_stone_num"""
        if type_ == 1:
            cur = self.conn.cursor()
            sql = f"UPDATE xiuxian_impart SET stone_num=stone_num+? WHERE user_id=?"
            cur.execute(sql, (impart_num, user_id))
            self.conn.commit()
            return True
        if type_ == 2:
            cur = self.conn.cursor()
            sql = f"UPDATE xiuxian_impart SET stone_num=stone_num-? WHERE user_id=?"
            cur.execute(sql, (impart_num, user_id))
            self.conn.commit()
            return True

    def update_impart_stone_all(self, impart_stone):
        """所有用户增加结晶"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET stone_num=stone_num+?"
        cur.execute(sql, (impart_stone,))
        self.conn.commit()

    def add_impart_exp_day(self, impart_num, user_id):
        """add  impart_exp_day"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET exp_day=exp_day+? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True

    def use_impart_exp_day(self, impart_num, user_id):
        """use  impart_exp_day"""
        cur = self.conn.cursor()
        sql = f"UPDATE xiuxian_impart SET exp_day=exp_day-? WHERE user_id=?"
        cur.execute(sql, (impart_num, user_id))
        self.conn.commit()
        return True


def leave_harm_time(user_id):
    hp_speed = 25
    user_mes = sql_message.get_user_message(user_id)  # 获取用户信息
    level = user_mes.level
    level_rate = sql_message.get_root_rate(user_mes.root_type)  # 灵根倍率
    realm_rate = jsondata.level_data()[level]["spend"]  # 境界倍率
    user_buff_data = UserBuffDate(user_id)
    mainbuffdata = UserBuffDate(user_id).get_user_main_buff_data()
    mainbuffratebuff = mainbuffdata['ratebuff'] if mainbuffdata != None else 0  # 功法修炼倍率
    try:
        time = int(((user_mes.exp / 10) - user_mes.hp) / ((XiuConfig().closing_exp * level_rate * realm_rate * (
                    1 + mainbuffratebuff)) * hp_speed))
    except:
        time = "无穷大"
    return time


async def impart_check(user_id):
    if XIUXIAN_IMPART_BUFF().get_user_message(user_id) is None:
        XIUXIAN_IMPART_BUFF()._create_user(user_id)
        return XIUXIAN_IMPART_BUFF().get_user_message(user_id)
    else:
        return XIUXIAN_IMPART_BUFF().get_user_message(user_id)
    
xiuxian_impart = XIUXIAN_IMPART_BUFF()

@DRIVER.on_shutdown
async def close_db():
    XIUXIAN_IMPART_BUFF().close()



# 这里是buff部分
class BuffJsonDate:

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


class UserBuffDate:

    def __init__(self, user_id):
        """用户Buff数据"""
        self.user_id = user_id
        self.BuffInfo = get_user_buff(self.user_id)

    def get_user_main_buff_data(self):
        try:
            main_buff_data = items.get_data_by_item_id(self.BuffInfo.main_buff)
        except:
            main_buff_data = None
        return main_buff_data
    
    def get_user_sub_buff_data(self):# 辅修功法9
        try:
            sub_buff_data = items.get_data_by_item_id(self.BuffInfo.sub_buff)
        except:
            sub_buff_data = None
        return sub_buff_data

    def get_user_sec_buff_data(self):
        try:
            sec_buff_data = items.get_data_by_item_id(self.BuffInfo.sec_buff)
        except:
            sec_buff_data = None
        return sec_buff_data

    def get_user_weapon_data(self):
        try:
            weapon_data = items.get_data_by_item_id(self.BuffInfo.faqi_buff)
        except:
            weapon_data = None
        return weapon_data

    def get_user_armor_buff_data(self):
        try:
            armor_buff_data = items.get_data_by_item_id(self.BuffInfo.armor_buff)
        except:
            armor_buff_data = None
        return armor_buff_data


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
    def_buff_msg = f"提升{int(weapon_info['def_buff'] * 100)}%减伤率！" if weapon_info['def_buff'] != 0 else ''
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
    #msg +=f"介绍：{armor_info['']}\n"
    return msg


def get_main_info_msg(id):
    mainbuff = items.get_data_by_item_id(id)
    hpmsg = f"提升{round(mainbuff['hpbuff'] * 100, 0)}%气血" if mainbuff['hpbuff'] != 0 else ''
    mpmsg = f"，提升{round(mainbuff['mpbuff'] * 100, 0)}%真元" if mainbuff['mpbuff'] != 0 else ''
    atkmsg = f"，提升{round(mainbuff['atkbuff'] * 100, 0)}%攻击力" if mainbuff['atkbuff'] != 0 else ''
    ratemsg = f"，提升{round(mainbuff['ratebuff'] * 100, 0)}%修炼速度" if mainbuff['ratebuff'] != 0 else ''
    
    cri_tmsg = f"，提升{round(mainbuff['crit_buff'] * 100, 0)}%会心率" if mainbuff['crit_buff'] != 0 else ''
    def_msg = f"，提升{round(mainbuff['def_buff'] * 100, 0)}%减伤率" if mainbuff['def_buff'] != 0 else ''
    dan_msg = f"，增加炼丹产出{round(mainbuff['dan_buff'])}枚" if mainbuff['dan_buff'] != 0 else ''
    dan_exp_msg = f"，每枚丹药额外增加{round(mainbuff['dan_exp'])}炼丹经验" if mainbuff['dan_exp'] != 0 else ''
    reap_msg = f"，提升药材收取数量{round(mainbuff['reap_buff'])}个" if mainbuff['reap_buff'] != 0 else ''
    exp_msg = f"，突破失败{round(mainbuff['exp_buff'] * 100, 0)}%经验保护" if mainbuff['exp_buff'] != 0 else ''
    critatk_msg = f"，提升{round(mainbuff['critatk'] * 100, 0)}%会心伤害" if mainbuff['critatk'] != 0 else ''
    two_msg = f"，增加{round(mainbuff['two_buff'])}双修次数" if mainbuff['two_buff'] != 0 else ''
    number_msg = f"，提升{round(mainbuff['number'])}%突破概率" if mainbuff['number'] != 0 else ''
    
    clo_exp_msg = f"，提升{round(mainbuff['clo_exp'] * 100, 0)}%闭关经验" if mainbuff['clo_exp'] != 0 else ''
    clo_rs_msg = f"，提升{round(mainbuff['clo_rs'] * 100, 0)}%闭关生命回复" if mainbuff['clo_rs'] != 0 else ''
    random_buff_msg = f"，战斗时随机获得一个战斗属性" if mainbuff['random_buff'] != 0 else ''
    ew_msg =  f"，使用专属武器时伤害增加50%！" if mainbuff['ew'] != 0 else ''
    msg = f"{mainbuff['name']}: {hpmsg}{mpmsg}{atkmsg}{ratemsg}{cri_tmsg}{def_msg}{dan_msg}{dan_exp_msg}{reap_msg}{exp_msg}{critatk_msg}{two_msg}{number_msg}{clo_exp_msg}{clo_rs_msg}{random_buff_msg}{ew_msg}！"
    return mainbuff, msg

def get_sub_info_msg(id): #辅修功法8
    subbuff = items.get_data_by_item_id(id)
    print(subbuff)
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

    stone_msg  = f"提升{round(subbuff['stone'] * 100, 0)}%boss战灵石获取" if subbuff['stone'] != 0 else ''
    integral_msg = f"，提升{round(subbuff['integral'])}点boss战积分获取" if subbuff['integral'] != 0 else ''
    jin_msg = f"禁止对手吸取" if subbuff['jin'] != 0 else ''
    drop_msg = f"，提升boss掉落率" if subbuff['drop'] != 0 else ''
    fan_msg = f"使对手发出的debuff失效" if subbuff['fan'] != 0 else ''
    break_msg = f"获得战斗破甲" if subbuff['break'] != 0 else ''
    exp_msg = f"，增加战斗获得的修为" if subbuff['exp'] != 0 else ''
    

    msg = f"{subbuff['name']}：{submsg}{stone_msg}{integral_msg}{jin_msg}{drop_msg}{fan_msg}{break_msg}{exp_msg}"
    return subbuff, msg

def get_user_buff(user_id):
    BuffInfo = sql_message.get_user_buff_info(user_id)
    if BuffInfo is None:
        sql_message.initialize_user_buff_info(user_id)
        return sql_message.get_user_buff_info(user_id)
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


PLAYERSDATA = Path() / "data" / "xiuxian" / "players"


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
        print("目录不存在，创建目录")
        os.makedirs(PLAYERSDATA / user_id)

    FILEPATH = PLAYERSDATA / user_id / f"{info_name}.json"
    data = json.dumps(data, ensure_ascii=False, indent=4)
    save_mode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=save_mode, encoding="UTF-8") as f:
        f.write(data)
        f.close()