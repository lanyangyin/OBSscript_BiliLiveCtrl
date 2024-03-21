import json
import os
import sys

# Python运行路径
import time

os.path.abspath('.')

# 当前脚本的路径
os.path.abspath(__file__)

# 当前脚本所在路径
os.path.dirname(os.path.abspath(__file__))

# 更改Python运行路径
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 添加设置 Python 的模块搜索路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

url = r'C:\Users\lanan\PycharmProjects\B播操作'
sys.path.append(url)
import BiliBili_api_limited
from BiliBili_api_limited import BiliGeneralApi
from BiliBili_api_limited import t2qr_str
from BiliBili_api_limited import BiliHomeApiNeedCookie
from BiliBili_api_limited import BiliLiveApiNeedCookie
from BiliBili_api_limited import BiliLiveApiNoCookie


def LuaTimerClose():
    """
    关闭Lua插件那边的timer
    :return:None
    """
    with open(os.path.dirname(os.path.abspath(__file__)) + '/BiliLiveCtrl_lua.temp', 'w', encoding='utf-8') as t:
        t.write('{【[{timerShowTempValue}AUTO]OFF】}')
    time.sleep(2)
    with open(os.path.dirname(os.path.abspath(__file__)) + '/BiliLiveCtrl_lua.temp', 'w', encoding='utf-8') as t:
        t.write('')


def writTempW(text: str):
    """
    向Temp文件覆盖写入内容
    :param text: 写入的内容
    :return: None
    """
    with open(os.path.dirname(os.path.abspath(__file__)) + '/BiliLiveCtrl_lua.temp', 'w', encoding='utf-8') as t:
        t.write(text)


def readTemp():
    """
    读取Temp文件内容
    :return: Temp文件内容
    """
    with open(os.path.dirname(os.path.abspath(__file__)) + '/BiliLiveCtrl_lua.temp', 'r', encoding='utf-8') as t:
        content = t.read()
    return content


def writDevicesW(text: str):
    """
    向devices文件覆盖写入内容
    :param text: 写入的内容
    :return: None
    """
    with open(os.path.dirname(os.path.abspath(__file__)) + '/devices.json', 'w', encoding='utf-8') as t:
        t.write(text)


def readDevices():
    """
    读取devices文件内容
    :return: Temp文件内容
    """
    with open(os.path.dirname(os.path.abspath(__file__)) + '/devices.json', 'r', encoding='utf-8') as t:
        content = t.read()
    return content


def firstinfo(headers):
    BiliHomeApiNeedCookieheaders = BiliHomeApiNeedCookie(headers)
    nav = BiliHomeApiNeedCookieheaders.nav()
    devices = {}
    setting = {}
    edit = {}
    if nav['isLogin']:
        BiliLiveCookieApi = BiliLiveApiNeedCookie(headers)
        BiliLiveApi = BiliLiveApiNoCookie(headers)
        cookie = headers['cookie']
        setting["cookie"] = cookie
        setting["uname"] = nav['uname']
        setting["uid"] = nav['mid']
        setting["room_id"] = BiliLiveCookieApi.audit__GetRoomInfo()
        Room__get_info = BiliLiveApi.Room__get_info(setting["room_id"])
        Master__info = BiliLiveApi.live_user__v1__Master__info(setting["uid"])
        # try:
        if setting["room_id"] != 0:
            edit['title'] = Room__get_info['title']
            edit['news'] = Master__info["room_news"]["content"]
            edit['tags'] = Room__get_info['tags']
            edit['live_status'] = Room__get_info['live_status']
            edit['live_time'] = Room__get_info['live_time']
            edit["Area_v1_id"] = Room__get_info['parent_area_id']
            edit["Area_v2_id"] = Room__get_info['area_id']
            AreaListData = BiliLiveApi.Area__getList()
            edit["area_v1"] = BiliBili_api_limited.Area_v1_List2json(AreaListData)
            edit["area_v2"] = BiliBili_api_limited.Area_v2_List2json(AreaListData)
            devices_area_id = {}
            for areadict in BiliBili_api_limited.AreaList2List(AreaListData):
                devices_area_id[areadict['id']] = areadict['parent_id']
            edit["area_id"] = devices_area_id
        # finally:
        else:
            AreaListData = BiliLiveApi.Area__getList()
            edit["area_v1"] = BiliBili_api_limited.Area_v1_List2json(AreaListData)
            edit["area_v2"] = BiliBili_api_limited.Area_v2_List2json(AreaListData)
            devices_area_id = {}
            for areadict in BiliBili_api_limited.AreaList2List(AreaListData):
                devices_area_id[areadict['id']] = areadict['parent_id']
            edit["area_id"] = devices_area_id
        devices['setting'] = setting
        devices['edit'] = edit
        # print(devices)
    return devices['setting'], devices['edit'], devices['edit']["area_v1"], devices['edit']["area_v2"], devices['edit']["area_id"]


with open(os.path.dirname(os.path.abspath(__file__)) + '/BiliLiveCtrl_lua.temp', 'r', encoding='utf-8') as t:
    order = t.read()
    try:
        model = json.loads(order)['model']
    except:
        model = ''

# model = 'updatacookie'
if model == 'updatacookie':
    # cookie = "json.loads(order)['cookie']"
    cookie = json.loads(order)['cookie']
    UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 ' \
         'Safari/537.36 '
    headers = {'origin': 'https://link.bilibili.com', 'referer': 'https://link.bilibili.com/p/center/index',
               'user-agent': UA, "cookie": cookie}
    BiliHomeApiNeedCookieheaders = BiliHomeApiNeedCookie(headers)
    nav = BiliHomeApiNeedCookieheaders.nav()
    if nav['isLogin']:
        devices = firstinfo(headers)
    else:
        with open(os.path.dirname(os.path.abspath(__file__)) + '/devices.json', 'w', encoding='utf-8') as t:
            t.write("")
        BiliGeneralApi = BiliGeneralApi(headers)
        __qrcode__generate = BiliGeneralApi.passport_login__web__qrcode__generate()
        qrcode_key = __qrcode__generate['qrcode_key']
        QR = t2qr_str(__qrcode__generate['url'])
        with open(os.path.dirname(os.path.abspath(__file__)) + '/BiliLiveCtrl_lua.temp', 'w', encoding='utf-8') as t:
            iTxt = ''
            for i in QR.split('\n'):
                itxt = BiliBili_api_limited.unicode_to_chinese(BiliBili_api_limited.chinese_to_unicode(i)) + '\n'
                iTxt += itxt
            t.write(iTxt)
        poll_code = 1
        is_code = ''
        time.sleep(1)
        while poll_code != 0:
            time.sleep(1)
            poll = BiliGeneralApi.passport_login__web__qrcode__poll(qrcode_key)
            poll_code = poll['code']
            message = ''
            if poll_code == 86101 and poll_code != is_code:
                is_code = 86101
                message = poll['message']
            elif poll_code == 86090 and poll_code != is_code:
                is_code = 86090
                message = poll['message']
            elif poll_code == 86038:
                message = poll['message']
                poll_code = 0
            elif poll_code == 0:
                message = "登陆成功"
            try:
                with open(os.path.dirname(os.path.abspath(__file__)) + '/BiliLiveCtrl_lua.temp', 'w',
                          encoding='utf-8') as t:
                    t.write(message)
            finally:
                if poll_code == 0:
                    cookie = BiliBili_api_limited.loginQrcodePollUrl2cookieFormat(poll['url'])
                    headers['cookie'] = cookie
                    cookie_dict = BiliBili_api_limited.cookieFormat2dict(cookie)
                    cookie_dict.update(BiliGeneralApi.getBili_withBuvid3())
                    cookie = BiliBili_api_limited.dict2cookieFormat(cookie_dict)
                    headers['cookie'] = cookie
                    devices = firstinfo(headers)
    with open(os.path.dirname(os.path.abspath(__file__)) + '/BiliLiveCtrl_lua.temp', 'w',
              encoding='utf-8') as t:
        t.write('')
    with open(os.path.dirname(os.path.abspath(__file__)) + '/devices.json', 'w', encoding='utf-8') as t:
        l1, l2, l3, l4, l5 = devices
        t.write(json.dumps(l1, ensure_ascii=False) + "\n")
        t.write(json.dumps(l2, ensure_ascii=False) + "\n")
        t.write(json.dumps(l3, ensure_ascii=False) + "\n")
        t.write(json.dumps(l4, ensure_ascii=False) + "\n")
        t.write(json.dumps(l5, ensure_ascii=False) + "\n")

if model == 'getuname':
    UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    headers = {
        'origin': 'https://link.bilibili.com',
        'referer': 'https://link.bilibili.com/p/center/index',
        'user-agent': UA,
    }
    try:
        with open(os.path.dirname(os.path.abspath(__file__)) + '/devices.json', 'r', encoding='utf-8') as t:
            devices = t.readline()
            headers["cookie"] = json.loads(devices)["setting"]['cookie']
    finally:
        devices = firstinfo(headers)
        with open(os.path.dirname(os.path.abspath(__file__)) + '/devices.json', 'w',
                  encoding='utf-8') as t:
            t.write(json.dumps(devices, ensure_ascii=False))

if model == 'get_uname':
    print()
