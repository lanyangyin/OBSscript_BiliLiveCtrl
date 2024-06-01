import asyncio
import datetime
import json
import zlib
from typing import Callable
from urllib.parse import unquote

import requests
import websockets

from BiliLiveCtrl_lua.BiliBiliAPI_limited import start_login


def html_url_decode(encoded_string: str) -> str:
    return unquote(encoded_string)


def cookie_format_to_dict(cookie_text: str) -> dict:
    cookie_dict = {}
    if cookie_text.endswith(';'):
        cookie_text = cookie_text[:-1]
    for item in cookie_text.split(';'):
        if '=' in item:
            key, value = map(html_url_decode, map(str.strip, item.split('=', 1)))
            cookie_dict[key] = value
    return cookie_dict


class BiliGeneralApi:
    def __init__(self, headers: dict):
        self.headers = headers

    def get_qrcode(self) -> dict:
        url = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate?&go_url=https://link.bilibili.com/'
        response = requests.get(url, headers=self.headers).json()
        if response.get('code') == 0:
            return response['data']
        print('Failed to get QR code')
        return {}

    def get_qrcode_status(self, qrcode_key: str) -> dict:
        url = f'https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={qrcode_key}'
        response = requests.get(url, headers=self.headers).json()
        if response.get('code') == 0:
            return response['data']
        print('Failed to get QR code status')
        return {}

    def get_buvid3(self) -> dict:
        response = requests.get('https://www.bilibili.com', headers=self.headers)
        return response.cookies.get_dict()

    def get_danmu_info(self, roomid: int) -> dict:
        url = f'https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo?id={roomid}'
        response = requests.get(url, headers=self.headers).json()
        return response


class BiliLiveApiNeedCookie:
    def __init__(self, headers: dict):
        self.headers = headers
        self.danmu = self.Danmu(headers, self.get_user_info)

    class Danmu:
        def __init__(self, headers: dict, get_user_info: Callable[[], dict]):
            self.headers = headers
            self.get_user_info = get_user_info

        class WebSocketClient:
            HEARTBEAT_INTERVAL = 30
            VERSION_NORMAL = 0
            VERSION_ZIP = 2

            def __init__(self, url: str, auth_body: dict):
                self.url = url
                self.auth_body = auth_body
                self.saved_danmudata = set()

            async def connect(self):
                async with websockets.connect(self.url) as ws:
                    await self.on_open(ws)
                    while True:
                        message = await ws.recv()
                        await self.on_message(message)

            async def on_open(self, ws):
                print("Connected to server...")
                await ws.send(self.pack(self.auth_body, 7))
                asyncio.create_task(self.send_heartbeat(ws))

            async def send_heartbeat(self, ws):
                while True:
                    await ws.send(self.pack(None, 2))
                    await asyncio.sleep(self.HEARTBEAT_INTERVAL)

            async def on_message(self, message):
                if isinstance(message, bytes):
                    self.unpack(message)

            def pack(self, content: dict, code: int) -> bytes:
                content_bytes = json.dumps(content).encode('utf-8') if content else b''
                header = (len(content_bytes) + 16).to_bytes(4, 'big') + \
                         (16).to_bytes(2, 'big') + \
                         self.VERSION_NORMAL.to_bytes(2, 'big') + \
                         code.to_bytes(4, 'big') + \
                         (1).to_bytes(4, 'big')
                return header + content_bytes

            def unpack(self, byte_buffer: bytes):
                package_len = int.from_bytes(byte_buffer[0:4], 'big')
                head_length = int.from_bytes(byte_buffer[4:6], 'big')
                prot_ver = int.from_bytes(byte_buffer[6:8], 'big')
                opt_code = int.from_bytes(byte_buffer[8:12], 'big')

                content_bytes = byte_buffer[16:package_len]
                if prot_ver == self.VERSION_ZIP:
                    content_bytes = zlib.decompress(content_bytes)
                    self.unpack(content_bytes)
                    return

                content = content_bytes.decode('utf-8')
                if opt_code == 8:  # AUTH_REPLY
                    print(f"Authentication Reply: {content}\n")
                elif opt_code == 5:  # SEND_SMS_REPLY
                    if content not in self.saved_danmudata:
                        self.saved_danmudata.add(content)
                        print(f"Danmu message at {datetime.datetime.now()}: {content}")

                if len(byte_buffer) > package_len:
                    self.unpack(byte_buffer[package_len:])

            async def main(self):
                await self.connect()

        def get_websocket_client(self, roomid: int):
            general_api = BiliGeneralApi(self.headers)
            danmu_info = general_api.get_danmu_info(roomid)
            token = danmu_info['data']['token']
            host = danmu_info['data']['host_list'][-1]
            wss_url = f"wss://{host['host']}:{host['wss_port']}/sub"

            user_info = self.get_user_info()
            cookie = cookie_format_to_dict(self.headers['cookie'])
            auth_body = {
                "uid": user_info["uid"],
                "roomid": roomid,
                "protover": 2,
                "buvid": cookie['buvid3'],
                "platform": "web",
                "type": 3,
                "key": token
            }
            return self.WebSocketClient(wss_url, auth_body)

    def get_user_info(self) -> dict:
        url = "https://api.live.bilibili.com/xlive/web-ucenter/user/get_user_info"
        response = requests.get(url, headers=self.headers).json()
        return response['data']


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'cookie': start_login(3546559824267399)
}
BAC = BiliLiveApiNeedCookie(headers)
dm_client = BAC.danmu.get_websocket_client(21756924)

asyncio.run(dm_client.main())
