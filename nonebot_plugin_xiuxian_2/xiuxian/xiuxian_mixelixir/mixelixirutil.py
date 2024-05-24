from ..xiuxian_utils.item_json import Items
from random import shuffle

mix_config = Items().get_data_by_item_type(['合成丹药'])
mix_configs = {}
for k, v in mix_config.items():
    mix_configs[k] = v['elixir_config']

yonhudenji = 0
Llandudno_info = {
    "max_num": 10,
    "rank": 20
}


async def check_mix(elixir_config):
    is_mix = False
    l_id = []
    # mix_configs = await get_mix_config()
    for k, v in mix_configs.items():  # 这里是丹药配方
        type_list = []
        for ek, ev in elixir_config.items():  # 这是传入的值判断
            # 传入的丹药config
            type_list.append(ek)
        formula_list = []
        for vk, vv in v.items():  # 这里是每个配方的值
            formula_list.append(vk)
        if sorted(type_list) == sorted(formula_list):  # key满足了
            flag = False
            for typek in type_list:
                if elixir_config[typek] >= v[typek]:
                    flag = True
                    continue
                else:
                    flag = False
                    break
            if flag:
                l_id.append(k)

            continue
        else:
            continue
    id = 0
    if l_id:
        is_mix = True
        id_config = {}
        for id in l_id:
            for k, v in mix_configs[id].items():
                id_config[id] = v
                break
        id = sorted(id_config.items(), key=lambda x: x[1], reverse=True)[0][0]  # 选出最优解

    return is_mix, id


async def get_mix_elixir_msg(yaocai):
    mix_elixir_msg = {}
    num = 0
    
    # 药材类型字典
    yaocai_by_type = {}
    for k, v in yaocai.items():
        yaocai_by_type.setdefault(v['type'], []).append((k, v))
    
    for k, v in yaocai.items():
        for i in range(1, min(v['num'], 5) + 1):  # 尝试第一个药材为主药
            for kk, vv in yaocai.items():
                if kk == k:  # 相同的药材不能同时做药引
                    continue
                for o in range(1, min(vv['num'], 5) + 1):
                    if await tiaohe(v, i, vv, o):  # 调和失败
                        continue
                    zhuyao_type = str(v['主药']['type'])
                    zhuyao_power = v['主药']['power'] * i
                    elixir_config = {zhuyao_type: zhuyao_power}
                    
                    for kkk, vvv in yaocai.items():
                        for p in range(1, min(vvv['num'], 5) + 1):
                            fuyao_type = str(vvv['辅药']['type'])
                            fuyao_power = vvv['辅药']['power'] * p
                            elixir_config[fuyao_type] = fuyao_power
                            
                            is_mix, id_ = await check_mix(elixir_config)
                            if is_mix and i + o + p <= Llandudno_info["max_num"]:  # 有可以合成的
                                mix_elixir_msg[num] = {
                                    'id': id_,
                                    '配方': elixir_config.copy(),  # 复制字典
                                    '配方简写': f"主药{v['name']}{i}药引{vv['name']}{o}辅药{vvv['name']}{p}",
                                    '主药': v['name'],
                                    '主药_num': i,
                                    '主药_level': v['level'],
                                    '药引': vv['name'],
                                    '药引_num': o,
                                    '药引_level': vv['level'],
                                    '辅药': vvv['name'],
                                    '辅药_num': p,
                                    '辅药_level': vvv['level']
                                }
                                num += 1
                                
                            if fuyao_type in elixir_config:
                                del elixir_config[fuyao_type]  # 清除辅药
                                
                    if zhuyao_type in elixir_config:
                        del elixir_config[zhuyao_type]  # 清除主药
                    
    temp_dict = {}
    temp_id_list = set()
    finall_mix_elixir_msg = {}
    
    if not mix_elixir_msg:
        return finall_mix_elixir_msg
    
    for v in mix_elixir_msg.values():
        temp_id_list.add(v['id'])
    
    for id_ in temp_id_list:
        temp_dict[id_] = {}
        for k, v in mix_elixir_msg.items():
            if id_ == v['id']:
                temp_dict[id_][k] = v['主药_num'] + v['药引_num'] + v['辅药_num']
        id_ = min(temp_dict[id_], key=temp_dict[id_].get)
        finall_mix_elixir_msg[id_] = mix_elixir_msg[id_]
    
    return finall_mix_elixir_msg


async def absolute(x):
    if x >= 0:
        return x
    else:
        return -x


async def tiaohe(zhuyao_info, zhuyao_num, yaoyin_info, yaoyin_num):
    _zhuyao = zhuyao_info['主药']['h_a_c']['type'] * zhuyao_info['主药']['h_a_c']['power'] * zhuyao_num
    _yaoyin = yaoyin_info['药引']['h_a_c']['type'] * yaoyin_info['药引']['h_a_c']['power'] * yaoyin_num

    return await absolute(_zhuyao + _yaoyin) > yonhudenji


async def make_dict(old_dict):
    old_dict_key = list(old_dict.keys())
    shuffle(old_dict_key)
    if len(old_dict_key) >= 25:
        old_dict_key = old_dict_key[:25]
    new_dic = {}
    for key in old_dict_key:
        new_dic[key] = old_dict.get(key)
    return new_dic
