# coding=utf-8
from tool import config_B, qr_encode, dict2cookieformat
from login import generate, poll
from special import master


def start_login(uid: int = 0):
    """
    扫码登陆获得cookies
    :param uid:
    :return:
    """
    configb = config_B(uid=uid, dirname="Biliconfig")
    cookies = configb.check()
    islogin = master(dict2cookieformat(cookies)).interface_nav()["isLogin"]
    if islogin:
        return dict2cookieformat(cookies)
    else:
        # 申请登录二维码
        url8qrcode_key = generate()
        url = url8qrcode_key['url']
        # 二维码
        qr = qr_encode(url)
        print(qr["str"])
        qrcode_key = url8qrcode_key['qrcode_key']
        code = poll(qrcode_key)['code']
        print(code)
        while True:
            code_ = code
            poll_ = poll(qrcode_key)
            code = poll_['code']
            if code_ != code:
                print(code)
            if code == 0 or code == 86038:
                cookies = poll_['cookies']
                break
    if uid == cookies['DedeUserID']:
        configb.update(cookies)
    else:
        uid = int(cookies['DedeUserID'])
        configb = config_B(uid=uid, dirname="Biliconfig")
        configb.update(cookies)
    return dict2cookieformat(cookies)


print(start_login())










