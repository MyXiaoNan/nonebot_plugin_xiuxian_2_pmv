import random
from .xiuxian2_handle import XiuxianDateManage ,OtherSet, UserBuffDate, XIUXIAN_IMPART_BUFF
from .xiuxian_config import USERRANK
xiuxian_impart = XIUXIAN_IMPART_BUFF()
boss_zs = 0
boss_hx = 0 
boss_bs = 0
boss_jg = 0
boss_jh = 0
boss_jb = 0
boss_xx = 0
boss_xl =0

random_break = 0
random_xx = 0
random_hx = 0
random_def = 0

def Player_fight(player1: dict, player2: dict, type_in, bot_id):
    """
    回合制战斗
    type_in : 1-切磋，不消耗气血、真元
              2-战斗，消耗气血、真元
    数据示例：
    {"user_id": None,"道号": None, "气血": None, "攻击": None, "真元": None, '会心':None, 'exp':None}
    """
    user1_buff_date = UserBuffDate(player1['user_id'])  # 1号的buff信息
    user1_main_buff_data = user1_buff_date.get_user_main_buff_data()
    user1_hp_buff = user1_main_buff_data['hpbuff'] if user1_main_buff_data is not None else 0
    user1_mp_buff = user1_main_buff_data['mpbuff'] if user1_main_buff_data is not None else 0
    try:
        user_1_impart_data = xiuxian_impart.get_user_message(player1['user_id'])
    except:
        user_1_impart_data = None
    user_1_impart_hp = user_1_impart_data.impart_hp_per if user_1_impart_data is not None else 0
    user_1_impart_mp = user_1_impart_data.impart_mp_per if user_1_impart_data is not None else 0
    user1_hp_buff = user1_hp_buff + user_1_impart_hp
    user1_mp_buff = user1_mp_buff + user_1_impart_mp

    user2_buff_date = UserBuffDate(player2['user_id'])  # 2号的buff信息
    user2_main_buff_data = user2_buff_date.get_user_main_buff_data()
    user2_hp_buff = user2_main_buff_data['hpbuff'] if user2_main_buff_data is not None else 0
    user2_mp_buff = user2_main_buff_data['mpbuff'] if user2_main_buff_data is not None else 0
    try:
        user_2_impart_data = xiuxian_impart.get_user_message(player2['user_id'])
    except:
        user_2_impart_data = None
    user_2_impart_hp = user_1_impart_data.impart_hp_per if user_2_impart_data is not None else 0
    user_2_impart_mp = user_1_impart_data.impart_mp_per if user_2_impart_data is not None else 0
    user1_hp_buff = user1_hp_buff + user_2_impart_hp
    user1_mp_buff = user1_mp_buff + user_2_impart_mp

    player1_skil_open = False
    player2_skil_open = False
    user1_skill_date = None
    if user1_buff_date.get_user_sec_buff_data() is not None:
        user1_skill_date = user1_buff_date.get_user_sec_buff_data()
        player1_skil_open = True
    user2_skill_date = None
    if user2_buff_date.get_user_sec_buff_data() is not None:
        user2_skill_date = user2_buff_date.get_user_sec_buff_data()
        player2_skil_open = True
        
    player1_sub_open = False #辅修功法14
    player2_sub_open = False
    user1_sub_buff_date = {}
    user2_sub_buff_date = {}
    if user1_buff_date.get_user_sub_buff_data() != None:
        user1_sub_buff_date = user1_buff_date.get_user_sub_buff_data()
        player1_sub_open = True
    if user2_buff_date.get_user_sub_buff_data() != None:
        user2_sub_buff_date = user2_buff_date.get_user_sub_buff_data()
        player2_sub_open = True    

    play_list = []
    suc = None
    isSql = False
    if type_in == 2:
        isSql = True
    user1_turn_skip = True
    user2_turn_skip = True
    player1_init_hp = player1['气血']
    player2_init_hp = player2['气血']

    player1_turn_cost = 0  # 先设定为初始值 0
    player2_turn_cost = 0  # 先设定为初始值 0
    player1_f_js = get_user_def_buff(player1['user_id'])
    player2_f_js = get_user_def_buff(player2['user_id'])
    player1_js = player1_f_js
    player2_js = player2_f_js
    user1_skill_sh = 0
    user2_skill_sh = 0
    user1_buff_turn = True
    user2_buff_turn = True
    
    user1_battle_buff_date = UserBattleBuffDate(player1['user_id'])  # 1号的战斗buff信息 辅修功法14
    user2_battle_buff_date = UserBattleBuffDate(player2['user_id'])  # 2号的战斗buff信息
    
    while True:
        msg1 = "{}发起攻击，造成了{}伤害\n"
        msg2 = "{}发起攻击，造成了{}伤害\n"
        
        user1_battle_buff_date, user2_battle_buff_date, msg = start_sub_buff_handle(player1_sub_open, user1_sub_buff_date, user1_battle_buff_date, player2_sub_open, user2_sub_buff_date , user2_battle_buff_date)
        play_list.append(get_msg_dict(player1, player1_init_hp, msg)) #辅修功法14
        
        player2_health_temp = player2['气血']
        if player1_skil_open:  # 是否开启技能
            if user1_turn_skip:  # 无需跳过回合
                play_list.append(get_msg_dict(player1, player1_init_hp, f"☆------{player1['道号']}的回合------☆"))
                user1_hp_cost, user1_mp_cost, user1_skill_type, skill_rate = get_skill_hp_mp_data(player1,
                                                                                                  user1_skill_date)
                if player1_turn_cost == 0:  # 没有持续性技能生效
                    player1_js = player1_f_js  # 没有持续性技能生效,减伤恢复
                    if isEnableUserSikll(player1, user1_hp_cost, user1_mp_cost, player1_turn_cost,
                                         skill_rate):  # 满足技能要求，#此处为技能的第一次释放
                        skill_msg, user1_skill_sh, player1_turn_cost = get_skill_sh_data(player1, user1_skill_date)
                        if user1_skill_type == 1:  # 直接伤害类技能
                            play_list.append(get_msg_dict(player1, player1_init_hp, skill_msg))
                            player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)
                            player2['气血'] = player2['气血'] - int(user1_skill_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(
                                get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))

                        elif user1_skill_type == 2:  # 持续性伤害技能
                            play_list.append(get_msg_dict(player1, player1_init_hp, skill_msg))
                            player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)
                            player2['气血'] = player2['气血'] - int(user1_skill_sh * (0.2 + player2_js))  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(
                                get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))

                        elif user1_skill_type == 3:  # buff类技能
                            user1_buff_type = user1_skill_date['bufftype']
                            if user1_buff_type == 1:  # 攻击类buff
                                isCrit, player1_sh = get_turnatk(player1, user1_skill_sh,
                                                                 user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if isCrit:
                                    msg1 = "{}发起会心一击，造成了{}伤害\n"
                                else:
                                    msg1 = "{}发起攻击，造成了{}伤害\n"
                                player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)
                                play_list.append(get_msg_dict(player1, player1_init_hp, skill_msg))
                                play_list.append(
                                    get_msg_dict(player1, player1_init_hp, msg1.format(player1['道号'], player1_sh)))
                                player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                                play_list.append(
                                    get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))

                            elif user1_buff_type == 2:  # 减伤类buff,需要在player2处判断
                                isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if isCrit:
                                    msg1 = "{}发起会心一击，造成了{}伤害\n"
                                else:
                                    msg1 = "{}发起攻击，造成了{}伤害\n"

                                player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)
                                play_list.append(get_msg_dict(player1, player1_init_hp, skill_msg))
                                play_list.append(
                                    get_msg_dict(player1, player1_init_hp, msg1.format(player1['道号'], player1_sh)))
                                player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                                play_list.append(
                                    get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))
                                player1_js = player1_f_js - user1_skill_sh if player1_f_js - user1_skill_sh > 0.1 else 0.1

                        elif user1_skill_type == 4:  # 封印类技能
                            play_list.append(get_msg_dict(player1, player1_init_hp, skill_msg))
                            player1 = calculate_skill_cost(player1, user1_hp_cost, user1_mp_cost)

                            if user1_skill_sh:  # 命中
                                user2_turn_skip = False
                                user2_buff_turn = False

                    else:  # 没放技能，打一拳
                        isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg1 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害\n"
                        play_list.append(get_msg_dict(player1, player1_init_hp, msg1.format(player1['道号'], player1_sh)))
                        player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                        play_list.append(get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))

                else:  # 持续性技能判断,不是第一次
                    if user1_skill_type == 2:  # 持续性伤害技能
                        player1_turn_cost = player1_turn_cost - 1
                        skill_msg = get_persistent_skill_msg(player1['道号'], user1_skill_date['name'], user1_skill_sh,
                                                             player1_turn_cost)
                        play_list.append(get_msg_dict(player1, player1_init_hp, skill_msg))
                        isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg1 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害\n"
                        play_list.append(get_msg_dict(player1, player1_init_hp, msg1.format(player1['道号'], player1_sh)))
                        # 玩家1的伤害 * 玩家2的减伤,持续性伤害不影响普攻
                        player2['气血'] = player2['气血'] - int((user1_skill_sh + player1_sh) * player2_js)
                        play_list.append(get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))

                    elif user1_skill_type == 3:  # buff类技能
                        user1_buff_type = user1_skill_date['bufftype']
                        if user1_buff_type == 1:  # 攻击类buff
                            isCrit, player1_sh = get_turnatk(player1, user1_skill_sh,user1_battle_buff_date)  # 判定是否暴击 辅修功法14

                            if isCrit:
                                msg1 = "{}发起会心一击，造成了{}伤害\n"
                            else:
                                msg1 = "{}发起攻击，造成了{}伤害\n"

                            player1_turn_cost = player1_turn_cost - 1
                            play_list.append(get_msg_dict(player1, player1_init_hp,
                                                          f"{user1_skill_date['name']}增伤剩余:{player1_turn_cost}回合"))
                            play_list.append(
                                get_msg_dict(player1, player1_init_hp, msg1.format(player1['道号'], player1_sh)))
                            player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(
                                get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))

                        elif user1_buff_type == 2:  # 减伤类buff,需要在player2处判断
                            isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                            if isCrit:
                                msg1 = "{}发起会心一击，造成了{}伤害\n"
                            else:
                                msg1 = "{}发起攻击，造成了{}伤害\n"

                            player1_turn_cost = player1_turn_cost - 1
                            play_list.append(get_msg_dict(player1, player1_init_hp,
                                                          f"{user1_skill_date['name']}减伤剩余{player1_turn_cost}回合"))
                            play_list.append(
                                get_msg_dict(player1, player1_init_hp, msg1.format(player1['道号'], player1_sh)))
                            player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(
                                get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))
                            player1_js = player1_f_js - user1_skill_sh if player2_f_js - user1_skill_sh > 0.1 else 0.1

                    elif user1_skill_type == 4:  # 封印类技能
                        player1_turn_cost = player1_turn_cost - 1
                        skill_msg = get_persistent_skill_msg(player1['道号'], user1_skill_date['name'], user1_skill_sh,
                                                             player1_turn_cost)
                        play_list.append(get_msg_dict(player1, player1_init_hp, skill_msg))
                        isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg1 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害\n"
                        play_list.append(get_msg_dict(player1, player1_init_hp, msg1.format(player1['道号'], player1_sh)))

                        player2['气血'] = player2['气血'] - int(player1_sh * player2_js)  # 玩家1的伤害 * 玩家2的减伤
                        play_list.append(get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))
                        if player1_turn_cost == 0:  # 封印时间到
                            user2_turn_skip = True
                            user2_buff_turn = True

            else:  # 休息回合-1
                play_list.append(get_msg_dict(player1, player1_init_hp, f"☆------{player1['道号']}动弹不得！------☆"))
                if player1_turn_cost > 0:
                    player1_turn_cost -= 1
                if player1_turn_cost == 0 and user1_buff_turn:
                    user1_turn_skip = True

        else:  # 没有技能的derB
            if user1_turn_skip:
                play_list.append(get_msg_dict(player1, player1_init_hp, f"☆------{player1['道号']}的回合------☆"))
                isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                if isCrit:
                    msg1 = "{}发起会心一击，造成了{}伤害\n"
                else:
                    msg1 = "{}发起攻击，造成了{}伤害\n"
                play_list.append(get_msg_dict(player1, player1_init_hp, msg1.format(player1['道号'], player1_sh)))
                player2['气血'] = player2['气血'] - player1_sh
                play_list.append(get_msg_dict(player1, player1_init_hp, f"{player2['道号']}剩余血量{player2['气血']}"))

            else:
                play_list.append(get_msg_dict(player1, player1_init_hp, f"☆------{player1['道号']}动弹不得！------☆"))

        ## 自己回合结束 处理 辅修功法14
        player1, boss, msg = after_atk_sub_buff_handle(player1_sub_open,player1, user1_main_buff_data, user1_sub_buff_date, player2_health_temp-player2['气血'], player2)
        play_list.append(get_msg_dict(player1, player1_init_hp, msg))

        if player2['气血'] <= 0:  # 玩家2气血小于0，结算
            play_list.append(
                {"type": "node", "data": {"name": "Bot", "uin": int(bot_id), "content": "{}胜利".format(player1['道号'])}})
            suc = f"{player1['道号']}"
            if isSql:
                #
                if player1['气血'] <= 0:
                    player1['气血'] = 1
                #
                XiuxianDateManage().update_user_hp_mp(
                    player1['user_id'],
                    int(player1['气血'] / (1 + user1_hp_buff)),
                    int(player1['真元'] / (1 + user1_mp_buff))
                )
                XiuxianDateManage().update_user_hp_mp(player2['user_id'], 1, int(player2['真元'] / (1 + user2_mp_buff)))
            break

        if player1_turn_cost < 0:  # 休息为负数，如果休息，则跳过回合，正常是0
            user1_turn_skip = False
            player1_turn_cost += 1
        
        player1_health_temp = player1['气血'] #辅修功法14
        if player2_skil_open:  # 有技能
            if user2_turn_skip:  # 玩家2无需跳过回合
                play_list.append(get_msg_dict(player2, player2_init_hp, f"☆------{player2['道号']}的回合------☆"))
                user2_hp_cost, user2_mp_cost, user2_skill_type, skill_rate = get_skill_hp_mp_data(player2,
                                                                                                  user2_skill_date)
                if player2_turn_cost == 0:  # 没有持续性技能生效
                    player2_js = player2_f_js
                    if isEnableUserSikll(player2, user2_hp_cost, user2_mp_cost, player2_turn_cost,
                                         skill_rate):  # 满足技能要求，#此处为技能的第一次释放
                        skill_msg, user2_skill_sh, player2_turn_cost = get_skill_sh_data(player2, user2_skill_date)
                        if user2_skill_type == 1:  # 直接伤害类技能
                            play_list.append(get_msg_dict(player2, player2_init_hp, skill_msg))
                            player1['气血'] = player1['气血'] - int(user2_skill_sh * player1_js)  # 玩家2的伤害 * 玩家1的减伤
                            play_list.append(
                                get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))
                            player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                        elif user2_skill_type == 2:  # 持续性伤害技能
                            play_list.append(get_msg_dict(player2, player2_init_hp, skill_msg))
                            player1['气血'] = player1['气血'] - int(user2_skill_sh *(0.2 + player1_js) )  # 玩家2的伤害 * 玩家1的减伤
                            play_list.append(
                                get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))
                            player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                        elif user2_skill_type == 3:  # buff类技能
                            user2_buff_type = user2_skill_date['bufftype']
                            if user2_buff_type == 1:  # 攻击类buff
                                isCrit, player2_sh = get_turnatk(player2, user2_skill_sh, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if isCrit:
                                    msg2 = "{}发起会心一击，造成了{}伤害\n"
                                else:
                                    msg2 = "{}发起攻击，造成了{}伤害\n"

                                play_list.append(get_msg_dict(player2, player2_init_hp, skill_msg))
                                play_list.append(
                                    get_msg_dict(player2, player2_init_hp, msg2.format(player2['道号'], player2_sh)))
                                player1['气血'] = player1['气血'] - int(player2_sh * player1_js)
                                play_list.append(
                                    get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))
                                player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                            elif user2_buff_type == 2:  # 减伤类buff,需要在player2处判断
                                isCrit, player2_sh = get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if isCrit:
                                    msg2 = "{}发起会心一击，造成了{}伤害\n"
                                else:
                                    msg2 = "{}发起攻击，造成了{}伤害\n"
                                play_list.append(get_msg_dict(player2, player2_init_hp, skill_msg))
                                play_list.append(
                                    get_msg_dict(player2, player2_init_hp, msg2.format(player2['道号'], player2_sh)))
                                player1['气血'] = player1['气血'] - int(player2_sh * player1_js)
                                play_list.append(
                                    get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))
                                player2_js = player2_f_js - user2_skill_sh if player2_f_js - user2_skill_sh > 0.1 else 0.1
                                player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                        elif user2_skill_type == 4:  # 封印类技能
                            play_list.append(get_msg_dict(player2, player2_init_hp, skill_msg))
                            player2 = calculate_skill_cost(player2, user2_hp_cost, user2_mp_cost)

                            if user2_skill_sh:  # 命中
                                user1_turn_skip = False
                                user1_buff_turn = False

                    else:  # 没放技能
                        isCrit, player2_sh = get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg2 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg2 = "{}发起攻击，造成了{}伤害\n"
                        play_list.append(get_msg_dict(player2, player2_init_hp, msg2.format(player2['道号'], player2_sh)))
                        player1['气血'] = player1['气血'] - int(player2_sh * player1_js)  # 玩家2的伤害 * 玩家1的减伤
                        play_list.append(get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))

                else:  # 持续性技能判断,不是第一次
                    if user2_skill_type == 2:  # 持续性伤害技能
                        player2_turn_cost = player2_turn_cost - 1
                        skill_msg = get_persistent_skill_msg(player2['道号'], user2_skill_date['name'], user2_skill_sh,
                                                             player2_turn_cost)
                        play_list.append(get_msg_dict(player2, player2_init_hp, skill_msg))

                        isCrit, player2_sh = get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg2 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg2 = "{}发起攻击，造成了{}伤害\n"

                        play_list.append(get_msg_dict(player2, player2_init_hp, msg2.format(player2['道号'], player2_sh)))
                        player1['气血'] = player1['气血'] - int((user2_skill_sh + player2_sh) * player1_js)
                        play_list.append(get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))

                    elif user2_skill_type == 3:  # buff类技能
                        user2_buff_type = user2_skill_date['bufftype']
                        if user2_buff_type == 1:  # 攻击类buff
                            isCrit, player2_sh = get_turnatk(player2, user2_skill_sh, user2_battle_buff_date)  # 判定是否暴击 辅修功法14

                            if isCrit:
                                msg2 = "{}发起会心一击，造成了{}伤害\n"
                            else:
                                msg2 = "{}发起攻击，造成了{}伤害\n"
                            player2_turn_cost = player2_turn_cost - 1
                            play_list.append(get_msg_dict(player2, player2_init_hp,
                                                          f"{user2_skill_date['name']}增伤剩余{player2_turn_cost}回合"))
                            play_list.append(
                                get_msg_dict(player2, player2_init_hp, msg2.format(player2['道号'], player2_sh)))
                            player1['气血'] = player1['气血'] - int(player2_sh * player1_js)  # 玩家2的伤害 * 玩家1的减伤
                            play_list.append(
                                get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))

                        elif user2_buff_type == 2:  # 减伤类buff,需要在player2处判断
                            isCrit, player2_sh = get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                            if isCrit:
                                msg2 = "{}发起会心一击，造成了{}伤害\n"
                            else:
                                msg2 = "{}发起攻击，造成了{}伤害\n"

                            player2_turn_cost = player2_turn_cost - 1
                            play_list.append(get_msg_dict(player2, player2_init_hp,
                                                          f"{user2_skill_date['name']}减伤剩余{player2_turn_cost}回合！"))
                            play_list.append(
                                get_msg_dict(player2, player2_init_hp, msg2.format(player2['道号'], player2_sh)))
                            player1['气血'] = player1['气血'] - int(player2_sh * player1_js)  # 玩家1的伤害 * 玩家2的减伤
                            play_list.append(
                                get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))

                            player2_js = player2_f_js - user2_skill_sh if player2_f_js - user2_skill_sh > 0.1 else 0.1

                    elif user2_skill_type == 4:  # 封印类技能
                        player2_turn_cost = player2_turn_cost - 1
                        skill_msg = get_persistent_skill_msg(player2['道号'], user2_skill_date['name'], user2_skill_sh,
                                                             player2_turn_cost)
                        play_list.append(get_msg_dict(player2, player2_init_hp, skill_msg))

                        isCrit, player2_sh = get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg2 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg2 = "{}发起攻击，造成了{}伤害\n"
                        play_list.append(get_msg_dict(player2, player2_init_hp, msg2.format(player2['道号'], player2_sh)))
                        player1['气血'] = player1['气血'] - int(player2_sh * player1_js)  # 玩家1的伤害 * 玩家2的减伤
                        play_list.append(get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))

                        if player2_turn_cost == 0:  # 封印时间到
                            user1_turn_skip = True
                            user1_buff_turn = True

            else:  # 休息回合-1
                play_list.append(get_msg_dict(player2, player2_init_hp, f"☆------{player2['道号']}动弹不得！------☆"))
                if player2_turn_cost > 0:
                    player2_turn_cost -= 1
                if player2_turn_cost == 0 and user2_buff_turn:
                    user2_turn_skip = True
        else:  # 没有技能的derB
            if user2_turn_skip:
                play_list.append(get_msg_dict(player2, player2_init_hp, f"☆------{player2['道号']}的回合------☆"))
                isCrit, player2_sh = get_turnatk(player2, 0, user2_battle_buff_date)  # 判定是否暴击 辅修功法14
                if isCrit:
                    msg2 = "{}发起会心一击，造成了{}伤害\n"
                else:
                    msg2 = "{}发起攻击，造成了{}伤害\n"
                play_list.append(get_msg_dict(player2, player2_init_hp, msg2.format(player2['道号'], player2_sh)))
                player1['气血'] = player1['气血'] - player2_sh
                play_list.append(get_msg_dict(player2, player2_init_hp, f"{player1['道号']}剩余血量{player1['气血']}"))

            else:
                play_list.append(get_msg_dict(player2, player2_init_hp, f"☆------{player2['道号']}动弹不得！------☆"))

        if player1['气血'] <= 0:  # 玩家1气血小于0，结算
            play_list.append(
                {"type": "node", "data": {"name": "Bot", "uin": int(bot_id), "content": "{}胜利".format(player2['道号'])}})
            suc = f"{player2['道号']}"
            if isSql:
                XiuxianDateManage().update_user_hp_mp(player1['user_id'], 1, int(player1['真元'] / (1 + user1_mp_buff)))
                #
                if player2['气血'] <= 0:
                    player2['气血'] = 1
                #
                XiuxianDateManage().update_user_hp_mp(
                    player2['user_id'],
                    int(player2['气血'] / (1 + user2_hp_buff)),
                    int(player2['真元'] / (1 + user2_mp_buff))
                )
            break
        
        ## 对方回合结束 处理 辅修功法14
        player2, player1, msg = after_atk_sub_buff_handle(player2_sub_open,player2, user2_main_buff_data, user2_sub_buff_date,
                                                       player1_health_temp - player1['气血'], player1)
        play_list.append(get_msg_dict(player1, player1_init_hp, msg))

        if player1['气血'] <= 0:  # 玩家2气血小于0，结算
            play_list.append({"type": "node",
                              "data": {"name": "Bot", "uin": int(bot_id), "content": "{}胜利".format(player2['道号'])}})
            suc = f"{player2['道号']}"
            if isSql:
                XiuxianDateManage().update_user_hp_mp(player1['user_id'], 1, int(player1['真元'] / (1 + user1_mp_buff)))
                XiuxianDateManage().update_user_hp_mp(player2['user_id'], int(player2['气血'] / (1 + user2_hp_buff)),
                                                      int(player2['真元'] / (1 + user2_mp_buff)))
            break

        

        if player2_turn_cost < 0:  # 休息为负数，如果休息，则跳过回合，正常是0
            user2_turn_skip = False
            player2_turn_cost += 1

        if user1_turn_skip == False and user2_turn_skip == False:
            play_list.append({"type": "node", "data": {"name": "Bot", "uin": int(bot_id), "content": "双方都动弹不得！"}})
            user1_turn_skip = True
            user2_turn_skip = True

        if player1['气血'] <= 0 or player2['气血'] <= 0:
            play_list.append({"type": "node", "data": {"name": "Bot", "uin": int(bot_id), "content": "逻辑错误！"}})
            break

    return play_list, suc

def get_st2_type():
    data_dict = ST2
    return get_dict_type_rate(data_dict)

def get_st1_type():
    """根据概率返回事件类型"""
    data_dict = ST1
    return get_dict_type_rate(data_dict)

def get_dict_type_rate(data_dict):
    """根据字典内概率,返回字典key"""
    temp_dict = {}
    for i, v in data_dict.items():
        try:
            temp_dict[i] = v["type_rate"]
        except:
            continue
    key = OtherSet().calculated(temp_dict)
    return key

ST1 ={
        "攻击": {
            "type_rate": 50,
        },
        "会心": {
            "type_rate": 50,
        },
        "暴伤": {
            "type_rate": 50,
        },
        "禁血": {
            "type_rate": 50,
        }
    }

ST2 ={
        "降攻": {
            "type_rate": 50,
        },
        "降会": {
            "type_rate": 50,
        },
        "降暴": {
            "type_rate": 50,
        },
        "禁蓝": {
            "type_rate": 50,
        }
    }


async def Boss_fight(player1: dict, boss: dict, type_in=2, bot_id=0):
    """
    回合制战斗
    type_in : 1-切磋，不消耗气血、真元
              2-战斗，消耗气血、真元
    数据示例：
    {"user_id": None,"道号": None, "气血": None, "攻击": None, "真元": None, '会心':None, 'exp':None}
    """
    user1_buff_date = UserBuffDate(player1['user_id'])  # 1号的buff信息
    user1_main_buff_data = user1_buff_date.get_user_main_buff_data()
    user1_sub_buff_data = user1_buff_date.get_user_sub_buff_data() #获取玩家1的辅修功法
    user1_hp_buff = user1_main_buff_data['hpbuff'] if user1_main_buff_data is not None else 0
    user1_mp_buff = user1_main_buff_data['mpbuff'] if user1_main_buff_data is not None else 0
    user1_random_buff = user1_main_buff_data['random_buff'] if user1_main_buff_data is not None else 0
    fan_buff = user1_sub_buff_data['fan'] if user1_sub_buff_data is not None else 0
    stone_buff = user1_sub_buff_data['stone'] if user1_sub_buff_data is not None else 0
    integral_buff = user1_sub_buff_data['integral'] if user1_sub_buff_data is not None else 0
    sub_break = user1_sub_buff_data['break'] if user1_sub_buff_data is not None else 0
    impart_data = xiuxian_impart.get_user_message(player1['user_id'])
    impart_hp_per = impart_data.impart_hp_per if impart_data is not None else 0
    impart_mp_per = impart_data.impart_mp_per if impart_data is not None else 0
    user1_hp_buff = user1_hp_buff + impart_hp_per
    user1_mp_buff = user1_mp_buff + impart_mp_per
    global random_break
    global random_xx
    global random_hx
    global random_def
    
    
    
    if user1_random_buff == 1:
        user1_main_buff = random.randint(0,100)
        if 0<= user1_main_buff <= 25:
            random_break = random.randint(15,40)/100
            random_xx = 0
            random_hx = 0
            random_def = 0
        elif 26<= user1_main_buff <= 50:
            random_break = 0
            random_xx = random.randint(2,10)/100
            random_hx = 0
            random_def = 0
        elif 51<= user1_main_buff <= 75:
            random_break = 0
            random_xx = 0
            random_hx = random.randint(5,40)/100
            random_def = 0
        elif 76<= user1_main_buff <= 100:
            random_break = 0
            random_xx = 0
            random_hx = 0
            random_def = random.randint(5,15)/100
    else:
        random_break = 0
        random_xx = 0
        random_hx = 0
        random_def = 0       
        
    user1_break = random_break + sub_break
    
    BOSSDEF = {
    "衣以候": "衣以侯布下了禁制镜花水月，",
    "金凰儿": "金凰儿使用了神通：金凰天火罩！",
    "九寒": "九寒使用了神通：寒冰八脉！",
    "莫女": "莫女使用了神通：圣灯启语诀！",
    "术方": "术方使用了神通：天罡咒！",
    "卫起": "卫起使用了神通：雷公铸骨！",
    "血枫": "血枫使用了神通：混世魔身！",
    "以向": "以向使用了神通：云床九练！",
    "砂鲛": "不说了！开鳖！",
    "神风王": "不说了！开鳖！",
    "鲲鹏": "鲲鹏使用了神通：逍遥游！",
    "天龙": "天龙使用了神通：真龙九变！",
    "历飞雨": "厉飞雨使用了神通：天煞震狱功！",
    "外道贩卖鬼": "不说了！开鳖！",
    "元磁道人": "元磁道人使用了法宝：元磁神山！",
    "散发着威压的尸体": "尸体周围爆发了出强烈的罡气！"
}
    BOSSATK = {
    "衣以候": "衣以侯布下了禁制镜花水月，",
    "金凰儿": "金凰儿使用了神通：金凰天火罩！",
    "九寒": "九寒使用了神通：寒冰八脉！",
    "莫女": "莫女使用了神通：圣灯启语诀！",
    "术方": "术方使用了神通：天罡咒！",
    "卫起": "卫起使用了神通：雷公铸骨！",
    "血枫": "血枫使用了神通：混世魔身！",
    "以向": "以向使用了神通：云床九练！",
    "砂鲛": "不说了！开鳖！",
    "神风王": "不说了！开鳖！",
    "鲲鹏": "鲲鹏使用了神通：逍遥游！",
    "天龙": "天龙使用了神通：真龙九变！",
    "历飞雨": "厉飞雨使用了神通：天煞震狱功！",
    "外道贩卖鬼": "不说了！开鳖！",
    "元磁道人": "元磁道人使用了法宝：元磁神山！",
    "散发着威压的尸体": "尸体周围爆发了出强烈的罡气！"
}

    # 有技能，则开启技能模式

    player1_skil_open = False
    user1_skill_date = None
    if user1_buff_date.get_user_sec_buff_data() is not None:
        user1_skill_date = user1_buff_date.get_user_sec_buff_data()
        player1_skil_open = True

    player1_sub_open = False #辅修功法14
    user1_sub_buff_date = {}
    if user1_buff_date.get_user_sub_buff_data() != None:
        user1_sub_buff_date = user1_buff_date.get_user_sub_buff_data()
        player1_sub_open = True


    play_list = []
    player_init_hp = player1['气血']
    suc = None
    isSql = False
    if type_in == 2:
        isSql = True
    user1_turn_skip = True
    boss_turn_skip = True
    player1_turn_cost = 0  # 先设定为初始值 0
    player1_f_js = get_user_def_buff(player1['user_id'])
    player1_js = player1_f_js # 减伤率
    
    
    global boss_zs
    global boss_hx
    global boss_bs 
    global boss_xx
    global boss_jg
    global boss_jh
    global boss_jb 
    global boss_xl
    #try:
    if boss["jj"] == '祭道之上':
            #boss["减伤"] = random.randint(40,90)/100 # boss减伤率
            boss["减伤"] = 0.05 # boss减伤率
            boss_st1 = random.randint(0,100) #boss神通1
            if 0 <= boss_st1 <= 25:
                boss_zs = 1   #boss攻击
                boss_hx = 0
                boss_bs = 0
                boss_xx = 0
            elif 26 <= boss_st1 <= 50:
                boss_zs = 0
                boss_hx = 0.7   #boss会心
                boss_bs = 0
                boss_xx = 0
            elif 51 <= boss_st1 <= 75:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 2   #boss暴伤
                boss_xx = 0
            elif 75 <= boss_st1 <= 100:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0
                boss_xx = 1  #boss禁血
                
            boss_st2 = random.randint(0,100) #boss神通2
            if 0 <= boss_st2 <= 25:
                boss_jg = 0.7   #boss降攻
                boss_jh = 0
                boss_jb = 0
                boss_xl = 0
            elif 26 <= boss_st2 <= 50:
                boss_jg = 0
                boss_jh = 0.7   #boss降会
                boss_jb = 0
                boss_xl = 0
            elif 51 <= boss_st2 <= 75:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 1.5   #boss降暴
                boss_xl = 0
            elif 76 <= boss_st2 <= 100:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0
                boss_xl = 1  #boss禁血
    
    if 19< USERRANK[boss["jj"] + '中期' ] <57: #遁一以下无免伤
            boss["减伤"] = 1 # boss减伤率
            boss_zs = 0
            boss_hx = 0
            boss_bs = 0
            boss_xx = 0
            boss_jg = 0
            boss_jh = 0
            boss_jb = 0
            boss_xl = 0
    if 16< USERRANK[boss["jj"] + '中期' ] <20: #遁一境 技能
            boss["减伤"] = random.randint(50,55)/100 # boss减伤率
            boss_st1 = random.randint(0,100) #boss神通1
            if 0 <= boss_st1 <= 25:
                boss_zs = 0.3   #boss攻击
                boss_hx = 0
                boss_bs = 0
                boss_xx = 0
            elif 26 <= boss_st1 <= 50:
                boss_zs = 0
                boss_hx = 0.1   #boss会心
                boss_bs = 0
                boss_xx = 0
            elif 51 <= boss_st1 <= 75:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0.5   #boss暴伤
                boss_xx = 0
            elif 75 <= boss_st1 <= 100:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0
                boss_xx = random.randint(5,100)/100  #boss禁血
                
            boss_st2 = random.randint(0,100) #boss神通2
            if 0 <= boss_st2 <= 25:
                boss_jg = 0.3   #boss降攻
                boss_jh = 0
                boss_jb = 0
                boss_xl = 0
            elif 26 <= boss_st2 <= 50:
                boss_jg = 0
                boss_jh = 0.3   #boss降会
                boss_jb = 0
                boss_xl = 0
            elif 51 <= boss_st2 <= 75:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0.5   #boss降暴
                boss_xl = 0
            elif 76 <= boss_st2 <= 100:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0
                boss_xl = random.randint(5,100)/100  #boss禁血
                
                        
    
    if 13< USERRANK[boss["jj"] + '中期' ] <17: #至尊境 技能
            boss["减伤"] = random.randint(40,45)/100 # boss减伤率
            boss_st1 = random.randint(0,100) #boss神通1
            if 0 <= boss_st1 <= 25:
                boss_zs = 0.4   #boss攻击
                boss_hx = 0
                boss_bs = 0
                boss_xx = 0
            elif 26 <= boss_st1 <= 50:
                boss_zs = 0
                boss_hx = 0.2   #boss会心
                boss_bs = 0
                boss_xx = 0
            elif 51 <= boss_st1 <= 75:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0.7   #boss暴伤
                boss_xx = 0
            elif 75 <= boss_st1 <= 100:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0
                boss_xx = random.randint(10,100)/100  #boss禁血
                
            boss_st2 = random.randint(0,100) #boss神通2
            if 0 <= boss_st2 <= 25:
                boss_jg = 0.4   #boss降攻
                boss_jh = 0
                boss_jb = 0
                boss_xl = 0
            elif 26 <= boss_st2 <= 50:
                boss_jg = 0
                boss_jh = 0.4   #boss降会
                boss_jb = 0
                boss_xl = 0
            elif 51 <= boss_st2 <= 75:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0.7   #boss降暴
                boss_xl = 0
            elif 76 <= boss_st2 <= 100:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0
                boss_xl = random.randint(10,100)/100  #boss禁血
            
    if 10< USERRANK[boss["jj"] + '中期' ] <14: #真仙境免伤
            boss["减伤"] = random.randint(30,35)/100 # boss减伤率
            boss_st1 = random.randint(0,100) #boss神通1
            if 0 <= boss_st1 <= 25:
                boss_zs = 0.6   #boss攻击
                boss_hx = 0
                boss_bs = 0
                boss_xx = 0
            elif 26 <= boss_st1 <= 50:
                boss_zs = 0
                boss_hx = 0.35   #boss会心
                boss_bs = 0
                boss_xx = 0
            elif 51 <= boss_st1 <= 75:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 1.1   #boss暴伤
                boss_xx = 0
            elif 75 <= boss_st1 <= 100:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0
                boss_xx = random.randint(30,100)/100  #boss禁血
                
            boss_st2 = random.randint(0,100) #boss神通2
            if 0 <= boss_st2 <= 25:
                boss_jg = 0.5   #boss降攻
                boss_jh = 0
                boss_jb = 0
                boss_xl = 0
            elif 26 <= boss_st2 <= 50:
                boss_jg = 0
                boss_jh = 0.5   #boss降会
                boss_jb = 0
                boss_xl = 0
            elif 51 <= boss_st2 <= 75:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0.9   #boss降暴
                boss_xl = 0
            elif 76 <= boss_st2 <= 100:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0
                boss_xl = random.randint(30,100)/100  #boss禁血
            
    if 7< USERRANK[(boss["jj"]+ '中期')] <11: #仙王境免伤
            boss["减伤"] = random.randint(20,25)/100  # boss减伤率
            boss_st1 = random.randint(0,100) #boss神通1
            if 0 <= boss_st1 <= 25:
                boss_zs = 0.7   #boss攻击
                boss_hx = 0
                boss_bs = 0
                boss_xx = 0
            elif 26 <= boss_st1 <= 50:
                boss_zs = 0
                boss_hx = 0.45   #boss会心
                boss_bs = 0
                boss_xx = 0
            elif 51 <= boss_st1 <= 75:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 1.3   #boss暴伤
                boss_xx = 0
            elif 75 <= boss_st1 <= 100:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0
                boss_xx = random.randint(40,100)/100  #boss禁血
                
            boss_st2 = random.randint(0,100) #boss神通2
            if 0 <= boss_st2 <= 25:
                boss_jg = 0.55   #boss降攻
                boss_jh = 0
                boss_jb = 0
                boss_xl = 0
            elif 26 <= boss_st2 <= 50:
                boss_jg = 0
                boss_jh = 0.6   #boss降会
                boss_jb = 0
                boss_xl = 0
            elif 51 <= boss_st2 <= 75:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 1   #boss降暴
                boss_xl = 0
            elif 76 <= boss_st2 <= 100:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0
                boss_xl = random.randint(40,100)/100  #boss禁血
            
    if 4< USERRANK[(boss["jj"]+ '中期')] <8: #准帝境免伤
            boss["减伤"] = random.randint(10,15)/100  # boss减伤率
            boss_st1 = random.randint(0,100) #boss神通1
            if 0 <= boss_st1 <= 25:
                boss_zs = 0.85   #boss攻击
                boss_hx = 0
                boss_bs = 0
                boss_xx = 0
            elif 26 <= boss_st1 <= 50:
                boss_zs = 0
                boss_hx = 0.5   #boss会心
                boss_bs = 0
                boss_xx = 0
            elif 51 <= boss_st1 <= 75:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 1.5   #boss暴伤
                boss_xx = 0
            elif 75 <= boss_st1 <= 100:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0
                boss_xx = random.randint(50,100)/100  #boss禁血
                
            boss_st2 = random.randint(0,100) #boss神通2
            if 0 <= boss_st2 <= 25:
                boss_jg = 0.6   #boss降攻
                boss_jh = 0
                boss_jb = 0
                boss_xl = 0
            elif 26 <= boss_st2 <= 50:
                boss_jg = 0
                boss_jh = 0.65   #boss降会
                boss_jb = 0
                boss_xl = 0
            elif 51 <= boss_st2 <= 75:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 1.1   #boss降暴
                boss_xl = 0
            elif 76 <= boss_st2 <= 100:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0
                boss_xl = random.randint(50,100)/100  #boss禁血
      
    if 1< USERRANK[(boss["jj"]+ '中期')] <5: #仙帝境免伤
            boss["减伤"] = 0.1  # boss减伤率
            boss_st1 = random.randint(0,100) #boss神通1
            if 0 <= boss_st1 <= 25:
                boss_zs = 0.9   #boss攻击
                boss_hx = 0
                boss_bs = 0
                boss_xx = 0
            elif 26 <= boss_st1 <= 50:
                boss_zs = 0
                boss_hx = 0.6   #boss会心
                boss_bs = 0
                boss_xx = 0
            elif 51 <= boss_st1 <= 75:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 1.7   #boss暴伤
                boss_xx = 0
            elif 75 <= boss_st1 <= 100:
                boss_zs = 0
                boss_hx = 0
                boss_bs = 0
                boss_xx = random.randint(60,100)/100  #boss禁血
                
            boss_st2 = random.randint(0,100) #boss神通2
            if 0 <= boss_st2 <= 25:
                boss_jg = 0.62   #boss降攻
                boss_jh = 0
                boss_jb = 0
                boss_xl = 0
            elif 26 <= boss_st2 <= 50:
                boss_jg = 0
                boss_jh = 0.67   #boss降会
                boss_jb = 0
                boss_xl = 0
            elif 51 <= boss_st2 <= 75:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 1.2   #boss降暴
                boss_xl = 0
            elif 76 <= boss_st2 <= 100:
                boss_jg = 0
                boss_jh = 0
                boss_jb = 0
                boss_xl = random.randint(60,100)/100  #boss禁血
            
            
    if fan_buff == 1:
        boss_jg = 0
        boss_jh = 0
        boss_jb = 0
        boss_xl = 0        
        fan_data = True
    else:
        fan_data = False
    
    
    
    
    
    #except:
    #    boss["减伤"] = 0.9  # boss减伤率
    user1_skill_sh = 0

    user1buffturn = True
    bossbuffturn = True

    get_stone = 0
    sh = 0
    qx = boss['气血']
    boss_now_stone = boss['stone']
    boss_js = boss['减伤']
    
    
    if boss_js <= 0.6 and boss['name'] in BOSSDEF:
        effect_name = BOSSDEF[boss['name']]
        boss_js_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{effect_name},获得了{int((1-boss_js)*100)}%减伤!"}}
        
        play_list.append(boss_js_data)
    
    if boss_zs > 0 :
        boss_zs_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{boss['name']}使用了真龙九变,提升了{int(boss_zs *100)}%攻击力!"}}
        
        play_list.append(boss_zs_data)
        
    if boss_hx > 0  :
        boss_hx_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{boss['name']}使用了无瑕七绝剑,提升了{int(boss_hx *100)}%会心率!"}}
        
        play_list.append(boss_hx_data)
    
    if boss_bs > 0 :
        boss_bs_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{boss['name']}使用了太乙剑诀,提升了{int(boss_bs *100)}%会心伤害!"}}
        
        play_list.append(boss_bs_data)
        
    if boss_xx > 0 :
        boss_xx_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{boss['name']}使用了七煞灭魂聚血杀阵,降低了{player1['道号']}{int((boss_xx) *100)}%气血吸取!"}}
        
        play_list.append(boss_xx_data)
        
    if boss_jg > 0 :
        boss_jg_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{boss['name']}使用了子午安息香,降低了{player1['道号']}{int((boss_jg) *100)}%伤害!"}}
        
        play_list.append(boss_jg_data)
    
    if boss_jh > 0 :
        boss_jh_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{boss['name']}使用了玄冥剑气,降低了{player1['道号']}{int((boss_jh) *100)}%会心率!"}}
        
        play_list.append(boss_jh_data)
        
    if boss_jb > 0 :
        boss_jb_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{boss['name']}使用了大德琉璃金刚身,降低了{player1['道号']}{int((boss_jb) *100)}%会心伤害!"}}
        
        play_list.append(boss_jb_data)
        
    if boss_xl > 0 :
        #effect_name = BOSSDEF[boss['name']]
        boss_xl_data = {"type": "node", "data": {"name": f"{boss['name']}",
                                     "uin": int(bot_id), "content": f"{boss['name']}使用了千煌锁灵阵,降低了{player1['道号']}{int((boss_xl) *100)}%真元吸取!"}}
        
        play_list.append(boss_xl_data)
        
    if random_break > 0:
        random_break_data = {"type": "node", "data": {"name": f"{player1['道号']}",
                                     "uin": int(bot_id), "content": f"{player1['道号']}发动了八九玄功,获得了{int((random_break)*100)}%穿甲！"}}
        play_list.append(random_break_data)
        
    if random_xx > 0:
        random_xx_data = {"type": "node", "data": {"name": f"{player1['道号']}",
                                     "uin": int(bot_id), "content": f"{player1['道号']}发动了八九玄功,提升了{int((random_xx)*100)}%!吸血效果！"}}
        play_list.append(random_xx_data)
        
    if random_hx > 0:
        random_hx_data = {"type": "node", "data": {"name": f"{player1['道号']}",
                                     "uin": int(bot_id), "content": f"{player1['道号']}发动了八九玄功,提升了{int((random_hx)*100)}%!会心！"}}
        play_list.append(random_hx_data)
        
    if random_def > 0:
        random_def_data = {"type": "node", "data": {"name": f"{player1['道号']}",
                                     "uin": int(bot_id), "content": f"{player1['道号']}发动了八九玄功,获得了{int((random_def)*100)}%!减伤！"}}
        play_list.append(random_def_data)
        
        
    #if boss_js <= 0.6 and boss['name'] == "衣以候":
       # boss_js_data = {"type": "node", "data": {"name": f"{boss['name']}",
   #                                  "uin": int(bot_id), "content": f"使用了金身神通：混世魔身！,获得了{int((1-boss_js)*100)}%减伤!"}}  
     #   play_list.append(boss_js_data)
       # print(boss_js_data["data"]["content"])
    
    #if boss_js <1:
        #boss_js_data = {"type": "node", "data": {"name": f"{boss['name']}",
        #                             "uin": int(bot_id), "content": f"凝聚真气,获得了{int((1-boss_js)*100)}%减伤!"}}
        #play_list.append(boss_js_data)
          
    boss['会心'] = 30
    
    if fan_data == True :
        fan_data = {"type": "node", "data": {"name": f"{player1['道号']}",
                                     "uin": int(bot_id), "content": f"{player1['道号']}发动了辅修功法反咒禁制，无效化了减益！"}}
        play_list.append(fan_data)
    
    user1_battle_buff_date = UserBattleBuffDate(player1['user_id'])  # 1号的战斗buff信息 辅修功法14


    while True:
        msg1 = "{}发起攻击，造成了{}伤害\n"
        msg2 = "{}发起攻击，造成了{}伤害\n"
        
        user1_battle_buff_date, user2_battle_buff_date, msg = start_sub_buff_handle(player1_sub_open,user1_sub_buff_date,user1_battle_buff_date,False,{},{})
        play_list.append(get_msg_dict(player1, player_init_hp, msg)) #辅修功法14

        player2_health_temp = boss['气血']
        if player1_skil_open:  # 是否开启技能
            if user1_turn_skip:  # 无需跳过回合
                turn_start_msg = f"☆------{player1['道号']}的回合------☆"
                play_list.append(get_msg_dict(player1, player_init_hp, turn_start_msg))
                user1hpconst, user1mpcost, user1skill_type, skillrate = get_skill_hp_mp_data(player1, user1_skill_date)
                if player1_turn_cost == 0:  # 没有持续性技能生效
                    player1_js = player1_f_js  # 没有持续性技能生效,减伤恢复
                    if isEnableUserSikll(player1, user1hpconst, user1mpcost, player1_turn_cost,
                                         skillrate):  # 满足技能要求，#此处为技能的第一次释放
                        skillmsg, user1_skill_sh, player1_turn_cost = get_skill_sh_data(player1, user1_skill_date)
                        if user1skill_type == 1:  # 直接伤害类技能
                            play_list.append(get_msg_dict(player1, player_init_hp, skillmsg))
                            player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)
                            boss['气血'] = boss['气血'] - int(user1_skill_sh * (boss_js + user1_break))  # 玩家1的伤害 * boss的减伤
                            boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                            play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                            sh += user1_skill_sh

                        elif user1skill_type == 2:  # 持续性伤害技能
                            play_list.append(get_msg_dict(player1, player_init_hp, skillmsg))
                            player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)
                            boss['气血'] = boss['气血'] - int(user1_skill_sh * (0.2 + boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                            boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                            play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                            sh += user1_skill_sh

                        elif user1skill_type == 3:  # buff类技能
                            user1buff_type = user1_skill_date['bufftype']
                            if user1buff_type == 1:  # 攻击类buff
                                isCrit, player1_sh = get_turnatk(player1 ,0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if isCrit:
                                    msg1 = "{}发起会心一击，造成了{}伤害\n"
                                else:
                                    msg1 = "{}发起攻击，造成了{}伤害\n"
                                player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)
                                play_list.append(get_msg_dict(player1, player_init_hp, skillmsg))
                                player1_atk_msg = msg1.format(player1['道号'], player1_sh)
                                play_list.append(get_msg_dict(player1, player_init_hp, player1_atk_msg))
                                boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                                boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                                play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                                sh += player1_sh

                            elif user1buff_type == 2:  # 减伤类buff,需要在player2处判断
                                isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                                if isCrit:
                                    msg1 = "{}发起会心一击，造成了{}伤害\n"
                                else:
                                    msg1 = "{}发起攻击，造成了{}伤害\n"

                                player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)
                                play_list.append(get_msg_dict(player1, player_init_hp, skillmsg))
                                player1_atk_msg = msg1.format(player1['道号'], player1_sh)
                                play_list.append(get_msg_dict(player1, player_init_hp, player1_atk_msg))
                                boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                                boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                                play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                                player1_js = player1_f_js - user1_skill_sh
                                sh += player1_sh

                        elif user1skill_type == 4:  # 封印类技能
                            play_list.append(get_msg_dict(player1, player_init_hp, skillmsg))
                            player1 = calculate_skill_cost(player1, user1hpconst, user1mpcost)

                            if user1_skill_sh:  # 命中
                                boss_turn_skip = False
                                bossbuffturn = False

                    else:  # 没放技能，打一拳
                        isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg1 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害\n"
                        player1_atk_msg = msg1.format(player1['道号'], player1_sh)
                        play_list.append(get_msg_dict(player1, player_init_hp, player1_atk_msg))
                        boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                        boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                        play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                        sh += player1_sh

                else:  # 持续性技能判断,不是第一次
                    if user1skill_type == 2:  # 持续性伤害技能
                        player1_turn_cost = player1_turn_cost - 1
                        skillmsg = get_persistent_skill_msg(player1['道号'], user1_skill_date['name'], user1_skill_sh,
                                                            player1_turn_cost)
                        play_list.append(get_msg_dict(player1, player_init_hp, skillmsg))
                        isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg1 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害\n"
                        player1_atk_msg = msg1.format(player1['道号'], player1_sh)
                        play_list.append(get_msg_dict(player1, player_init_hp, player1_atk_msg))
                        boss['气血'] = boss['气血'] - int((user1_skill_sh + player1_sh) * (boss_js + user1_break))
                        boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                        play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                        sh += player1_sh + user1_skill_sh

                    elif user1skill_type == 3:  # buff类技能
                        user1buff_type = user1_skill_date['bufftype']
                        if user1buff_type == 1:  # 攻击类buff
                            isCrit, player1_sh = get_turnatk(player1, user1_skill_sh,user1_battle_buff_date)  # 判定是否暴击 辅修功法14

                            if isCrit:
                                msg1 = "{}发起会心一击，造成了{}伤害\n"
                            else:
                                msg1 = "{}发起攻击，造成了{}伤害\n"
                            player1_turn_cost = player1_turn_cost - 1
                            play_list.append(get_msg_dict(player1, player_init_hp,
                                                          f"{user1_skill_date['name']}增伤剩余:{player1_turn_cost}回合"))
                            player1_atk_msg = msg1.format(player1['道号'], player1_sh)
                            play_list.append(get_msg_dict(player1, player_init_hp, player1_atk_msg))
                            boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                            boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                            play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                            sh += player1_sh

                        elif user1buff_type == 2:  # 减伤类buff,需要在player2处判断
                            isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                            if isCrit:
                                msg1 = "{}发起会心一击，造成了{}伤害\n"
                            else:
                                msg1 = "{}发起攻击，造成了{}伤害\n"

                            player1_turn_cost = player1_turn_cost - 1
                            play_list.append(get_msg_dict(player1, player_init_hp, f"减伤剩余{player1_turn_cost}回合！"))
                            player1_atk_msg = msg1.format(player1['道号'], player1_sh)
                            play_list.append(get_msg_dict(player1, player_init_hp, player1_atk_msg))
                            boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                            boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                            play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                            player1_js = player1_f_js - user1_skill_sh
                            sh += player1_sh

                    elif user1skill_type == 4:  # 封印类技能
                        player1_turn_cost = player1_turn_cost - 1
                        skillmsg = get_persistent_skill_msg(player1['道号'], user1_skill_date['name'], user1_skill_sh,
                                                            player1_turn_cost)
                        play_list.append(get_msg_dict(player1, player_init_hp, skillmsg))
                        isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
                        if isCrit:
                            msg1 = "{}发起会心一击，造成了{}伤害\n"
                        else:
                            msg1 = "{}发起攻击，造成了{}伤害\n"
                        player1_atk_msg = msg1.format(player1['道号'], player1_sh)
                        play_list.append(get_msg_dict(player1, player_init_hp, player1_atk_msg))
                        boss['气血'] = boss['气血'] - int(player1_sh * (boss_js + user1_break))  # 玩家1的伤害 * 玩家2的减伤
                        boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
                        play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
                        sh += player1_sh
                        if player1_turn_cost == 0:  # 封印时间到
                            boss_turn_skip = True
                            bossbuffturn = True

            else:  # 休息回合-1
                play_list.append(get_msg_dict(player1, player_init_hp, f"☆------{player1['道号']}动弹不得！------☆"))
                if player1_turn_cost > 0:
                    player1_turn_cost -= 1
                if player1_turn_cost == 0:
                    user1_turn_skip = True

        else:  # 没有技能的derB
            play_list.append(get_msg_dict(player1, player_init_hp, f"☆------{player1['道号']}的回合------☆"))
            isCrit, player1_sh = get_turnatk(player1, 0, user1_battle_buff_date)  # 判定是否暴击 辅修功法14
            if isCrit:
                msg1 = "{}发起会心一击，造成了{}伤害\n"
            else:
                msg1 = "{}发起攻击，造成了{}伤害\n"
            player1_atk_msg = msg1.format(player1['道号'], player1_sh)
            play_list.append(get_msg_dict(player1, player_init_hp, player1_atk_msg))
            boss['气血'] = boss['气血'] - player1_sh
            boss_hp_msg = f"{boss['name']}剩余血量{boss['气血']}"
            play_list.append(get_msg_dict(player1, player_init_hp, boss_hp_msg))
            sh += player1_sh
            
         ## 自己回合结束 处理 辅修功法14
        player1,boss,msg = after_atk_sub_buff_handle(player1_sub_open,player1,user1_main_buff_data,user1_sub_buff_date,player2_health_temp - boss['气血'],boss)
        play_list.append(get_msg_dict(player1, player_init_hp, msg))
        sh += player2_health_temp - boss['气血']

        if boss['气血'] <= 0:  # boss气血小于0，结算
            play_list.append(
                {"type": "node", "data": {"name": "Bot", "uin": int(bot_id), "content": "{}胜利".format(player1['道号'])}})
            suc = "群友赢了"
            get_stone = boss_now_stone * (1 + stone_buff)
            if isSql:
                #
                if player1['气血'] <= 0:
                    player1['气血'] = 1
                #
                XiuxianDateManage().update_user_hp_mp(
                    player1['user_id'],
                    int(player1['气血'] / (1 + user1_hp_buff)),
                    int(player1['真元'] / (1 + user1_mp_buff))
                )

            break

        if player1_turn_cost < 0:  # 休息为负数，如果休息，则跳过回合，正常是0
            user1_turn_skip = False
            player1_turn_cost += 1

            # 没有技能的derB
        if boss_turn_skip:
            boss_sub = random.randint(0,100)
            if boss_sub <= 8:
                play_list.append(get_boss_dict(boss, qx, f"☆------{boss['name']}的回合------☆", bot_id))
                isCrit, boss_sh = get_turnatk_boss(boss,0,UserBattleBuffDate("9999999"))  # 判定是否暴击 辅修功法14
                if isCrit:
                    msg2 = "{}：紫玄掌！！紫星河！！！并且发生了会心一击，造成了{}伤害\n"
                else:
                    msg2 = "{}：紫玄掌！！紫星河！！！造成了{}伤害\n"
                play_list.append(get_boss_dict(boss, qx, msg2.format(boss['name'], boss_sh * (1 + boss_zs) * 5 + (player1['气血'] * 0.3)), bot_id))
                player1['气血'] = player1['气血'] - (((boss_sh * (1 + boss_zs) * (player1_js - random_def) * 5) + (player1['气血'] * 0.3) ))
                play_list.append(get_boss_dict(boss, qx, f"{player1['道号']}剩余血量{player1['气血']}", bot_id))
            
            elif 8<= boss_sub <= 16:
                 play_list.append(get_boss_dict(boss, qx, f"☆------{boss['name']}的回合------☆", bot_id))
                 isCrit, boss_sh = get_turnatk_boss(boss,0,UserBattleBuffDate("9999999"))  # 判定是否暴击 辅修功法14
                 if isCrit:
                     msg2 = "{}：子龙朱雀！！！穿透了对方的护甲！并且发生了会心一击，造成了{}伤害\n"
                 else:
                     msg2 = "{}：子龙朱雀！！！穿透了对方的护甲！造成了{}伤害\n"
                 play_list.append(get_boss_dict(boss, qx, msg2.format(boss['name'], boss_sh * (1 + boss_zs) * (player1_js - random_def + 0.5)  * 3), bot_id))
                 player1['气血'] = player1['气血'] - (((boss_sh * (1 + boss_zs) * (player1_js - random_def + 0.5) * 3)))
                 play_list.append(get_boss_dict(boss, qx, f"{player1['道号']}剩余血量{player1['气血']}", bot_id))
                
            else:
                play_list.append(get_boss_dict(boss, qx, f"☆------{boss['name']}的回合------☆", bot_id))
                isCrit, boss_sh = get_turnatk_boss(boss,0,UserBattleBuffDate("9999999"))  # 判定是否暴击 辅修功法14
                if isCrit:
                    msg2 = "{}发起会心一击，造成了{}伤害\n"
                else:
                    msg2 = "{}发起攻击，造成了{}伤害\n"
                play_list.append(get_boss_dict(boss, qx, msg2.format(boss['name'], boss_sh * (1 + boss_zs)), bot_id))
                player1['气血'] = player1['气血'] - (boss_sh * (1 + boss_zs) * (player1_js - random_def))
                play_list.append(get_boss_dict(boss, qx, f"{player1['道号']}剩余血量{player1['气血']}", bot_id))

        else:
            play_list.append(get_boss_dict(boss, qx, f"☆------{boss['name']}动弹不得！------☆", bot_id))

        if player1['气血'] <= 0:  # 玩家2气血小于0，结算
            play_list.append(
                {"type": "node", "data": {"name": "Bot", "uin": int(bot_id), "content": "{}胜利".format(boss['name'])}})
            suc = "Boss赢了"
            
            #get_stone = int(boss_now_stone * (sh * boss_js / qx))
            #boss['stone'] = boss_now_stone - get_stone

            zx = boss['总血量']
            
            get_stone = int(boss_now_stone * ((qx - boss['气血']) / zx ) * (1 + stone_buff))
            boss['stone'] = boss_now_stone - get_stone


            if isSql:
                XiuxianDateManage().update_user_hp_mp(
                    player1['user_id'], 1,
                    int(player1['真元'] / (1 + user1_mp_buff))
                )

            break

        if player1['气血'] <= 0 or boss['气血'] <= 0:
            play_list.append({"type": "node", "data": {"name": "Bot", "uin": int(bot_id), "content": "逻辑错误！"}})
            break

    return play_list, suc, boss, get_stone


def get_msg_dict(player, player_init_hp, msg):
    return {"type": "node", "data": {"name": f"{player['道号']}，当前血量：{int(player['气血'])} / {int(player_init_hp)}",
                                     "uin": int(player['user_id']), "content": msg}}


def get_boss_dict(boss, boss_init_hp, msg, bot_id):
    return {"type": "node",
            "data": {"name": f"{boss['name']}当前血量：{int(boss['气血'])} / {int(boss_init_hp)}", "uin": int(bot_id),
                     "content": msg}}


def get_user_def_buff(user_id):
    user_armor_data = UserBuffDate(user_id).get_user_armor_buff_data()
    user_weapon_data = UserBuffDate(user_id).get_user_weapon_data() #武器减伤
    user_main_data = UserBuffDate(user_id).get_user_main_buff_data() #功法减伤
    if user_weapon_data is not None:
        weapon_def =  user_weapon_data['def_buff']  #武器减伤
    else:
        weapon_def =0
    if user_main_data is not None:
        main_def =  user_main_data['def_buff']  #功法减伤
    else:
        main_def =0
    if user_armor_data is not None:
        def_buff = user_armor_data['def_buff']  #减伤公式
    else:
        def_buff = 0
    return round(1 - (def_buff + weapon_def + main_def ), 2)  # 初始减伤率

def get_turnatk(player, buff=0, user_battle_buff_date={}): #辅修功法14
    sub_atk = 0
    sub_crit = 0
    sub_dmg = 0
    zwsh =0
    try:
        user_id = player['user_id']
        impart_data = xiuxian_impart.get_user_message(user_id)
        user_buff_data = UserBuffDate(user_id)
        weapon_critatk_data = UserBuffDate(user_id).get_user_weapon_data() #武器会心伤害
        weapon_zw = UserBuffDate(user_id).get_user_weapon_data()
        main_zw = user_buff_data.get_user_main_buff_data()
        if main_zw["ew"] == weapon_zw["zw"] :
            zwsh = 0.5
        else:
            zwsh =0
        
        
        main_critatk_data = user_buff_data.get_user_main_buff_data() #功法会心伤害
        player_sub_open = False #辅修功法14
        user_sub_buff_date = {}
        if user_buff_data.get_user_sub_buff_data() != None:
            user_sub_buff_date = UserBuffDate(user_id).get_user_sub_buff_data()
            player_sub_open = True
        buff_value = int(user_sub_buff_date['buff'])
        buff_type = user_sub_buff_date['buff_type']
        if buff_type == '1':
            sub_atk = buff_value / 100
        else:
            sub_atk = 0
        if buff_type == '2':
            sub_crit = buff_value / 100
        else:
            sub_crit = 0
        if buff_type == '3':
            sub_dmg = buff_value / 100
        else:
            sub_dmg = 0
    except:
        impart_data = None
        weapon_critatk_data = None
        main_critatk_data = None
    impart_know_per = impart_data.impart_know_per if impart_data is not None else 0
    impart_burst_per = impart_data.impart_burst_per if impart_data is not None else 0
    weapon_critatk = weapon_critatk_data['critatk'] if weapon_critatk_data is not None else 0 #武器会心伤害
    main_critatk = main_critatk_data['critatk'] if main_critatk_data is not None else 0 #功法会心伤害
    isCrit = False
    turnatk = int(round(random.uniform(0.95, 1.05), 2) 
                  * (player['攻击'] *  (buff + sub_atk + 1) * (1 - boss_jg)) * (1 + zwsh))  # 攻击波动,buff是攻击buff
    if random.randint(0, 100) <= player['会心'] + (impart_know_per + sub_crit - boss_jh + random_hx )* 100:  # 会心判断
        turnatk = int(turnatk * (1.5 + impart_burst_per + weapon_critatk + main_critatk + sub_dmg - boss_jb)) #boss战、切磋、秘境战斗会心伤害公式（不包含抢劫）
        isCrit = True
    return isCrit, turnatk

def get_turnatk_boss(player, buff=0, user_battle_buff_date={}): #boss伤害计算公式
    isCrit = False
    turnatk = int(round(random.uniform(0.95, 1.05), 2) 
                  * (player['攻击'] *  (buff  + 1)))  # 攻击波动,buff是攻击buff
    if random.randint(0, 100) <= player['会心'] + boss_hx * 100:  # 会心判断
        turnatk = int(turnatk * (1.5 + boss_bs )) #boss战、切磋、秘境战斗会心伤害公式（不包含抢劫）
        isCrit = True
    return isCrit, turnatk

def isEnableUserSikll(player, hpcost, mpcost, turncost, skillrate):  # 是否满足技能释放条件
    skill = False
    if turncost < 0:  # 判断是否进入休息状态
        return skill

    if player['气血'] > hpcost and player['真元'] >= mpcost:  # 判断血量、真元是否满足
        if random.randint(0, 100) <= skillrate:  # 随机概率释放技能
            skill = True
    return skill


def get_skill_hp_mp_data(player, secbuffdata):
    user_id = player['user_id']
    weapon_data = UserBuffDate(user_id).get_user_weapon_data()
    if weapon_data is not None and "mp_buff" in weapon_data:
        weapon_mp = weapon_data["mp_buff"]
    else:
        weapon_mp = 0

    hpcost = int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0
    mpcost = int(secbuffdata['mpcost'] * player['exp'] * (1 - weapon_mp )) if secbuffdata['mpcost'] != 0 else 0
    return hpcost, mpcost, secbuffdata['skill_type'], secbuffdata['rate']


def calculate_skill_cost(player, hpcost, mpcost):
    player['气血'] = player['气血'] - hpcost  # 气血消耗
    player['真元'] = player['真元'] - mpcost  # 真元消耗

    return player


def get_persistent_skill_msg(username, skillname, sh, turn):
    if sh:
        return f"{username}的封印技能：{skillname}，剩余回合：{turn}!"
    return f"{username}的持续性技能：{skillname}，造成{sh}伤害，剩余回合：{turn}!"


def get_skill_sh_data(player, secbuffdata):
    skillmsg = ''
    if secbuffdata['skill_type'] == 1:  # 连续攻击类型
        turncost = -secbuffdata['turncost']
        isCrit, turnatk = get_turnatk(player)
        atkvalue = secbuffdata['atkvalue']  # 列表
        skillsh = 0
        atkmsg = ''
        for value in atkvalue:
            atkmsg += f"{int(value * turnatk)}伤害、"
            skillsh += int(value * turnatk)

        if turncost == 0:
            turnmsg = '!'
        else:
            turnmsg = f"，休息{secbuffdata['turncost']}回合！"

        if isCrit:
            skillmsg = f"{player['道号']}发动技能：{secbuffdata['name']}，消耗气血{int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0}点、真元{int(secbuffdata['mpcost'] * player['exp']) if secbuffdata['mpcost'] != 0 else 0}点，{secbuffdata['desc']}并且发生了会心一击，造成{atkmsg[:-1]}{turnmsg}"
        else:
            skillmsg = f"{player['道号']}发动技能：{secbuffdata['name']}，消耗气血{int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0}点、真元{int(secbuffdata['mpcost'] * player['exp']) if secbuffdata['mpcost'] != 0 else 0}点，{secbuffdata['desc']}造成{atkmsg[:-1]}{turnmsg}"

        return skillmsg, skillsh, turncost

    elif secbuffdata['skill_type'] == 2:  # 持续伤害类型
        turncost = secbuffdata['turncost']
        isCrit, turnatk = get_turnatk(player)
        skillsh = int(secbuffdata['atkvalue'] * player['攻击'])  # 改动
        atkmsg = ''
        if isCrit:
            skillmsg = f"{player['道号']}发动技能：{secbuffdata['name']}，消耗气血{int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0}点、真元{int(secbuffdata['mpcost'] * player['exp']) if secbuffdata['mpcost'] != 0 else 0}点，{secbuffdata['desc']}并且发生了会心一击，造成{skillsh}点伤害，持续{turncost}回合！"
        else:
            skillmsg = f"{player['道号']}发动技能：{secbuffdata['name']}，消耗气血{int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0}点、真元{int(secbuffdata['mpcost'] * player['exp']) if secbuffdata['mpcost'] != 0 else 0}点，{secbuffdata['desc']}造成{skillsh}点伤害，持续{turncost}回合！"

        return skillmsg, skillsh, turncost

    elif secbuffdata['skill_type'] == 3:  # 持续buff类型
        turncost = secbuffdata['turncost']
        skillsh = secbuffdata['buffvalue']
        atkmsg = ''
        if secbuffdata['bufftype'] == 1:
            skillmsg = f"{player['道号']}发动技能：{secbuffdata['name']}，消耗气血{int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0}点、真元{int(secbuffdata['mpcost'] * player['exp']) if secbuffdata['mpcost'] != 0 else 0}点，{secbuffdata['desc']}攻击力增加{skillsh}倍，持续{turncost}回合！"
        elif secbuffdata['bufftype'] == 2:
            skillmsg = f"{player['道号']}发动技能：{secbuffdata['name']}，消耗气血{int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0}点、真元{int(secbuffdata['mpcost'] * player['exp']) if secbuffdata['mpcost'] != 0 else 0}点，{secbuffdata['desc']}获得{skillsh * 100}%的减伤，持续{turncost}回合！"

        return skillmsg, skillsh, turncost

    elif secbuffdata['skill_type'] == 4:  # 封印类技能
        turncost = secbuffdata['turncost']
        if random.randint(0, 100) <= secbuffdata['success']:  # 命中
            skillsh = True
            skillmsg = f"{player['道号']}发动技能：{secbuffdata['name']}，消耗气血{int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0}点、真元{int(secbuffdata['mpcost'] * player['exp']) if secbuffdata['mpcost'] != 0 else 0}点，使对手动弹不得,{secbuffdata['desc']}持续{turncost}回合！"
        else:  # 未命中
            skillsh = False
            skillmsg = f"{player['道号']}发动技能：{secbuffdata['name']}，消耗气血{int(secbuffdata['hpcost'] * player['气血']) if secbuffdata['hpcost'] != 0 else 0}点、真元{int(secbuffdata['mpcost'] * player['exp']) if secbuffdata['mpcost'] != 0 else 0}点，{secbuffdata['desc']}但是被对手躲避！"

        return skillmsg, skillsh, turncost


# 处理开局的辅修功法效果
def apply_buff(user_battle_buff, subbuffdata, is_opponent=False):
    buff_type_to_attr = {
        '1': ('atk_buff', "攻击力"),
        '2': ('crit_buff', "暴击率"),
        '3': ('crit_dmg_buff', "暴击伤害"),
        '4': ('health_restore_buff', "气血回复"),
        '5': ('mana_restore_buff', "真元回复"),
        '6': ('health_stolen_buff', "气血吸取"),
        '7': ('mana_stolen_buff', "真元吸取"),
        '8': ('thorns_buff', "中毒"),
        '9': ('hm_stolen_buff', "气血真元吸取"),
        '10': ('jx_buff', "重伤效果"),
        '11': ('fan_buff', "抵消效果"),
        '12': ('stone_buff', "聚宝效果"),
        '13': ('break_buff', "斗战效果"),
    }
    
    attr, desc = buff_type_to_attr[subbuffdata['buff_type']]
    setattr(user_battle_buff, attr, subbuffdata['buff'])
    if int(subbuffdata['buff_type']) >= 0 and int(subbuffdata['buff_type']) <= 10:
        sub_msg = f"提升{subbuffdata['buff']}%{desc}"
    else:
        sub_msg = "获得了特殊效果！！"
    prefix = "。对手" if is_opponent else ""
    return f"{prefix}使用功法{subbuffdata['name']}, {sub_msg}"


def start_sub_buff_handle(player1_sub_open, subbuffdata1, user1_battle_buff_date,
                          player2_sub_open, subbuffdata2, user2_battle_buff_date):
    msg1 = apply_buff(user1_battle_buff_date, subbuffdata1) if player1_sub_open else ""
    msg2 = apply_buff(user2_battle_buff_date, subbuffdata2, is_opponent=True) if player2_sub_open else ""

    return user1_battle_buff_date, user2_battle_buff_date, msg1 + msg2


def before_atk_sub_buff_handle(player, subbuffdata):
    print("123")


# 处理攻击后辅修功法效果
def     after_atk_sub_buff_handle(player1_sub_open, player1, user1_main_buff_data, subbuffdata1, damage1, player2):
    msg = ""

    if not player1_sub_open:
        return player1, player2, msg

    buff_value = int(subbuffdata1['buff'])
    buff_tow = int(subbuffdata1['buff2'])
    buff_type = subbuffdata1['buff_type']
    exp = int(player1['exp'])
    max_hp = int(exp/2) * (1 + user1_main_buff_data['hpbuff'])
    max_mp = exp * (1 + user1_main_buff_data['mpbuff'])
    
    if buff_type == '4':
        restore_health = int(exp/2) * (1 + user1_main_buff_data['hpbuff']) * buff_value // 100
        player1['气血'] += restore_health
        player1['气血'] = min(player1['气血'], max_hp)
        msg = "回复气血:" + str(restore_health)
    elif buff_type == '5':
        restore_mana = exp * (1 + user1_main_buff_data['mpbuff']) * buff_value // 100
        player1['真元'] += restore_mana
        player1['真元'] = min(player1['真元'], max_mp)
        msg = "回复真元:" + str(restore_mana)
    elif buff_type == '6':
        health_stolen = (damage1 * (buff_value + random_xx) // 100) * (1 - boss_xx)
        player1['气血'] += health_stolen
        player1['气血'] = min(player1['气血'], max_hp)
        msg = "吸取气血:" + str(health_stolen)
    elif buff_type == '7':
        mana_stolen = (damage1 * buff_value // 100) * (1 - boss_xl)
        player1['真元'] += mana_stolen
        player1['真元'] = min(player1['真元'], max_mp)
        msg = "吸取真元:" + str(mana_stolen)
    elif buff_type == '8':
        poison_damage = player2['气血'] * buff_value // 100
        player2['气血'] -= poison_damage
        msg = "对手中毒消耗血量:" + str(poison_damage)
        
    elif buff_type == '9':
        health_stolen = (damage1 * (buff_value + random_xx) // 100) * (1 - boss_xx)
        mana_stolen = (damage1 * buff_tow // 100) * (1 - boss_xl)
        player1['气血'] += health_stolen
        player1['气血'] = min(player1['气血'], max_hp)
        player1['真元'] += mana_stolen
        player1['真元'] = min(player1['真元'], max_mp)
        msg = f"吸取气血: {str(health_stolen)}, 吸取真元: {str(mana_stolen)}"

    return player1, player2, msg


class UserBattleBuffDate: #辅修功法14
    def __init__(self, user_id):
        """用户战斗Buff数据"""
        self.user_id = user_id
        # 攻击buff
        self.atk_buff = 0
        # 攻击buff
        self.atk_buff_time = -1

        # 暴击率buff
        self.crit_buff = 0
        # 暴击率buff
        self.crit_buff_time = -1

        # 暴击伤害buff
        self.crit_dmg_buff = 0
        # 暴击伤害buff
        self.crit_dmg__buff_time = -1

        # 回血buff
        self.health_restore_buff = 0
        self.health_restore_buff_time = -1
        # 回蓝buff
        self.mana_restore_buff = 0
        self.mana_restore_buff_time = -1

        # 吸血buff
        self.health_stolen_buff = 0
        self.health_stolen_buff_time = -1
        # 吸蓝buff
        self.mana_stolen_buff = 0
        self.mana_stolen_buff_time = -1
        # 反伤buff
        self.thorns_buff = 0
        self.thorns_buff_time = -1

        # 破甲buff
        self.armor_break_buff = 0
        self.armor_break_buff_time = -1