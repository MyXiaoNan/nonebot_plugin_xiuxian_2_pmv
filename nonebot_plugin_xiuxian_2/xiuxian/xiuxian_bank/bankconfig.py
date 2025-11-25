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
        "1": {"savemax": 1000000, "levelup": 200000, 'interest': 0.001, "level": "凡铜会员"},
        "2": {"savemax": 2000000, "levelup": 400000, 'interest': 0.001, "level": "凡银会员"},
        "3": {"savemax": 4000000, "levelup": 800000, 'interest': 0.001, "level": "凡金会员"},
        "4": {"savemax": 8000000, "levelup": 1600000, 'interest': 0.001, "level": "玄铜会员"},
        "5": {"savemax": 16000000, "levelup": 3200000, 'interest': 0.001, "level": "玄银会员"},
        "6": {"savemax": 32000000, "levelup": 6400000, 'interest': 0.001, "level": "玄金会员"},
        "7": {"savemax": 64000000, "levelup": 12800000, 'interest': 0.001, "level": "灵铜会员"},
        "8": {"savemax": 128000000, "levelup": 25600000, 'interest': 0.001, "level": "灵银会员"},
        "9": {"savemax": 256000000, "levelup": 51200000, 'interest': 0.001, "level": "灵金会员"},
        "10": {"savemax": 512000000, "levelup": 102400000, 'interest': 0.001, "level": "仙铜会员"},
        "11": {"savemax": 1024000000, "levelup": 204800000, 'interest': 0.001, "level": "仙银会员"},
        "12": {"savemax": 2048000000, "levelup": 409600000, 'interest': 0.001, "level": "仙金会员"},
        "13": {"savemax": 4096000000, "levelup": 819200000, 'interest': 0.001, "level": "天铜会员"},
        "14": {"savemax": 8192000000, "levelup": 1638400000, 'interest': 0.001, "level": "天银会员"},
        "15": {"savemax": 16384000000, "levelup": 3276800000, 'interest': 0.001, "level": "天金会员"},
        "16": {"savemax": 32768000000, "levelup": 6553600000, 'interest': 0.001, "level": "玉铜会员"},
        "17": {"savemax": 65536000000, "levelup": 13107200000, 'interest': 0.001, "level": "玉银会员"},
        "18": {"savemax": 131072000000, "levelup": 26214400000, 'interest': 0.001, "level": "玉金会员"},
        "19": {"savemax": 262144000000, "levelup": 52428800000, 'interest': 0.001, "level": "圣铜会员"},
        "20": {"savemax": 524288000000, "levelup": 104857600000, 'interest': 0.001, "level": "圣银会员"},
        "21": {"savemax": 1048576000000, "levelup": 209715200000, 'interest': 0.001, "level": "圣金会员"},
        "22": {"savemax": 2097152000000, "levelup": 419430400000, 'interest': 0.001, "level": "道铜会员"},
        "23": {"savemax": 4194304000000, "levelup": 838860800000, 'interest': 0.001, "level": "道银会员"},
        "24": {"savemax": 8388608000000, "levelup": 1677721600000, 'interest': 0.001, "level": "道金会员"},
        "25": {"savemax": 16777216000000, "levelup": 3355443200000, 'interest': 0.001, "level": "混元铜会员"},
        "26": {"savemax": 33554432000000, "levelup": 6710886400000, 'interest': 0.001, "level": "混元银会员"},
        "27": {"savemax": 67108864000000, "levelup": 13421772800000, 'interest': 0.001, "level": "混元金会员"},
        "28": {"savemax": 134217728000000, "levelup": 26843545600000, 'interest': 0.001, "level": "太乙铜会员"},
        "29": {"savemax": 268435456000000, "levelup": 53687091200000, 'interest': 0.001, "level": "太乙银会员"},
        "30": {"savemax": 536870912000000, "levelup": 107374182400000, 'interest': 0.001, "level": "太乙金会员"},
        "31": {"savemax": 1073741824000000, "levelup": 214748364800000, 'interest': 0.001, "level": "太虚铜会员"},
        "32": {"savemax": 2147483648000000, "levelup": 429496729600000, 'interest': 0.001, "level": "太虚银会员"},
        "33": {"savemax": 4294967296000000, "levelup": 858993459200000, 'interest': 0.001, "level": "太虚金会员"},
        "34": {"savemax": 8589934592000000, "levelup": 1717986918400000, 'interest': 0.001, "level": "鸿蒙铜会员"},
        "35": {"savemax": 17179869184000000, "levelup": 3435973836800000, 'interest': 0.001, "level": "鸿蒙银会员"},
        "36": {"savemax": 34359738368000000, "levelup": 6871947673600000, 'interest': 0.001, "level": "鸿蒙金会员"},
        "37": {"savemax": 68719476736000000, "levelup": 13743895347200000, 'interest': 0.001, "level": "盘古铜会员"},
        "38": {"savemax": 137438953472000000, "levelup": 27487790694400000, 'interest': 0.001, "level": "盘古银会员"},
        "39": {"savemax": 274877906944000000, "levelup": 54975581388800000, 'interest': 0.001, "level": "盘古金会员"},
        "40": {"savemax": 549755813888000000, "levelup": 109951162777600000, 'interest': 0.001, "level": "洪荒铜会员"},
        "41": {"savemax": 1099511627776000000, "levelup": 219902325555200000, 'interest': 0.001, "level": "洪荒银会员"},
        "42": {"savemax": 2199023255552000000, "levelup": 439804651110400000, 'interest': 0.001, "level": "洪荒金会员"},
        "43": {"savemax": 4398046511104000000, "levelup": 879609302220800000, 'interest': 0.001, "level": "开天铜会员"},
        "44": {"savemax": 8796093022208000000, "levelup": 1759218604441600000, 'interest': 0.001, "level": "开天银会员"},
        "45": {"savemax": 17592186044416000000, "levelup": 3518437208883200000, 'interest': 0.001, "level": "开天金会员"},
        "46": {"savemax": 35184372088832000000, "levelup": 7036874417766400000, 'interest': 0.001, "level": "太初铜会员"},
        "47": {"savemax": 70368744177664000000, "levelup": 14073748835532800000, 'interest': 0.001, "level": "太初银会员"},
        "48": {"savemax": 140737488355328000000, "levelup": 0, 'interest': 0.001, "level": "太初金会员"},
    }
}


def get_config():
    try:
        config = readf()
        for key in configkey:
            if key not in list(config.keys()):
                config[key] = CONFIG[key]
        savef(config)
    except FileNotFoundError:
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
