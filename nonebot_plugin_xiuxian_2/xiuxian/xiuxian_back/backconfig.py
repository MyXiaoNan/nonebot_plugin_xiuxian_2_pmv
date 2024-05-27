try:
    import ujson as json
except ImportError:
    import json
import os
from pathlib import Path

configkey = ["open", "auctions", "拍卖会定时参数"]
CONFIG = {
    "open": [],
    "auctions": {
      "安神灵液": {
         "id": 1412,
         "start_price": 550000
      },
      "魇龙之血": {
         "id": 1413,
         "start_price": 550000
      },
      "化劫丹": {
         "id": 1414,
         "start_price": 700000
      },
      "太上玄门丹": {
         "id": 1415,
         "start_price": 15000000
      },
      "金仙破厄丹": {
         "id": 1416,
         "start_price": 20000000
      },
      "太乙炼髓丹": {
         "id": 1417,
         "start_price": 50000000
      },
      "地仙玄丸": {
         "id": 2014,
         "start_price": 500000
      },
      "消冰宝丸": {
         "id": 2015,
         "start_price": 1000000
      },
      "生骨丹": {
         "id": 1101,
         "start_price": 1000
      },
      "化瘀丹": {
         "id": 1102,
         "start_price": 3000
      },
      "培元丹": {
         "id": 1103,
         "start_price": 5000
      },
      "培元丹plus": {
         "id": 1104,
         "start_price": 10000
      },
      "黄龙丹": {
         "id": 1105,
         "start_price": 15000
      },
      "回元丹": {
         "id": 1106,
         "start_price": 25000
      },
      "回春丹": {
         "id": 1107,
         "start_price": 40000
      },
      "养元丹": {
         "id": 1108,
         "start_price": 60000
      },
      "太元真丹": {
         "id": 1109,
         "start_price": 80000
      },
      "九阳真丹": {
         "id": 1110,
         "start_price": 100000
      },
      "无始经": {
         "id": 9914,
         "start_price": 55000000
      },
      "不灭天功": {
         "id": 9913,
         "start_price": 55000000
      },
      "射日弓": {
         "id": 8000,
         "start_price": 1500000000
      },
      "遁一丹": {
         "id": 1418,
         "start_price": 70000000
      },
      "至尊丹": {
         "id": 1419,
         "start_price": 100000000
      },
      "极品至尊丹": {
         "id": 1421,
         "start_price": 300000000
      },
      "极品遁一丹": {
         "id": 1420,
         "start_price": 150000000
      },
      "青龙偃月刀": {
         "id": 7097,
         "start_price": 250000000
      },
      "万魔渡": {
         "id": 9924,
         "start_price": 150000000
      },
      "血海魔铠": {
         "id": 6094,
         "start_price": 120000000
      },
      "万剑归宗": {
         "id": 8920,
         "start_price": 700000000
      },
      "华光猎影": {
         "id": 8921,
         "start_price": 600000000
      },
      "灭剑血胧": {
         "id": 8922,
         "start_price": 600000000
      },
      "风神诀": {
         "id": 9926,
         "start_price": 300000000
      },
      "三丰丹经": {
         "id": 9920,
         "start_price": 85000000
      },
      "暗渊灭世功": {
         "id": 9935,
         "start_price": 1200000000
      },
      "太清丹经": {
         "id": 9933,
         "start_price": 1000000000
      },
      "大道归一丹": {
         "id": 15102,
         "start_price": 500000000
      },
      "天地玄功": {
         "id": 9934,
         "start_price": 1150000000
      },
      "渡劫天功": {
         "id": 9931,
         "start_price": 1000000000
      },
      "道师符经": {
         "id": 9921,
         "start_price": 150000000
      },
    },
    "拍卖会定时参数": {  # 拍卖会生成的时间，两个不可全为0
        "hours": "17",
        "minutes": "0"
    }
}


def get_auction_config():
    try:
        config = readf()
        for key in configkey:
            if key not in list(config.keys()):
                config[key] = CONFIG[key]
        if 'user_auctions' not in config:
            config['user_auctions'] = []
        savef_auction(config)
    except:
        config = CONFIG
        config['user_auctions'] = []
        savef_auction(config)
    return config


CONFIGJSONPATH = Path(__file__).parent
FILEPATH = CONFIGJSONPATH / 'config.json'


def readf():
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def savef_auction(data):
    data = json.dumps(data, ensure_ascii=False, indent=3)
    savemode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=savemode, encoding="UTF-8") as f:
        f.write(data)
        f.close()
    return True


def remove_auction_item(auction_id):
    config = get_auction_config()
    auction_id = int(auction_id)
    found = False
    
    for auction in config['user_auctions']:
        for key, value in auction.items():
            if int(value['id']) == auction_id:
                config['user_auctions'].remove(auction)
                found = True
                break
        if found:
            break

    savef_auction(config)



