import asyncio
import datetime
import json
import pprint
import zlib
from typing import Callable

import requests
from aiohttp import WSMsgType, ClientSession

from BiliLiveCtrl_lua.BiliBiliAPI_limited import start_login
from BiliLiveCtrl_lua.BiliBili_api_limited import cookieFormat2dict, BiliGeneralApi

cookie = start_login(3546559824267399)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    'cookie': cookie,
}


class Normal:
    def __init__(self, headers: dict, roomid: int):
        self.headers = headers
        self.roomid = roomid

        def user__get_user_info() -> dict:
            """
            获得 经验值信息部分和B站直播间财产信息
            get_url：https://api.live.bilibili.com/xlive/web-ucenter/user/get_user_info
            @return:
            <pre>{<br>&#32;&#32;"uid":&#32;int(B站uid),<br>&#32;&#32;"uname":&#32;str(B站昵称),<br>&#32;&#32;"face":&#32;str(头像url),<br>&#32;&#32;"billCoin":&#32;int(硬币数),<br>&#32;&#32;"silver":int(直播间银瓜子数),<br>&#32;&#32;"gold":&#32;int(直播间电池值：1人民币=&gt;10电池=&gt;1000电池值),<br>&#32;&#32;"achieve":int(成就值),<br>&#32;&#32;"vip":&#32;0,<br>&#32;&#32;"svip":&#32;0,<br>&#32;&#32;"user_level":&#32;int(B站用户等级),<br>&#32;&#32;"user_next_level":int(下一级B站用户等级),<br>&#32;&#32;"user_intimacy":int(当前B站用户等级经验值：1人民币=&gt;1000用户等级经验值),<br>&#32;&#32;"user_next_intimacy":int(当前B站用户等级经验值槽总量),<br>&#32;&#32;"is_level_top":&#32;0,<br>&#32;&#32;"user_level_rank":&#32;"&gt;50000：疑似当前B站用户等级经验值排名",<br>&#32;&#32;"user_charged":&#32;0,<br>&#32;&#32;"identification":&#32;1,<br>&#32;&#32;"wealth_info":&#32;{<br>&#32;&#32;&#32;&#32;"cur_score":int(当前直播间荣耀等级经验值),<br>&#32;&#32;&#32;&#32;"dm_icon_key":&#32;"",<br>&#32;&#32;&#32;&#32;"level":&#32;int(直播间荣耀等级),<br>&#32;&#32;&#32;&#32;"level_total_score":int(当前直播间荣耀等级经验值槽总量),<br>&#32;&#32;&#32;&#32;"status":&#32;int(直播间荣耀等级权益锁定状态:1=&gt;开启，2=&gt;锁定，0可能是未激活荣耀等级),<br>&#32;&#32;&#32;&#32;"uid":int(B站uid),<br>&#32;&#32;&#32;&#32;"upgrade_need_score":int(直播间荣耀等级进入下一级所需经验值：1人民币=&gt;1000直播间荣耀等级经验值)<br>&#32;&#32;}<br>}</pre>
            """
            url = f"https://api.live.bilibili.com/xlive/web-ucenter/user/get_user_info"
            get_user_info_data = {}
            try:
                request = requests.get(url, headers=self.headers).json()
                get_user_info_data = request['data']
            except Exception as r:
                print(f'请检查网络，{r}')
            return get_user_info_data

        self.__user__get_user_info = user__get_user_info
        self.__BiliGeneralApi = BiliGeneralApi(headers)

    def connect(self):
        """

        :param roomid: 需要连接弹幕的长房间号
        :return:
        """
        cookie = self.headers['cookie']
        DanmuInfo = self.__BiliGeneralApi.getDanmuInfo(self.roomid)
        key = DanmuInfo['data']['token']
        wss_url = f"wss://{DanmuInfo['data']['host_list'][-1]['host']}:{DanmuInfo['data']['host_list'][-1]['wss_port']}/sub"
        auth_body = {
            "uid": self.__user__get_user_info()["uid"],
            "roomid": self.roomid,
            "protover": 2,
            "buvid": cookieFormat2dict(cookie)['buvid3'],
            "platform": "web",
            "type": 3,
            "key": key
        }
        auth_body = json.dumps(auth_body, ensure_ascii=False)
        return wss_url, auth_body


class session:
    """
    使用session获取弹幕的实例
    """
    __savedamudata = set()

    def __init__(self, url: str, auth_body: str):
        """
        鉴权协议认证
        :param auth_body:
        开放平台的在start_app函数的["data"]["websocket_info"]["auth_body"]<br>
        普通的格式为
        :param wss_url:
        """
        self.url = url
        self.auth_body = auth_body

    class Opt:
        HEARTBEAT = 2
        HEARTBEAT_REPLY = 3
        SEND_SMS_REPLY = 5
        AUTH = 7
        AUTH_REPLY = 8

    class Version:
        NORMAL = 0
        ZIP = 2

    async def on_open(self, session):
        print("已连接服务...")
        self.session = session

        # 鉴权协议包
        auth_pack = self.generate_auth_pack(self.auth_body)
        await session.send_bytes(auth_pack)

        # 每30秒发送心跳包
        async def send_heartbeat():
            while True:
                try:
                    heartbeat_pack = self.generate_heartbeat_pack()
                    await session.send_bytes(heartbeat_pack)
                except Exception as e:
                    raise RuntimeError(e)
                await asyncio.sleep(30)

        asyncio.create_task(send_heartbeat())

    async def on_message(self, msg):
        if msg.type == WSMsgType.BINARY:
            # 解包
            self.unpack(msg.data)

    async def connect(self):
        """
        连接WSS
        :param uri: WSS/WS服务器网址
        """
        async with ClientSession() as session:
            async with session.ws_connect(self.url) as ws:
                await self.on_open(ws)
                while True:
                    msg = await ws.receive()
                    await self.on_message(msg)
                # async for msg in ws:
                #     # print(msg)
                #     await self.on_message(msg)
                #     print(f"接收到消息：{message}")

    def pack(self, json_str, code):
        content_bytes = b''
        if code == self.Opt.AUTH:
            content_bytes = json_str.encode('utf-8')
        header = (len(content_bytes) + 16).to_bytes(4, 'big') + \
                 (16).to_bytes(2, 'big') + \
                 self.Version.NORMAL.to_bytes(2, 'big') + \
                 code.to_bytes(4, 'big') + \
                 (1).to_bytes(4, 'big')

        return header + content_bytes

    def generate_auth_pack(self, json_str):
        return self.pack(json_str, self.Opt.AUTH)

    def generate_heartbeat_pack(self):
        return self.pack(None, self.Opt.HEARTBEAT)

    def unpack(self, byte_buffer):
        # print(byte_buffer)
        package_len = int.from_bytes(byte_buffer[0:4], 'big')
        head_length = int.from_bytes(byte_buffer[4:6], 'big')
        prot_ver = int.from_bytes(byte_buffer[6:8], 'big')
        opt_code = int.from_bytes(byte_buffer[8:12], 'big')
        sequence = int.from_bytes(byte_buffer[12:16], 'big')

        content_bytes = byte_buffer[16:package_len]
        if prot_ver == self.Version.ZIP:
            content_bytes = zlib.decompress(content_bytes)
            self.unpack(content_bytes)
            return

        content = content_bytes.decode('utf-8')
        # print(content)
        if content not in self.__savedamudata:
            self.__savedamudata.add(content)
            if opt_code == self.Opt.AUTH_REPLY:
                # print(f"这是鉴权回复：{content}")
                self.AuthenticationReply = content
            elif opt_code == self.Opt.SEND_SMS_REPLY:
                # print(f"真正的弹幕消息：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_{content}")
                # 使用json.loads将字符串转换为JSON对象
                json_data = json.loads(content)
                # 使用json.dumps将JSON对象转换为带缩进格式的字符串
                formatted_json_string = json.dumps(json_data, indent=4)
                # 打印类型和格式化后的JSON字符串
                print(f"{type(json_data)}\n{formatted_json_string}\n")
                self.DanmuInfo = content
                # todo 自定义处理

        if len(byte_buffer) > package_len:
            self.unpack(byte_buffer[package_len:])

    async def main(self):
        """
        搭建WSS长连接
        :param uri: WSS服务器网址
        :return:
        """
        connectNum = 50
        if "group" in list(json.loads(self.auth_body).keys()):
            if json.loads(self.auth_body)["group"] == "open":
                connectNum = 1
        tasks = [self.connect() for _ in range(connectNum)]
        await asyncio.gather(*tasks)

    def starDanMu(self):
        asyncio.run(self.main())

# fd = Normal(headers, 1960179)
# print(fd.connect())
# wss_url, auth_body = fd.connect()
# danm = session(wss_url, auth_body)
# danm.starDanMu()