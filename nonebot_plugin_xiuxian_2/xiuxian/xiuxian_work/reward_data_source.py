import os
from nonebot.log import logger
from ..xiuxian_utils.data_source import *



PLAYERSDATA = Path() / "data" / "xiuxian" / "players"


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
