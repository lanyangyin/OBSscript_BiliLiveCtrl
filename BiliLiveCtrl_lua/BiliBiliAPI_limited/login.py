# coding=utf-8
# 只能二维码登录
import json
import os
import re
import time
from typing import Dict, Any

import requests

from tool import urldata_dict

debug = False
debug_num = 0
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
    (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
}


def generate() -> dict:
    """
    申请登录二维码
    @return: {'url': 二维码文本, 'qrcode_key': 扫描秘钥}
    """
    api = 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate'
    url8qrcode_key = requests.get(api, headers=headers).json()
    # print(url8qrcode_key)
    data = url8qrcode_key['data']
    url = data['url']
    qrcode_key = data['qrcode_key']
    return {'url': url, 'qrcode_key': qrcode_key}


# print(generate())


def poll(qrcode_key: str) -> dict[str, dict[str, str] | int]:
    """
    获取登陆状态，登陆成功获取 基础的 cookies
    @param qrcode_key: 扫描秘钥
    @return: {'code', 'cookies'}
    <table>
        <thead>
        <tr>
            <th>字段</th>
            <th>类型</th>
            <th>内容</th>
            <th>备注</th>
        </tr>
        </thead>
        <tbody>
        <tr>
            <td>code</td>
            <td>num</td>
            <td>0：扫码登录成功<br>86038：二维码已失效<br>86090：二维码已扫码未确认<br>86101：未扫码</td>
            <td></td>
        </tr>
        </tbody>
    </table>
    @rtype: dict
    """
    global data
    api = f'https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={qrcode_key}'
    DedeUserID8DedeUserID__ckMd58SESSDATA8bili_jct = requests.get(api, data=qrcode_key, headers=headers).json()
    data = DedeUserID8DedeUserID__ckMd58SESSDATA8bili_jct['data']
    # print(data)
    cookies = {}
    code = data['code']
    if code == 0:
        data_dict = urldata_dict(data['url'])
        cookies["DedeUserID"] = data_dict['DedeUserID']
        cookies["DedeUserID__ckMd5"] = data_dict['DedeUserID__ckMd5']
        cookies["SESSDATA"] = data_dict['SESSDATA']
        cookies["csrf"] = data_dict['bili_jct']
        # 补充 cookie
        response = requests.get(f'https://www.bilibili.com/video/', headers=headers)
        cookies.update(response.cookies.get_dict())
    return {'code': code, 'cookies': cookies}


# print(poll(""))


def get_buvid3(bvid: str = 'BV16F411c7CR') -> dict:
    """
    通过视频BV号获取cookie部分参数
    :param bvid: BV号
    :return:  {'cookies': cookies, 'data_dict': data_dict, 'session': sessionId}
    """
    response = requests.get(f'https://www.bilibili.com/video/{bvid}/', headers=headers)
    cookies = response.cookies.get_dict()
    data_list = re.findall(r'__INITIAL_STATE__=(.+);\(function', response.text)  # .表示除换行符所有字符，+ 表示一个或者多个
    try:
        data_dict = json.loads(data_list[0])  # 结果长得像字典， 就用python中反序列化转成json格式
        sessionId = re.findall(r'session":"(.+)"}</script', response.text)[0]
    except:
        data_dict = ''
        sessionId = ''
    return {'cookies': cookies, 'data_dict': data_dict, 'session': sessionId}

# print_debug(get_buvid3())
