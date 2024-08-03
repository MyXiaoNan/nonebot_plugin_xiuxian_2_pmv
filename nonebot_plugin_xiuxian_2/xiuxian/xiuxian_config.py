try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path
from nonebot.log import logger

DATABASE = Path() / "data" / "xiuxian"

def convert_rank(rank_name):
    """
    获取境界等级，替代原来的USERRANK
    convert_rank('江湖好手')[0] 返回江湖好手的境界等级
    convert_rank('江湖好手')[1] 返回境界列表
    """
    ranks = [
        '江湖好手', # 57
        '搬血境初期', '搬血境中期', '搬血境圆满',
        '洞天境初期', '洞天境中期', '洞天境圆满', # 51
        '化灵境初期', '化灵境中期', '化灵境圆满',
        '铭纹境初期', '铭纹境中期', '铭纹境圆满',
        '列阵境初期', '列阵境中期', '列阵境圆满',
        '尊者境初期', '尊者境中期', '尊者境圆满', # 39
        '神火境初期', '神火境中期', '神火境圆满',
        '真一境初期', '真一境中期', '真一境圆满',
        '圣祭境初期', '圣祭境中期', '圣祭境圆满',
        '天神境初期', '天神境中期', '天神境圆满', # 27
        '虚道境初期', '虚道境中期', '虚道境圆满',
        '斩我境初期', '斩我境中期', '斩我境圆满',
        '遁一境初期', '遁一境中期', '遁一境圆满',
        '至尊境初期', '至尊境中期', '至尊境圆满', # 15
        '真仙境初期', '真仙境中期', '真仙境圆满',
        '仙王境初期', '仙王境中期', '仙王境圆满',
        '准帝境初期', '准帝境中期', '准帝境圆满',
        '仙帝境初期', '仙帝境中期', '仙帝境圆满',
        '祭道境初期', '祭道境中期', '祭道境圆满' # 0
    ]
    
    if rank_name in ranks:
        rank_number = len(ranks) - ranks.index(rank_name) - 1
        return rank_number, ranks
    else:
        return None, ranks

    
class XiuConfig:
    def __init__(self):
        self.sql_table = ["user_xiuxian", "user_cd", "sects", "back", "BuffInfo"]  
        self.sql_user_xiuxian = ["id", "user_id", "user_name", "stone", "root",
                                 "root_type", "level", "power",
                                 "create_time", "is_sign", "is_beg", "is_ban",
                                 "exp", "work_num", "level_up_cd",
                                 "level_up_rate", "sect_id",
                                 "sect_position", "hp", "mp", "atk",
                                 "atkpractice", "sect_task", "sect_contribution",
                                 "sect_elixir_get", "blessed_spot_flag", "blessed_spot_name", "user_stamina"]
        self.sql_user_cd = ["user_id", "type", "create_time", "scheduled_time", "last_check_info_time"]
        self.sql_sects = ["sect_id", "sect_name", "sect_owner", "sect_scale", "sect_used_stone", "sect_fairyland",
                          "sect_materials", "mainbuff", "secbuff", "elixir_room_level"]
        self.sql_buff = ["id", "user_id", "main_buff", "sec_buff", "faqi_buff", "fabao_weapon", "armor_buff",
                         "atk_buff", "sub_buff", "blessed_spot"]
        self.sql_back = ["user_id", "goods_id", "goods_name", "goods_type", "goods_num", "create_time", "update_time",
                         "remake", "day_num", "all_num", "action_time", "state", "bind_num"]
        self.sql_user_auctions = [""]
        # 上面是数据库校验,别动
        self.level = convert_rank('江湖好手')[1] # 境界列表，别动
        self.img = True # 是否使用图片发送消息
        self.user_info_image = True # 是否使用图片发送个人信息
        self.level_up_cd = 0  # 突破CD(分钟)
        self.closing_exp = 60  # 闭关每分钟获取的修为
        self.put_bot = []  # 接收消息qq,主qq，框架将只处理此qq的消息
        self.main_bo = []  # 负责发送消息的qq
        self.shield_group = []  # 屏蔽的群聊
        self.layout_bot_dict = {}
        # QQ所负责的群聊 #{群 ：bot}   其中 bot类型 []或str }
        # "123456":"123456",
        self.sect_min_level = "铭纹境圆满" # 创建宗门最低境界
        self.sect_create_cost = 5000000 # 创建宗门消耗
        self.sect_rename_cost = 50000000 # 宗门改名消耗
        self.sect_rename_cd = 1 # 宗门改名cd/天
        self.auto_change_sect_owner_cd = 7 # 自动换长时间不玩宗主cd/天
        self.closing_exp_upper_limit = 1.5  # 闭关获取修为上限（例如：1.5 下个境界的修为数*1.5）
        self.level_punishment_floor = 10  # 突破失败扣除修为，惩罚下限（百分比）
        self.level_punishment_limit = 35  # 突破失败扣除修为，惩罚上限(百分比)
        self.level_up_probability = 0.2  # 突破失败增加当前境界突破概率的比例
        self.sign_in_lingshi_lower_limit = 10000  # 每日签到灵石下限
        self.sign_in_lingshi_upper_limit = 50000  # 每日签到灵石上限
        self.beg_max_level = "铭纹境圆满" # 仙途奇缘能领灵石最高境界
        self.beg_max_days = 3 # 仙途奇缘能领灵石最多天数
        self.beg_lingshi_lower_limit = 200000  # 仙途奇缘灵石下限
        self.beg_lingshi_upper_limit = 500000  # 仙途奇缘灵石上限
        self.tou = 100000  # 偷灵石惩罚
        self.dufang_cd = 10  # 金银阁cd/秒
        self.tou_lower_limit = 0.01  # 偷灵石下限(百分比)
        self.tou_upper_limit = 0.50  # 偷灵石上限(百分比)
        self.remake = 100000  # 重入仙途的消费
        self.max_stamina = 240 # 体力上限
        self.stamina_recovery_points = 1 # 体力恢复点数/分钟
        self.lunhui_min_level = "祭道境圆满" # 千世轮回最低境界
        self.twolun_min_level = "祭道境圆满" # 万世轮回最低境界
        self.del_boss_id = []  # 支持非管理员和超管天罚boss
        self.gen_boss_id = []  # 支持非管理员和超管生成boss
        self.merge_forward_send = False # 消息合并转发,True是合并转发，False是长图发送，建议长图发送
        self.img_compression_limit = 90 # 图片压缩率，0为不压缩，最高100
        self.img_type = "webp" # 图片类型，webp或者jpeg，如果机器人的图片消息不显示请使用jpeg，jpeg请调低压缩率
        self.img_send_type = "io" # 图片发送类型,默认io,官方bot建议base64
        self.third_party_bot = True # 是否是野生机器人，是的话填True，官方bot请填False
        self.version = "xiuxian_2.2" # 修仙插件版本，别动


class JsonConfig:
    def __init__(self):
        self.config_jsonpath = DATABASE / "config.json"
        self.create_default_config()
    
    def read_data(self):
        """读取配置数据"""
        with open(self.config_jsonpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "group" not in data:
                data["group"] = [] 
                with open(self.config_jsonpath, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
        return data
        
    def create_default_config(self):
        """创建默认配置文件"""
        if not self.config_jsonpath.exists():
            default_data = {"group": []}
            with open(self.config_jsonpath, 'w', encoding='utf-8') as f:
                json.dump(default_data, f)

    def write_data(self, key, group_id=None):
        """
        说明：设置修仙开启或关闭
        参数：
        key: 群聊 1 为开启， 2为关闭,默认关闭
        """
        json_data = self.read_data()
        group_list = json_data.get('group', [])
        if key == 1:
            if group_id not in group_list:
                try:
                    group_list.append(group_id)
                    json_data['group'] = group_list
                except Exception as e:
                    logger.opt(colors=True).info(f"<red>错误:{e}</red>")
                    return False
        elif key == 2:
            if group_id in group_list:
                try:
                    group_list.remove(group_id)
                    json_data['group'] = group_list
                except Exception as e:
                    logger.opt(colors=True).info(f"<red>错误:{e}</ewd>")
                    return False
        else:
            logger.opt(colors=True).info("<red>未知key</red>")
            return False

        # 去重
        json_data['group'] = list(set(json_data['group']))

        with open(self.config_jsonpath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

            
    def get_enabled_groups(self):
        """获取开启修仙功能的群聊列表，去除重复项"""
        data = self.read_data()
        return list(set(data.get("group", [])))
