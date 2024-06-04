from ..xiuxian_utils.xiuxian2_handle import *
from .workmake import *
from ..xiuxian_utils.xiuxian2_handle import XiuxianDateManage
from ..xiuxian_utils.item_json import Items

sql_message = XiuxianDateManage()  # sql类


def readf(user_id):
    user_id = str(user_id)

    FILEPATH = PLAYERSDATA / user_id / "workinfo.json"
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def savef(user_id, data):
    user_id = str(user_id)

    if not os.path.exists(PLAYERSDATA / user_id):
        logger.opt(colors=True).info("<green>用户目录不存在，创建目录</green>")
        os.makedirs(PLAYERSDATA / user_id)

    FILEPATH = PLAYERSDATA / user_id / "workinfo.json"

    savemode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=savemode, encoding="UTF-8") as f:
        f.write(data)
        f.close()
    return True

class workhandle(XiuxianJsonDate):

    def do_work(self, key, work_list=None, name=None, level="江湖好手", exp=None, user_id=None):
        """悬赏令获取"""
        if key == 0:  # 如果没有获取过，则返回悬赏令
            data = workmake(level, exp, sql_message.get_user_info_with_id(user_id)['level'])
            get_work_list = []
            for k, v in data.items():
                if v[3] == 0:
                    item_msg = '!'
                else:
                    item_info = Items().get_data_by_item_id(v[3])
                    item_msg = f"，可能额外获得：{item_info['level']}:{item_info['name']}!"
                get_work_list.append([k, v[0], v[1], v[2], item_msg])
            savef(user_id, json.dumps(data, ensure_ascii=False))
            return get_work_list

        if key == 1:  # 返回对应的悬赏令信息
            try:
                data = readf(user_id)
                return data[name][2]
            except:
                pass

        elif key == 2:  # 如果是结算，则获取结果

            data = readf(user_id)

            bigsuc = False
            if data[work_list][0] >= 100:
                bigsuc = True

            success_msg = data[work_list][4]
            fail_msg = data[work_list][5]
            item_id = data[work_list][3]

            if random.randint(1, 100) <= data[work_list][0]:
                return success_msg, data[work_list][1], True, item_id, bigsuc
            else:
                return fail_msg, int(data[work_list][1] / 2), False, 0, bigsuc
