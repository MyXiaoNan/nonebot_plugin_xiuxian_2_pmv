try:
    import ujson as json
except ImportError:
    import json
import os
from pathlib import Path

configkey = ["BANKLEVEL"]
CONFIG = {
    "BANKLEVEL": {
        # 钱庄等级参数。savemax：当前等级可以存储上限，levelup：升级钱庄等级消耗的灵石数量，interest：每小时给与的利息，level：当前等级会员的名称
        "1": {"savemax": 1000000, "levelup": 200000, 'interest': 0.002, "level": "凡铜会员"},
        "2": {"savemax": 2000000, "levelup": 400000, 'interest': 0.0021, "level": "凡银会员"},
        "3": {"savemax": 4000000, "levelup": 800000, 'interest': 0.0022, "level": "凡金会员"},
        "4": {"savemax": 8000000, "levelup": 1600000, 'interest': 0.0023, "level": "玄铜会员"},
        "5": {"savemax": 16000000, "levelup": 3200000, 'interest': 0.0024, "level": "玄银会员"},
        "6": {"savemax": 32000000, "levelup": 6400000, 'interest': 0.0025, "level": "玄金会员"},
        "7": {"savemax": 64000000, "levelup": 12800000, 'interest': 0.0030, "level": "灵铜会员"},
        "8": {"savemax": 128000000, "levelup": 25600000, 'interest': 0.0035, "level": "灵银会员"},
        "9": {"savemax": 256000000, "levelup": 51200000, 'interest': 0.0040, "level": "灵金会员"},
        "10": {"savemax": 512000000, "levelup": 102400000, 'interest': 0.0045, "level": "仙铜会员"},
        "11": {"savemax": 1024000000, "levelup": 204800000, 'interest': 0.0050, "level": "仙银会员"},
        "12": {"savemax": 2048000000, "levelup": 409600000, 'interest': 0.0055, "level": "仙金会员"},
        "13": {"savemax": 4096000000, "levelup": 819200000, 'interest': 0.0060, "level": "天铜会员"},
        "14": {"savemax": 8192000000, "levelup": 1638400000, 'interest': 0.0065, "level": "天银会员"},
        "15": {"savemax": 16384000000, "levelup": 3276800000, 'interest': 0.0070, "level": "天金会员"},
        "16": {"savemax": 32768000000, "levelup": 6553600000, 'interest': 0.0075, "level": "玉铜会员"},
        "17": {"savemax": 65536000000, "levelup": 13107200000, 'interest': 0.0080, "level": "玉银会员"},
        "18": {"savemax": 131072000000, "levelup": 26214400000, 'interest': 0.0085, "level": "玉金会员"},
        "19": {"savemax": 262144000000, "levelup": 52428800000, 'interest': 0.0090, "level": "圣铜会员"},
        "20": {"savemax": 524288000000, "levelup": 104857600000, 'interest': 0.0095, "level": "圣银会员"},
        "21": {"savemax": 1048576000000, "levelup": 209715200000, 'interest': 0.0100, "level": "圣金会员"},
        "22": {"savemax": 2097152000000, "levelup": 419430400000, 'interest': 0.0105, "level": "道铜会员"},
        "23": {"savemax": 4194304000000, "levelup": 838860800000, 'interest': 0.0110, "level": "道银会员"},
        "24": {"savemax": 8388608000000, "levelup": 0, 'interest': 0.0120, "level": "道金会员"},
    }
}


def get_config():
    try:
        config = readf()
        for key in configkey:
            if key not in list(config.keys()):
                config[key] = CONFIG[key]
        savef(config)
    except:
        config = CONFIG
        savef(config)
    return config


CONFIGJSONPATH = Path(__file__).parent
FILEPATH = CONFIGJSONPATH / 'config.json'


def readf():
    with open(FILEPATH, "r", encoding="UTF-8") as f:
        data = f.read()
    return json.loads(data)


def savef(data):
    data = json.dumps(data, ensure_ascii=False, indent=3)
    savemode = "w" if os.path.exists(FILEPATH) else "x"
    with open(FILEPATH, mode=savemode, encoding="UTF-8") as f:
        f.write(data)
        f.close()
    return True
