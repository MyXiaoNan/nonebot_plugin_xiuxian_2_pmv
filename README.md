<div align="center">
  <br>
</div>

<div align="center">

# 🎉 修仙2.2魔改版

_✨ QQ群聊修仙文字游戏✨_

🧬 主要是青木猫画饼3.0期间做的一些魔改和优化！🎉 

<p align="center">
</p>
</div>

# 📖 介绍
一款适用于QQ群的修仙插件,设定征集中，有好的想法可以推送给我哦~~~

原插件地址：https://github.com/QingMuCat/nonebot_plugin_xiuxian_2

# 🎉 和原版有什么区别？
1、修复了许多Bug，报错与原版相比少很多，以及更多功能优化

2、新增了更多指令，例如：合成武器，仙途奇缘（新手灵石礼包），轮回重修等等

3、支持全部转图片发送，支持图片压缩率等等，并且可以在配置文件中更改

4、新增各种丹药，装备，功法，礼包

5、更多不同请自行探索

# 💿 安装
1、手动安装(所有改动都会在dev稳定后合并到master)
```
git clone --depth=1 https://github.com/wsdtl/nonebot_plugin_xiuxian_2_pmv

dev分支可选

git clone -b dev --depth=1 https://github.com/wsdtl/nonebot_plugin_xiuxian_2_pmv
```

2、将git下来的data文件夹移动到bot根目录

3、安装依赖
```
pip install -r requirements.txt
```

4、在.env.*文件中设置超管与机器人昵称
```
SUPERUSERS = ["xxxxx"]
NICKNAME = ["xx"]
```

5、在xiuxian_config.py中配置好各种选项
```
一般来说，只需要关注下面几项：
self.merge_forward_send = False # 消息转发类型,True是合并转发，False是长图发送
self.img_compression_limit = 80 # 图片压缩率，0为不压缩，最高100
self.img_type = "webp" # 图片类型，webp或者jpeg，如果机器人的图片消息不显示请使用jpeg
self.img_send_type = "io" # 图片发送类型,默认io,官方bot建议base64
self.third_party_bot = True # 是否是野生机器人，是的话填True，官方bot请填False
```

5、如解决不了进交流群：[760517008](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=zIKrPPqNStgZnRtuLhiOv9woBQSMQurq&authKey=Nrqm0zDxYKP2Fon2MskbNRmZ588Rqm79lJvQyVYWtkh9vDFK1RGBK0UhqzehVyDw&noverify=0&group_code=760517008) 提问，提问请贴上完整的日志

# 💿 使用
群聊发送 启用修仙功能 后根据引导来即可，不支持私聊
如果你使用的是官方机器人记得改配置

# 💿 配置文件
1、配置文件一般在data/xiuxian文件夹下，自行按照json格式修改即可，一些字段的含义可以进群交流<br>
2、子插件的配置会在插件运行后在子插件文件中生成config.json文件，该文件字段含义在同级目录的xxxconfig.py有备注。注意：修改配置只需要修改json即可，修改.py文件的话需要删除json文件才会生效，任何修改都需要重启bot<br>
3、记得将git下来的data文件夹放置于bot根目录下<br>
4、总的参数配置在xiuxian_config.py中<br>
5、更多详情可见 [文档](https://xiuxian.netlify.app/) (仅供参考)<br>

# 💿 风控配置
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

# 🎉 特别感谢
- [NoneBot2](https://github.com/nonebot/nonebot2)：本插件实装的开发框架，NB天下第一可爱。
- [nonebot_plugin_xiuxian](https://github.com/s52047qwas/nonebot_plugin_xiuxian)：原版修仙
- [nonebot_plugin_xiuxian_2](https://github.com/QingMuCat/nonebot_plugin_xiuxian_2)：原版修仙2

# 🎉 支持
- 大家喜欢的话可以给这个项目点个star
- 有bug、意见和建议都欢迎提交 [Issues](https://github.com/wsdtl/nonebot_plugin_xiuxian_2_pmv/issues) 
- 3.0版本正在路上，敬请期待(日常拷打青木猫)

# 🎉 许可证
本项目使用 [MIT](https://choosealicense.com/licenses/mit/) 作为开源许可证，并且没有cc限制
