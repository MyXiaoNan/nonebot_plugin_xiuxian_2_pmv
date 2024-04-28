<div align="center">
  <br>
</div>

<div align="center">

# 修仙2.0魔改版

_✨ QQ群聊修仙文字游戏✨_

🧬 主要是青木猫画饼3.0期间做的一些魔改！🎉 

<p align="center">
</p>
</div>

## 📖 介绍

一款适用于QQ群的修仙插件,设定征集中，有好的想法可以推送给我哦~~~

原插件地址：https://github.com/QingMuCat/nonebot_plugin_xiuxian_2


## 💿 安装

详情可见 [文档](https://xiuxian.netlify.app/)

### 下载


1. 手动安装(非常建议)

```
git clone https://github.com/wsdtl/nonebot_plugin_xiuxian_2_pmv
```

2、安装依赖
```
pip install -r requirements.txt
```
3、在.env.*文件中设置超管与机器人昵称
```
SUPERUSERS = ["xxxxx"]
NICKNAME = ["xx"]
```

4、如解决不了进交流群：[760517008](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=zIKrPPqNStgZnRtuLhiOv9woBQSMQurq&authKey=Nrqm0zDxYKP2Fon2MskbNRmZ588Rqm79lJvQyVYWtkh9vDFK1RGBK0UhqzehVyDw&noverify=0&group_code=760517008) 提问，提问请贴上完整的日志


## 配置文件
1、配置文件一般在data/xiuxian文件夹下，自行按照json格式修改即可，一些字段的含义可以进群交流<br>
2、子插件的配置会在插件运行后在子插件文件中生成config.json文件，该文件字段含义在同级目录的xxxconfig.py有备注。注意：修改配置只需要修改json即可，修改.py文件的话需要删除json文件才会生效，任何修改都需要重启bot<br>
3、记得将git下来的data文件夹放置于bot根目录下<br>
4、总的参数配置在xiuxian_utils/xiuxian_config.py中
```
self.img = True # 是否使用图片发送，True是使用图片发送，False是使用文字发送
self.user_info_image = True # 是否使用图片发送个人信息，True是使用图片发送，False是使用文字发送
self.level = list(USERRANK.keys()) # 别动
self.user_info_cd = 30  # 我的存档cd/秒
self.level_up_cd = 0  # 突破CD(分钟)
self.closing_exp = 90  # 闭关每分钟获取的修为
self.put_bot = []  # 接收消息qq,主qq，框架将只处理此qq的消息，
self.main_bo = []  # 负责发送消息的qq
self.shield_group = []  # 屏蔽的群聊
self.layout_bot_dict = {}
# QQ所负责的群聊
# "123456":"123456",
self.sect_min_level = "铭纹境圆满" # 创建宗门最低境界
self.sect_create_cost = 5000000 # 创建宗门消耗
self.sect_rename_cost = 5000000000 # 宗门改名消耗
self.sect_rename_cd = 86400 # 宗门改名cd/秒
self.closing_exp_upper_limit = 3  # 闭关获取修为上限（例如：1.5 下个境界的修为数*1.5）
self.level_punishment_floor = 1  # 突破失败扣除修为，惩罚下限（百分比）
self.level_punishment_limit = 10  # 突破失败扣除修为，惩罚上限(百分比)
self.level_up_probability = 0.3  # 突破失败增加当前境界突破概率的比例
self.sign_in_lingshi_lower_limit = 1000000  # 每日签到灵石下限
self.sign_in_lingshi_upper_limit = 5000000  # 每日签到灵石上限
self.beg_max_level = "铭纹境圆满" # 仙途奇缘能领灵石最高境界
self.beg_max_days = 7 # 仙途奇缘能领灵石最多天数
self.beg_lingshi_lower_limit = 200000000  # 仙途奇缘灵石下限
self.beg_lingshi_upper_limit = 500000000  # 仙途奇缘灵石上限
self.tou = 1000000  # 偷灵石惩罚
self.tou_cd = 30  # 偷灵石cd/秒
self.battle_boss_cd = 0  # 讨伐bosscd/秒
self.dufang_cd = 10  # 金银阁cd/秒
self.tou_lower_limit = 0.01  # 偷灵石下限(百分比)
self.tou_upper_limit = 0.30  # 偷灵石上限(百分比)
self.remake = 100000  # 重入仙途的消费
self.lunhui_min_level = "遁一境初期" # 千世轮回最低境界
self.twolun_min_level = "虚道境初期" # 万世轮回最低境界
self.del_boss_id = []  # 支持非管理员和超管天罚boss
self.gen_boss_id = []  # 支持非管理员和超管生成boss
self.merge_forward_send = False # 消息转发类型,True是合并转发，False是长图发送
self.img_compression_limit = 100 # 图片压缩率，0为不压缩，最高100
self.version = "xiuxian_2.2" # 修仙插件版本，别动
```


## 风控配置
```
配置地址:修仙插件下xiuxian_config.py
在只有一个qq链接的情况下风控配置应该全部为空，即不配置
self.put_bot = []  # 接收消息qq,主qq,框架将只处理此qq的消息，不配置将默认设置第一个链接的qq为主qq
self.main_bo = []  # 负责发送消息的qq,调用lay_out.py 下range_bot函数的情况下需要填写
self.shield_group = []  # 屏蔽的群聊
self.layout_bot_dict = {{}}  # QQ所负责的群聊{{群 :bot}}   其中 bot类型 []或str
示例： {
    "群123群号" : "对应发送消息的qq号"
    "群456群号" ： ["对应发送消息的qq号1","对应发送消息的qq号2"]
}
当后面qq号为一个字符串时为一对一，为列表时为多对一
```
## 一些问题



# 🎉 特别感谢

- [NoneBot2](https://github.com/nonebot/nonebot2)：本插件实装的开发框架，NB天下第一可爱。
- [nonebot_plugin_xiuxian](https://github.com/s52047qwas/nonebot_plugin_xiuxian)：原版修仙
- [nonebot_plugin_xiuxian_2](https://github.com/QingMuCat/nonebot_plugin_xiuxian_2)：修仙2


# 🎉支持

- 大家喜欢的话可以给这个项目点个star

- 有bug、意见和建议都欢迎提交 [Issues](https://github.com/wsdtl/nonebot_plugin_xiuxian_2_pmv/issues) 
- 或者联系进入QQ交流群：[760517008](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=zIKrPPqNStgZnRtuLhiOv9woBQSMQurq&authKey=Nrqm0zDxYKP2Fon2MskbNRmZ588Rqm79lJvQyVYWtkh9vDFK1RGBK0UhqzehVyDw&noverify=0&group_code=760517008)
- 3.0版本正在路上，敬请期待(日常拷打青木猫)

# 许可证
本项目使用 [MIT](https://choosealicense.com/licenses/mit/) 作为开源许可证
