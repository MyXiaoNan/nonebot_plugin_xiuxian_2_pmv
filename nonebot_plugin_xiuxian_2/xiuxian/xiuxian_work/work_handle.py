import json
import random
from ..xiuxian_utils.xiuxian2_handle import XiuxianJsonData
from .workmake import workmake
from ..xiuxian_utils.xiuxian2_handle import XiuxianDataManager
from ..xiuxian_utils.item_json import Items
from .reward_data_source import savef, readf

class workhandle(XiuxianJsonData):

    async def do_work(self, key, work_list=None, name=None, level="江湖好手", exp=None, user_id=None):
        """悬赏令获取"""
        if key == 0:  # 如果没有获取过，则返回悬赏令
            data = workmake(level, exp, (await XiuxianDataManager().get_user_infos_by_ids(user_id))['level'])
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
            except ValueError:
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