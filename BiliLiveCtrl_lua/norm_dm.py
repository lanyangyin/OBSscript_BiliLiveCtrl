import asyncio
import datetime
import hashlib
import hmac
import json
import random
import time
import zlib
from typing import Callable
from urllib.parse import unquote

import requests
import websockets


def html_url_decode(encoded_string: str) -> str:
    """
    # 使用 unquote 函数进行 HTML URL 解码
    :param encoded_string:
    :return:HTML URL 解码后 的字符串
    """
    decoded_string = unquote(encoded_string)
    return decoded_string


def cookieFormat2dict(cookieFormat_text: str) -> dict:
    """
    将cookice格式的文本转换成字典
    cookie-name可以包含除了控制字符（ASCII 字符 0 至 31，以及 ASCII 字符 127）和分隔符（空格、制表符和以下字符：( ) < > @ , ; : \ " / [ ] ? = { }）之外的任何 US-ASCII 字符。
    cookie-value可以选择包裹在双引号中。支持除了控制字符（ASCII 字符 0 至 31，以及 ASCII 字符 127）、空白字符、双引号、逗号、分号以及反斜杠之外的任意 US-ASCII 字符。
    编码：许多实现会对 cookie 值进行 URL 编码。但是按照 RFC 规范，这不是必须的。不过 URL 编码有助于满足 <cookie-value> 对允许使用的字符的要求。
    :param cookieFormat_text: cookice格式的文本;
    :return:
    """
    cookieDict = {}
    cookieFormat_is = True
    if cookieFormat_text.endswith(';'):
        cookieFormat_text = cookieFormat_text.split(';', -1)[0]
    if cookieFormat_text.count(';') + 1 == cookieFormat_text.count('='):
        for i in cookieFormat_text.split(';'):
            if '=' not in i:
                print('"="的html url编码为"%3D"')
                cookieFormat_is = False
            else:
                pass
        if cookieFormat_is:
            cookie_ = ''
            for i in cookieFormat_text.split(';'):
                cookie_name = html_url_decode(i.split('=', 1)[0].strip())
                cookie_value = html_url_decode(i.split('=', 1)[1].strip())
                if i != cookieFormat_text.split(';')[-1]:
                    cookie_ += f'\"{cookie_name}\": \"{cookie_value}\", '
                else:
                    cookie_ += f'\"{cookie_name}\": \"{cookie_value}\"'
            cookieDict = json.loads('{' + cookie_ + '}')
        else:
            print('请检查";"和"="，可以转换成html url编码')
    else:
        print('"="出现的次数应该为";"的数量加一，可以转换成html url编码')
    return cookieDict


class BiliGeneralApi:
    """
    实例：B站通用api
    """

    def __init__(self, headers: dict):
        """
        为实例配置一个headers
        :param headers: 看情况带cookie的headers
        """
        self.headers = headers

    def passport_login__web__qrcode__generate(self) -> dict:
        """
        获取 登录二维码链接 和 32位二维码密钥
        get_url：https://passport.bilibili.com/x/passport-login/web/qrcode/generate
        :return:
        <table>
            <tbody>
                <tr><td>url</td><td><em>str</em></td><td><u>二维码内容 (登录页面 url)</u></td><td></td></tr>
                <tr><td>qrcode_key</td><td><em>str</em></td><td><u>扫码登录秘钥</u></td><td>恒为32字符</td></tr>
            </tbody>
        </table>
        """
        url = f'https://passport.bilibili.com/x/passport-login/web/qrcode/generate?&go_url=https://link.bilibili.com/'
        generate_data = {}
        try:
            request = requests.get(url, headers=self.headers).json()
            loginQrcodeGenerate_code = request['code']
            if loginQrcodeGenerate_code == 0:
                generate_data = request['data']
            else:
                print(f'获取登录二维码链接失败')
        except Exception as r:
            print(f'请检查网络，{r}')
        return generate_data

    def passport_login__web__qrcode__poll(self, qrcode_key: str):
        """
        获取B站登录二维码 扫描状态
        get_url：https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key=
        :param qrcode_key: 32位二维码密钥
        :return:
        <table>
            <tbody>
                <tr><td>url</td><td><em>str</em></td><td><u>游戏分站跨域登录 url</u></td><td>未登录为空</td></tr>
                <tr><td>refresh_token</td><td><em>str</em></td><td><u>刷新<code>refresh_token</code></u></td><td>未登录为空</td></tr>
                <tr><td>timestamp</td><td><em>num</em></td><td><u>登录时间</u></td><td>未登录为<code>0</code><br>时间戳 单位为毫秒</td></tr>
                <tr><td>code</td><td><em>num</em></td><td><u>0：扫码登录成功<br>86038：二维码已失效<br>86090：二维码已扫码未确认<br>86101：未扫码</u></td><td></td></tr>
                <tr><td>message</td><td><em>str</em></td><td><u>扫码状态信息</u></td><td></td></tr>
            </tbody>
        </table>
        """
        url = f'https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={qrcode_key}'
        loginQrcodePoll_data = {}
        try:
            request = requests.get(url, headers=self.headers).json()
            loginQrcodeGenerate_code = request['code']
            if loginQrcodeGenerate_code == 0:
                loginQrcodePoll_data = request['data']
            else:
                print(f'获取登录二维码返回信息失败')
        except Exception as r:
            print(f'请检查网络，{r}')
        return loginQrcodePoll_data

    def getBili_withBuvid3(self) -> dict:
        """
        获得一个含有 buvid3 的dict，用于完善cookie
        :return:含有 buvid3 的dict
        """
        request = requests.get(url='https://www.bilibili.com', headers=self.headers)
        dict_with_buvid3 = request.cookies.get_dict()
        return dict_with_buvid3

    def getDanmuInfo(self, roomid: int) -> dict:
        """
        获取弹幕消息过程中所需的wss认证包
        :param roomid:直播间真实id
        :return:
        <table>
            <thead>
            <tr>
                <th>字段</th>
                <th><em>类型</em></th>
                <th><u>内容</u></th>
                <th>备注</th>
            </tr>
            </thead>
            <tbody>
            <tr>
                <td>code</td>
                <td><em>num</em></td>
                <td><u>返回值</u></td>
                <td>0：成功<br>65530：token错误（登录错误）<br>1：错误<br>60009：分区不存在<br><strong>（其他错误码有待补充）</strong>
                </td>
            </tr>
            <tr>
                <td>message</td>
                <td><em>str</em></td>
                <td><u>错误信息</u></td>
                <td>默认为空</td>
            </tr>
            <tr>
                <td>ttl</td>
                <td><em>num</em></td>
                <td><u>1</u></td>
                <td></td>
            </tr>
            <tr>
                <td><font color="green">["data"]</font></td>
                <td><em>obj</em></td>
                <td><u>信息本体</u></td>
                <td></td>
            </tr>
            </tbody>
        </table>
        <p><font color="#0A9F0A">["data"]</font></p>
        <table>
            <thead>
            <tr>
                <th>字段</th>
                <th>类型</th>
                <th><u>内容</u></th>
                <th>备注</th>
            </tr>
            </thead>
            <tbody>
            <tr>
                <td>group</td>
                <td>str</td>
                <td><u>live</u></td>
                <td></td>
            </tr>
            <tr>
                <td>business_id</td>
                <td>num</td>
                <td><u>0</u></td>
                <td></td>
            </tr>
            <tr>
                <td>refresh_row_factor</td>
                <td>num</td>
                <td><u>0.125</u></td>
                <td></td>
            </tr>
            <tr>
                <td>refresh_rate</td>
                <td>num</td>
                <td><u>100</u></td>
                <td></td>
            </tr>
            <tr>
                <td>max_delay</td>
                <td>num</td>
                <td><u>5000</u></td>
                <td></td>
            </tr>
            <tr>
                <td>token</td>
                <td>str</td>
                <td><u>认证秘钥</u></td>
                <td></td>
            </tr>
            <tr>
                <td><font color="#0C7287" >["host_list"]</font></td>
                <td>array</td>
                <td><u>信息流服务器节点列表</u></td>
                <td></td>
            </tr>
            </tbody>
        </table>
        <p><font color="#0A9F0A">["data"]</font><font color="#109DBA" >["host_list"][n0-3]</font></p>
        <table>
            <thead>
            <tr>
                <th>字段</th>
                <th><em>类型</em></th>
                <th><u>内容</u></th>
                <th>备注</th>
            </tr>
            </thead>
            <tbody>
            <tr>
                <td>host</td>
                <td><em>str</em></td>
                <td><u>服务器域名</u></td>
                <td></td>
            </tr>
            <tr>
                <td>port</td>
                <td><em>num</em></td>
                <td><u>tcp端口</u></td>
                <td></td>
            </tr>
            <tr>
                <td>wss_port</td>
                <td><em>num</em></td>
                <td><u>wss端口</u></td>
                <td></td>
            </tr>
            <tr>
                <td>ws_port</td>
                <td><em>num</em></td>
                <td><u>ws端口</u></td>
                <td></td>
            </tr>
            </tbody>
        </table>
        """
        request = requests.get(f'https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo?id={roomid}',
                               headers=self.headers).json()
        return request


class BiliLiveApiNeedCookie:
    """
    实例：B站直播Api_需要cookie的hearder
    """

    def __init__(self, headers: dict):
        """
        为实例配置一个有cookie的headers
        :param headers: 带有cookie的headers
        """
        self.headers = headers
        self.Danmu = self.__Danmu(self.headers, self.user__get_user_info)

    class __Danmu:
        def __init__(self, headers: dict, user__get_user_info: Callable[[], dict]):
            """

            :param headers:
            :param user__get_user_info: 用于获取普通模式弹幕所需要的参数 uid
            """
            self.headers = headers
            self.__user__get_user_info = user__get_user_info

        def Normal(self, roomid: int) -> '__Normal':
            Normal = self.__Normal(self.headers, roomid, self.websocket, self.__user__get_user_info)
            return Normal

        class __Normal:
            def __init__(self, headers: dict, roomid: int, websocket: type,
                         user__get_user_info: Callable[[], dict]):
                self.wss_url = None
                self.auth_body = None
                self.headers = headers
                self.roomid = roomid
                self.__websocket = websocket
                self.__user__get_user_info = user__get_user_info
                self.__BiliGeneralApi = BiliGeneralApi(headers)

            def websocket(self):
                self.wss_url, self.auth_body = self.__connect(self.roomid)
                websocket = self.__websocket(self.wss_url, self.auth_body)
                return websocket

            def __connect(self, roomid: int):
                """

                :param roomid: 需要连接弹幕的长房间号
                :return:
                """
                cookie = self.headers['cookie']
                DanmuInfo = self.__BiliGeneralApi.getDanmuInfo(roomid)
                key = DanmuInfo['data']['token']
                wss_url = f"wss://{DanmuInfo['data']['host_list'][-1]['host']}:{DanmuInfo['data']['host_list'][-1]['wss_port']}/sub"
                auth_body = {
                    "uid": self.__user__get_user_info()["uid"],
                    "roomid": roomid,
                    "protover": 2,
                    "buvid": cookieFormat2dict(cookie)['buvid3'],
                    "platform": "web",
                    "type": 3,
                    "key": key
                }
                auth_body = json.dumps(auth_body, ensure_ascii=False)
                return wss_url, auth_body

        class websocket:
            """
            使用websockets获取弹幕的实例
            """

            def __init__(self, url: str, auth_body: str):
                """
                鉴权协议认证
                :param auth_body:
                开放平台的在start_app函数的["data"]["websocket_info"]["auth_body"]<br>
                普通的格式为
                :param url:
                """
                self.url = url
                self.auth_body = auth_body

            __savedamudata = set()

            class Opt:
                HEARTBEAT = 2
                HEARTBEAT_REPLY = 3
                SEND_SMS_REPLY = 5
                AUTH = 7
                AUTH_REPLY = 8

            class Version:
                NORMAL = 0
                ZIP = 2

            async def on_open(self, websocket):
                print("已连接服务...")

                # 鉴权协议包
                auth_pack = self.generate_auth_pack(self.auth_body)
                # print(auth_pack)
                await websocket.send(auth_pack)

                # 每30秒发送心跳包
                async def send_heartbeat():
                    while True:
                        try:
                            heartbeat_pack = self.generate_heartbeat_pack()
                            await websocket.send(heartbeat_pack)
                        except Exception as e:
                            raise RuntimeError(e)
                        await asyncio.sleep(30)

                await asyncio.create_task(send_heartbeat())

            async def on_message(self, message):
                if isinstance(message, bytes):
                    # 解包
                    self.unpack(message)

            async def connect(self):
                async with websockets.connect(self.url) as websocket:
                    await self.on_open(websocket)
                    while True:
                        message = await websocket.recv()
                        # 处理接收到的消息
                        # print(f"接收到消息：{message}")
                        # async for message in websocket:
                        await self.on_message(message)

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
                if opt_code == self.Opt.AUTH_REPLY:
                    self.AuthenticationReply = content
                    print(f"这是鉴权回复：{self.AuthenticationReply}\n")
                elif opt_code == self.Opt.SEND_SMS_REPLY:
                    self.DanmuInfo = content
                    if content not in self.__savedamudata:
                        self.__savedamudata.add(content)
                        print(
                            f"真正的弹幕消息：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_{self.DanmuInfo}")
                    # print(content)

                if len(byte_buffer) > package_len:
                    self.unpack(byte_buffer[package_len:])

            async def main(self):
                tasks = [self.connect() for _ in range(45)]
                await asyncio.gather(*tasks)
                # await self.connect()

    def user__get_user_info(self) -> dict:
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


from .BiliBiliAPI_limited import start_login

cookie = start_login(3546559824267399)
print(cookie)
