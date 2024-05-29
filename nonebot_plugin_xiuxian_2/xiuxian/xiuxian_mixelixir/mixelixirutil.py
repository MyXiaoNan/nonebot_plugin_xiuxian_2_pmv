from ..xiuxian_utils.item_json import Items
from random import shuffle

mix_config = Items().get_data_by_item_type(['合成丹药'])
mix_configs = {k: v['elixir_config'] for k, v in mix_config.items()}
yonhudenji = 0
Llandudno_info = {"max_num": 10, "rank": 20}

async def check_mix(elixir_config):
    is_mix = False
    l_id = []

    for k, v in mix_configs.items():
        type_list = list(elixir_config.keys())
        formula_list = list(v.keys())
        
        if sorted(type_list) == sorted(formula_list):
            if all(elixir_config[typek] >= v[typek] for typek in type_list):
                l_id.append(k)

    if l_id:
        is_mix = True
        id = max(l_id, key=lambda id: sum(mix_configs[id].values()))

    return is_mix, id if is_mix else 0

async def get_mix_elixir_msg(yaocai):
    mix_elixir_msg = {}
    num = 0

    for k, v in yaocai.items():
        for i in range(1, min(v['num'], 5) + 1):
            for kk, vv in yaocai.items():
                if kk == k:
                    continue
                for o in range(1, min(vv['num'], 5) + 1):
                    if await tiaohe(v, i, vv, o):
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
                            if is_mix and i + o + p <= Llandudno_info["max_num"]:
                                mix_elixir_msg[num] = {
                                    'id': id_,
                                    '配方': elixir_config.copy(),
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

                            elixir_config.pop(fuyao_type, None)

                    elixir_config.pop(zhuyao_type, None)

    if not mix_elixir_msg:
        return {}

    temp_dict = {}
    temp_id_list = {v['id'] for v in mix_elixir_msg.values()}
    finall_mix_elixir_msg = {}
    
    for id_ in temp_id_list:
        temp_dict[id_] = {}
        for k, v in mix_elixir_msg.items():
            if id_ == v['id']:
                temp_dict[id_][k] = v['主药_num'] + v['药引_num'] + v['辅药_num']
        best_id = min(temp_dict[id_], key=temp_dict[id_].get)
        finall_mix_elixir_msg[best_id] = mix_elixir_msg[best_id]

    return finall_mix_elixir_msg

async def absolute(x):
    return x if x >= 0 else -x

async def tiaohe(zhuyao_info, zhuyao_num, yaoyin_info, yaoyin_num):
    _zhuyao = zhuyao_info['主药']['h_a_c']['type'] * zhuyao_info['主药']['h_a_c']['power'] * zhuyao_num
    _yaoyin = yaoyin_info['药引']['h_a_c']['type'] * yaoyin_info['药引']['h_a_c']['power'] * yaoyin_num
    return await absolute(_zhuyao + _yaoyin) > yonhudenji

async def make_dict(old_dict):
    old_dict_keys = list(old_dict.keys())
    shuffle(old_dict_keys)
    return {key: old_dict[key] for key in old_dict_keys[:25]}
