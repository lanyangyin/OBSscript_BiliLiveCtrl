import asyncio
import datetime
import hashlib
import hmac
import json
import random
import sys
import time
import zlib
from io import StringIO
from typing import Callable
from urllib.parse import quote
from urllib.parse import unquote

import qrcode
import requests
import websockets
from aiohttp import ClientSession, WSMsgType


def UnixTime2UtcTime(timestamp: int):
    """
    Unix时间戳转成UTC（协调世界时）
    :param timestamp:
    :return:UTC（协调世界时）
    """
    # 使用datetime.fromtimestamp()方法将时间戳转换成datetime对象
    converted_time = datetime.datetime.fromtimestamp(timestamp)
    # 将转换后的datetime对象格式化为字符串
    formatted_time = converted_time.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time


def html_url_decode(encoded_string: str) -> str:
    """
    # 使用 unquote 函数进行 HTML URL 解码
    :param encoded_string:
    :return:HTML URL 解码后 的字符串
    """
    decoded_string = unquote(encoded_string)
    return decoded_string


def html_url_encode(input_string: str) -> str:
    """
    # 使用 quote 函数进行 HTML URL 编码
    :param input_string:
    :return:HTML URL 编码后 的字符串
    """
    encoded_string = quote(input_string)
    return encoded_string


def Payload2HtmlUrlCode(input_dict: dict) -> str:
    """
    # 将网络负载data进行 HTML URL 格式编码
    :param input_dict:
    :return:将网络负载 进行HTML URL编码后 的字符串
    """
    HtmlUrlCode = ''
    for i in input_dict.keys():
        if i != list(input_dict.keys())[-1]:
            if type(input_dict[str(i)]) == dict:
                HtmlUrlCode += f"{html_url_encode(str(i).replace(' ', ''))}={html_url_encode(json.dumps(input_dict[str(i)], ensure_ascii=False).replace(' ', ''))}&"
            else:
                HtmlUrlCode += f"{html_url_encode(str(i).replace(' ', ''))}={html_url_encode(str(input_dict[str(i)]).replace(' ', ''))}&"
        else:
            if type(input_dict[str(i)]) == dict:
                HtmlUrlCode += f"{html_url_encode(str(i).replace(' ', ''))}={html_url_encode(json.dumps(input_dict[str(i)], ensure_ascii=False).replace(' ', ''))}"
            else:
                HtmlUrlCode += f"{html_url_encode(str(i).replace(' ', ''))}={html_url_encode(str(input_dict[str(i)]).replace(' ', ''))}"
    return HtmlUrlCode


def t2qr_str(text: str, border: int = 1, invert: bool = False) -> str:
    """
    将文本转换成二维码字符串
    :param text: 二维码的内容
    :param border: 二维码边缘宽度
    :param invert: False时背景为黑，True时背景为白
    :return:二维码字符串
    """
    qr = qrcode.QRCode()
    qr.border = border
    qr.add_data(text)
    qr.make()
    # 创建一个 StringIO 对象来捕获输出
    qr_text_buffer = StringIO()
    # 保存原始的标准输出
    original_stdout = sys.stdout
    try:
        # 将输出重定向到 StringIO
        sys.stdout = qr_text_buffer
        # 调用 print_ascii 方法
        qr.print_ascii(out=None, tty=False, invert=invert)
        # 获取输出文本
        qr_text = qr_text_buffer.getvalue()
    finally:
        # 恢复原始的标准输出
        sys.stdout = original_stdout
    return qr_text


def loginQrcodePollUrl2cookieFormat(url: str) -> str:
    """
    将扫描二维码登录获得带有cookie的 游戏分站跨域登录 url 中的cookie提取出来格式化
    :param url: 游戏分站跨域登录 url,    url格式为：<br>https://passport.biligame.com/x/passport-login/web/crossDomain?DedeUserID=int(B站UID)&DedeUserID__ckMd5=（str）&Expires=（int）&SESSDATA=（str）&gourl=登录跳转链接
    :return: DedeUserID=int(B站UID); DedeUserID__ckMd5=（str）; Expires=int; SESSDATA=（str）; bili_jct= str(csrf); gourl=登录跳转链接
    """
    cookie = str(url).split('?')[1].replace('&', '; ')
    return cookie


def chinese_to_unicode(s: str) -> str:
    """
    输出为  Unicode 转义序列
    :param s:
    :return:
    """
    return ''.join(['U{:04x}'.format(ord(c)) for c in s])


def unicode_to_chinese(s: str) -> str:
    """
    # 将Unicode编码转换为可读文本
    :param s: 格式为U00a0U00a0U00a0U00a0U00a0U00a0U00a0U00a0
    :return:str
    """
    decoded_text = ""
    for char in s.split("U"):
        try:
            decoded_text += chr(int(char, 16))
        except ValueError:
            decoded_text += char
    return decoded_text


def is_CookieName_format(s: str) -> bool:
    """
    判断字符串是否满足cookie-name的格式<br>
    cookie-name可以包含除了控制字符（ASCII 字符 0 至 31，以及 ASCII 字符 127）和分隔符（空格、制表符和以下字符：( ) < > @ , ; : \ " / [ ] ? = { }）之外的任何 US-ASCII 字符。
    编码：许多实现会对 cookie 值进行 URL 编码。但是按照 RFC 规范，这不是必须的。不过 URL 编码有助于满足 <cookie-value> 对允许使用的字符的要求。
    :param s:
    :return:
    """
    for char in s:
        # 判断字符是否为控制字符或分隔符
        try:
            if ord(char) <= 31 or ord(char) == 127 or char in ' \t()<>@,;:\\\"/[]?={}':
                print('出错字符：', char)
                return False
        except:
            return False
    return True


def is_CookieValue_format(s: str) -> bool:
    """
    判断字符串是否满足cookie-value的格式<br>
    cookie-value可以选择包裹在双引号中。支持除了控制字符（ASCII 字符 0 至 31，以及 ASCII 字符 127）、空白字符、双引号、逗号、分号以及反斜杠之外的任意 US-ASCII 字符。
    编码：许多实现会对 cookie 值进行 URL 编码。但是按照 RFC 规范，这不是必须的。不过 URL 编码有助于满足 <cookie-value> 对允许使用的字符的要求。
    :param s:
    :return:
    """
    if s.startswith('\"') and s.endswith('\"'):
        s = s.split('\"', 1)[1].split('\"', -1)[0]
    for char in s:
        try:
            # 判断字符是否为控制字符、空白字符、双引号、逗号、分号或反斜杠
            if ord(char) <= 31 or ord(char) == 127 or char.isspace() or char in ',"\';\\':
                print('出错字符：', char)
                return False
        except:
            return False
    return True


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


def dict2cookieFormat(dict_: dict) -> str:
    """
    将字典类型转换成cookice格式的文本
    cookie-name可以包含除了控制字符（ASCII 字符 0 至 31，以及 ASCII 字符 127）和分隔符（空格、制表符和以下字符：( ) < > @ , ; : \ " / [ ] ? = { }）之外的任何 US-ASCII 字符。
    cookie-value可以选择包裹在双引号中。支持除了控制字符（ASCII 字符 0 至 31，以及 ASCII 字符 127）、空白字符、双引号、逗号、分号以及反斜杠之外的任意 US-ASCII 字符。
    编码：许多实现会对 cookie 值进行 URL 编码。但是按照 RFC 规范，这不是必须的。不过 URL 编码有助于满足 <cookie-value> 对允许使用的字符的要求。
    :param dict_:需要为字典类型的参数
    :return:
    """
    cookieFormat_text = ''
    cookieFormat_is = True
    if cookieFormat_is:
        for i in dict_.keys():
            if i != list(dict_.keys())[-1]:
                if type(dict_[i]) == dict:
                    cookieFormat_text += f'{html_url_encode(str(i))}={html_url_encode(json.dumps(dict_[i], ensure_ascii=False).replace("", ""))}; '
                else:
                    cookieFormat_text += f'{html_url_encode(str(i))}={html_url_encode(str(dict_[i]).strip())}; '
            else:
                if type(dict_[i]) == dict:
                    cookieFormat_text += f'{html_url_encode(str(i))}={html_url_encode(json.dumps(dict_[i], ensure_ascii=False).replace("", ""))}'
                else:
                    cookieFormat_text += f'{html_url_encode(str(i))}={html_url_encode(str(dict_[i]).strip())}'
    return cookieFormat_text


def Area_v1_List2json(AreaListData: list) -> dict:
    """
    从 Arealist的原始列表 中 提出一级分区名称和数字号码
    :param AreaListData: Arealist的原始列表, 由getAreaList()获得
    :return: {Area_v1_name: Area_v1_id（int）, ......}
    """
    Area_v1_json = {}
    for AreaListData_E in AreaListData:
        Area_v1_json[AreaListData_E["name"]] = AreaListData_E["id"]
    return Area_v1_json


def Area_v2_List2json(AreaListData: list, Area_v1_name: str = '', Area_v1_id: int = 0) -> dict:
    """
    从 Arealist的原始列表 中 提出与Area_v1_name或Area_v1_id（int）对应的二级分区名称和号码
    若没有，则提出所有二级分区名称和号码
    :param AreaListData: Arealist的原始列表, 由getAreaList()获得
    :param Area_v1_name: 一级分区名称
    :param Area_v1_id: 一级分区数字号码
    :return: {Area_v2_name: Area_v2_id（str）, ......}
    """
    Area_v2_json = {}
    for AreaListData_E in AreaListData:
        Area_v2_List = AreaListData_E['list']
        if Area_v1_name != '':
            if Area_v1_name == AreaListData_E["name"]:
                for Area_v2_List_E in Area_v2_List:
                    Area_v2_json[Area_v2_List_E["name"]] = Area_v2_List_E["id"]
        elif Area_v1_id != 0:
            if Area_v1_id == AreaListData_E["id"]:
                for Area_v2_List_E in Area_v2_List:
                    Area_v2_json[Area_v2_List_E["name"]] = Area_v2_List_E["id"]
        else:
            for Area_v2_List_E in Area_v2_List:
                Area_v2_json[Area_v2_List_E["name"]] = Area_v2_List_E["id"]
    return Area_v2_json


def AreaList2List(AreaListData: list) -> list:
    """
    从 Arealist的原始列表 中 提出分区名称和号码 列表
    :param AreaListData: Arealist的原始列表, 由getAreaList()获得
    :return: <pre>[<br>&#32;&#32;{<br>&#32;&#32;&#32;&#32;'id':&#32;二级分区号码,<br>&#32;&#32;&#32;&#32;'parent_id':&#32;一级分区号码,<br>&#32;&#32;&#32;&#32;'old_area_id':&#32;旧分区号码,<br>&#32;&#32;&#32;&#32;'name':&#32;二级分区名称,<br>&#32;&#32;&#32;&#32;'act_id':&#32;'0',<br>&#32;&#32;&#32;&#32;'pk_status':&#32;'1',<br>&#32;&#32;&#32;&#32;'hot_status':&#32;0,<br>&#32;&#32;&#32;&#32;'lock_status':&#32;'0',<br>&#32;&#32;&#32;&#32;'pic':&#32;分区标识图像url,<br>&#32;&#32;&#32;&#32;'complex_area_name':&#32;'',<br>&#32;&#32;&#32;&#32;'parent_name':&#32;一级分区名称,<br>&#32;&#32;&#32;&#32;'area_type':&#32;0<br>&#32;&#32;},<br>&#32;&#32;......<br>]</pre>
    """
    AreaList = []
    for AreaListData_E in AreaListData:
        Area_v2_List = AreaListData_E["list"]
        for Area_v2_List_E in Area_v2_List:
            AreaList.append(Area_v2_List_E)
    return AreaList


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
        :param url: B站主站url：如<a href='https://www.bilibili.com'>https://www.bilibili.com</a>
        :param __headers:
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


class BiliHomeApiNeedCookie:
    """
    实例：B站主站api_需要cookie
    """

    def __init__(self, headers: dict):
        """
        为实例配置一个有cookie的headers
        :param headers: 带有cookie的headers
        """
        self.headers = headers

    def nav(self) -> dict:
        """
        B站导航栏用户信息

        :return:
        <table>
            <tbody>
            <tr>
                <td>isLogin</td>
                <td><em>bool</em></td>
                <td>是否已登录</td>
                <td>false：未登录<br>true：已登录</td>
            </tr>
            <tr>
                <td>email_verified</td>
                <td><em>num</em></td>
                <td>是否验证邮箱地址</td>
                <td>0：未验证<br>1：已验证</td>
            </tr>
            <tr>
                <td>face</td>
                <td><em>str</em></td>
                <td>用户头像 url</td>
                <td></td>
            </tr>
            <tr>
                <td><strong>[&quot;level_info&quot;]</strong></td>
                <td><em>obj</em></td>
                <td>等级信息</td>
                <td></td>
            </tr>
            <tr>
                <td>mid</td>
                <td><em>num</em></td>
                <td>用户 mid</td>
                <td></td>
            </tr>
            <tr>
                <td>mobile_verified</td>
                <td><em>num</em></td>
                <td>是否验证手机号</td>
                <td>0：未验证<br>1：已验证</td>
            </tr>
            <tr>
                <td>money</td>
                <td><em>num</em></td>
                <td>拥有硬币数</td>
                <td></td>
            </tr>
            <tr>
                <td>moral</td>
                <td><em>num</em></td>
                <td>当前节操值</td>
                <td>上限为70</td>
            </tr>
            <tr>
                <td><strong>[&quot;official&quot;]</strong></td>
                <td><em>obj</em></td>
                <td>认证信息</td>
                <td></td>
            </tr>
            <tr>
                <td><strong>[&quot;officialVerify&quot;]</strong></td>
                <td><em>obj</em></td>
                <td>认证信息 2</td>
                <td></td>
            </tr>
            <tr>
                <td><strong>[&quot;pendant&quot;]</strong></td>
                <td><em>obj</em></td>
                <td>头像框信息</td>
                <td></td>
            </tr>
            <tr>
                <td>scores</td>
                <td><em>num</em></td>
                <td>（？）</td>
                <td></td>
            </tr>
            <tr>
                <td>uname</td>
                <td><em>str</em></td>
                <td>用户昵称</td>
                <td></td>
            </tr>
            <tr>
                <td>vipDueDate</td>
                <td><em>num</em></td>
                <td>会员到期时间</td>
                <td>毫秒 时间戳</td>
            </tr>
            <tr>
                <td>vipStatus</td>
                <td><em>num</em></td>
                <td>会员开通状态</td>
                <td>0：无<br>1：有</td>
            </tr>
            <tr>
                <td>vipType</td>
                <td><em>num</em></td>
                <td>会员类型</td>
                <td>0：无<br>1：月度大会员<br>2：年度及以上大会员</td>
            </tr>
            <tr>
                <td>vip_pay_type</td>
                <td><em>num</em></td>
                <td>会员开通状态</td>
                <td>0：无<br>1：有</td>
            </tr>
            <tr>
                <td>vip_theme_type</td>
                <td><em>num</em></td>
                <td>（？）</td>
                <td></td>
            </tr>
            <tr>
                <td><strong>[&quot;vip_label&quot;]</strong></td>
                <td><em>obj</em></td>
                <td>会员标签</td>
                <td></td>
            </tr>
            <tr>
                <td>vip_avatar_subscript</td>
                <td><em>num</em></td>
                <td>是否显示会员图标</td>
                <td>0：不显示<br>1：显示</td>
            </tr>
            <tr>
                <td>vip_nickname_color</td>
                <td><em>str</em></td>
                <td>会员昵称颜色</td>
                <td>颜色码</td>
            </tr>
            <tr>
                <td><strong>[&quot;wallet&quot;]</strong></td>
                <td><em>obj</em></td>
                <td>B币钱包信息</td>
                <td></td>
            </tr>
            <tr>
                <td>has_shop</td>
                <td><em>bool</em></td>
                <td>是否拥有推广商品</td>
                <td>false：无<br>true：有</td>
            </tr>
            <tr>
                <td>shop_url</td>
                <td><em>str</em></td>
                <td>商品推广页面 url</td>
                <td></td>
            </tr>
            <tr>
                <td>allowance_count</td>
                <td><em>num</em></td>
                <td>（？）</td>
                <td></td>
            </tr>
            <tr>
                <td>answer_status</td>
                <td><em>num</em></td>
                <td>（？）</td>
                <td></td>
            </tr>
            <tr>
                <td>is_senior_member</td>
                <td><em>num</em></td>
                <td>是否硬核会员</td>
                <td>0：非硬核会员<br>1：硬核会员</td>
            </tr>
            <tr>
                <td><strong>[&quot;wbi_img&quot;]</strong></td>
                <td><em>obj</em></td>
                <td>Wbi 签名实时口令</td>
                <td><span style="color: blue; ">该字段即使用户未登录也存在</span></td>
            </tr>
            <tr>
                <td>is_jury</td>
                <td><em>bool</em></td>
                <td>是否风纪委员</td>
                <td>true：风纪委员<br>false：非风纪委员</td>
            </tr>
            </tbody>
        </table><br>
        <p><span style="color: green; "><code><strong>[&quot;level_info&quot;]</strong></code></span></p>
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
                <td>current_level</td>
                <td><em>num</em></td>
                <td><u>当前等级</u></td>
                <td></td>
            </tr>
            <tr>
                <td>current_min</td>
                <td><em>num</em></td>
                <td><u>当前等级经验最低值</u></td>
                <td></td>
            </tr>
            <tr>
                <td>current_exp</td>
                <td><em>num</em></td>
                <td><u>当前经验</u></td>
                <td></td>
            </tr>
            <tr>
                <td>next_exp</td>
                <td><em><span style="color: blue">小于6级时：num<br>6级时：str</span></em></td>
                <td><u>升级下一等级需达到的经验</u></td>
                <td><span style="color: green">当用户等级为Lv6时，值为<code>--</code>，代表无穷大</span></td>
            </tr>
            </tbody>
        </table><br>
        <p><span style="color: green; "><code><strong>[&quot;official&quot;]</strong></code></span></p>
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
                <td>role</td>
                <td><em>num</em></td>
                <td><u>认证类型</u></td>
                <td>
                    <table>
                        <thead>
                        <tr>
                            <th>ID</th>
                            <th>认证类型</th>
                            <th>详细类型</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr>
                            <td>0</td>
                            <td>无</td>
                            <td></td>
                        </tr>
                        <tr>
                            <td>1</td>
                            <td>个人认证</td>
                            <td>知名UP主</td>
                        </tr>
                        <tr>
                            <td>2</td>
                            <td>个人认证</td>
                            <td>大V达人</td>
                        </tr>
                        <tr>
                            <td>3</td>
                            <td>机构认证</td>
                            <td>企业</td>
                        </tr>
                        <tr>
                            <td>4</td>
                            <td>机构认证</td>
                            <td>组织</td>
                        </tr>
                        <tr>
                            <td>5</td>
                            <td>机构认证</td>
                            <td>媒体</td>
                        </tr>
                        <tr>
                            <td>6</td>
                            <td>机构认证</td>
                            <td>政府</td>
                        </tr>
                        <tr>
                            <td>7</td>
                            <td>个人认证</td>
                            <td>高能主播</td>
                        </tr>
                        <tr>
                            <td>9</td>
                            <td>个人认证</td>
                            <td>社会知名人士</td>
                        </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
            <tr>
                <td>title</td>
                <td><em>str</em></td>
                <td><u>认证信息</u></td>
                <td>无为空</td>
            </tr>
            <tr>
                <td>desc</td>
                <td><em>str</em></td>
                <td><u>认证备注</u></td>
                <td>无为空</td>
            </tr>
            <tr>
                <td>type</td>
                <td><em>num</em></td>
                <td><u>是否认证</u></td>
                <td>-1：无<br>0：认证</td>
            </tr>
            </tbody>
        </table><br>
        <p><span style="color: green; "><code><strong>[&quot;official_verify&quot;]</strong></code></span></p>
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
                <td>type</td>
                <td>num</td>
                <td>是否认证</td>
                <td>-1：无<br>0：认证</td>
            </tr>
            <tr>
                <td>desc</td>
                <td>str</td>
                <td>认证信息</td>
                <td>无为空</td>
            </tr>
            </tbody>
        </table><br>
        <p><span style="color: green; "><code><strong>[&quot;pendant&quot;]</strong></code></span></p>
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
                <td>pid</td>
                <td>num</td>
                <td>挂件id</td>
                <td></td>
            </tr>
            <tr>
                <td>name</td>
                <td>str</td>
                <td>挂件名称</td>
                <td></td>
            </tr>
            <tr>
                <td>image</td>
                <td>str</td>
                <td>挂件图片url</td>
                <td></td>
            </tr>
            <tr>
                <td>expire</td>
                <td>num</td>
                <td>（？）</td>
                <td></td>
            </tr>
            </tbody>
        </table>
        <p><span style="color: green; "><code><strong>[&quot;vip_label&quot;]</strong></code></span></p>
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
                <td>path</td>
                <td>str</td>
                <td>（？）</td>
                <td></td>
            </tr>
            <tr>
                <td>text</td>
                <td>str</td>
                <td>会员名称</td>
                <td></td>
            </tr>
            <tr>
                <td>label_theme</td>
                <td>str</td>
                <td>会员标签</td>
                <td>vip：大会员<br>annual_vip：年度大会员<br>ten_annual_vip：十年大会员<br>hundred_annual_vip：百年大会员</td>
            </tr>
            </tbody>
        </table><br>
        <p><span style="color: green; "><code><strong>[&quot;wallet&quot;]</strong></code></span></p>
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
                <td>mid</td>
                <td>num</td>
                <td>登录用户mid</td>
                <td></td>
            </tr>
            <tr>
                <td>bcoin_balance</td>
                <td>num</td>
                <td>拥有B币数</td>
                <td></td>
            </tr>
            <tr>
                <td>coupon_balance</td>
                <td>num</td>
                <td>每月奖励B币数</td>
                <td></td>
            </tr>
            <tr>
                <td>coupon_due_time</td>
                <td>num</td>
                <td>（？）</td>
                <td></td>
            </tr>
            </tbody>
        </table><br>
        <p><span style="color: green; "><code><strong>[&quot;wbi_img&quot;]</strong></code></span></p>
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
                <td>img_url</td>
                <td>str</td>
                <td>Wbi 签名参数 <code>imgKey</code>的伪装 url</td>
                <td>详见文档 <a href="./wbi.html" class="">Wbi 签名</a></td>
            </tr>
            <tr>
                <td>sub_url</td>
                <td>str</td>
                <td>Wbi 签名参数 <code>subKey</code>的伪装 url</td>
                <td>详见文档 <a href="./wbi.html" class="">Wbi 签名</a></td>
            </tr>
            </tbody>
        </table>
        """
        url = f'https://api.bilibili.com/x/web-interface/nav'
        nav_data = {}
        try:
            request = requests.get(url, headers=self.headers).json()
            nav_data = request['data']
            nav_data['错误日志'] = f'0'
        except Exception as r:
            nav_data['错误日志'] = f'请检查网络，{r}'
        return nav_data


class BiliLiveApiNoCookie:
    """
    实例：B站直播Api_不需要cookie
    """

    def __init__(self, headers: dict):
        """
        为实例配置一个普通的headers
        :param headers:普通的headers
        """
        self.headers = headers

    def getRoomBaseInfo(self, room_id: int = 0, uid: int = 0) -> dict:
        """
        获取直播间基础信息
        get_url：https://api.live.bilibili.com/xlive/web-room/v1/index/getRoomBaseInfo?room_ids=&uids=&req_biz=link-center
        :param uid: 直播间房主的uid（旧，大部分uid不能用）
        :param room_id: 直播间房间号，尽量用直播间房间真实（长）号，优先使用roomid
        :return:
        <table>
            <tbody>
                <tr><td>room_id</td><td>: 直播间房间真实（长）号【int】</td><td></td></tr>
                <tr><td>uid</td><td>: 直播间房主的uid【int】</td><td></td></tr>
                <tr><td>area_id</td><td>: 二级分区号【int】</td><td></td></tr>
                <tr><td>live_status</td><td>: 直播状态【int】</td><td>0未播<br>1直播<br>2轮播</td></tr>
                <tr><td>live_url</td><td>: 直播间url【str】</td><td></td></tr>
                <tr><td>parent_area_id</td><td>: 一级分区号【int】</td><td></td></tr>
                <tr><td>title</td><td>: 直播间标题【str】</td><td></td></tr>
                <tr><td>parent_area_name</td><td>: 一级分区名称【str】</td><td></td></tr>
                <tr><td>area_name</td><td>: 二级分区名称【str】</td><td></td></tr>
                <tr><td>live_time</td><td>: 直播开始时间【str】</td><td>YYYY-MM-DD HH:mm:ss</td></tr>
                <tr><td>description</td><td>: 直播间内个人简介【str】</td><td></td></tr>
                <tr><td>tags</td><td>: 标签【str】</td><td>格式为使用 “,” 分隔</td></tr>
                <tr><td>attention</td><td>: 关注数量【int】</td><td></td></tr>
                <tr><td>online</td><td>: 观看人数【int】</td><td></td></tr>
                <tr><td>short_id</td><td>: 直播间短房间号【int】</td><td></td></tr>
                <tr><td>uname</td><td>: B站昵称【str】</td><td></td></tr>
                <tr><td>cover</td><td>: 直播间封面图url【str】</td><td></td></tr>
                <tr><td>background</td><td>: 直播间背景图url【str】</td><td></td></tr>
                <tr><td>join_slide</td><td>: 未知【int】</td><td></td></tr>
                <tr><td>live_id</td><td>: 未知【int】</td><td></td></tr>
                <tr><td>live_id_str</td><td>: live_id的str格式【str】</td><td></td></tr>
                <tr><td>错误日志</td><td>: 0/警告信息/错误信息【str】 </td><td></td></tr>
            </tbody>
        </table>
        """
        info = {}
        try:
            if room_id != 0:
                url = f'https://api.live.bilibili.com/xlive/web-room/v1/index/getRoomBaseInfo?room_ids={room_id}&req_biz=link-center'
            else:
                url = f'https://api.live.bilibili.com/xlive/web-room/v1/index/getRoomBaseInfo?uids={uid}&req_biz=link-center'
            if room_id == 0 and uid == 0:
                print(f'错误_请输入 直播间真实号 或者 老直播间房主uid')
            else:
                request = requests.get(url, headers=self.headers).json()
                getRoomBaseInfo_data = request['data']
                if room_id != 0:
                    getRoomBaseInfo_ = getRoomBaseInfo_data["by_room_ids"]
                else:
                    getRoomBaseInfo_ = getRoomBaseInfo_data["by_uids"]
                if getRoomBaseInfo_ != {}:
                    try:
                        if room_id != 0:
                            info = getRoomBaseInfo_[str(room_id)]
                        elif uid != 0:
                            info = getRoomBaseInfo_[str(uid)]
                    except Exception as r:
                        try:
                            if room_id != 0:
                                for i in getRoomBaseInfo_.keys():
                                    room_id = i
                                info = getRoomBaseInfo_[str(room_id)]
                                print(f'警告_直播间房间号应该为{room_id},{r}')
                            elif uid != 0:
                                for i in getRoomBaseInfo_.keys():
                                    uid = i
                                info = getRoomBaseInfo_[str(uid)]
                                print(f'警告_直播间房主号应该为{uid},{r}')
                        except Exception as r:
                            if room_id != 0:
                                print(f'错误_房间号：{room_id}，错误,{r}')
                            elif uid != 0:
                                print(f'错误_房主号：{uid}，错误,{r}')
                else:
                    if room_id != 0:
                        print(f'错误_未查询到 房间号：{room_id}，的直播间基础信息')
                    elif uid != 0:
                        print(f'错误_未查询到 房主号：{uid}，的直播间基础信息，可能过于年轻')
        except Exception as r:
            print(f'请检查网络，{r}')
        return info

    def Room__get_info(self, room_id: int) -> dict:
        f"""
        获取直播间信息
        get_api：https://api.live.bilibili.com/room/v1/Room/get_info?room_id=
        :param room_id: 直播间房间号
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
                <td>uid</td>
                <td><em>num</em></td>
                <td><u>主播mid</u></td>
                <td></td>
            </tr>
            <tr>
                <td>room_id</td>
                <td><em>num</em></td>
                <td><u>直播间长号</u></td>
                <td></td>
            </tr>
            <tr>
                <td>short_id</td>
                <td><em>num</em></td>
                <td><u>直播间短号</u></td>
                <td>为0是无短号</td>
            </tr>
            <tr>
                <td>attention</td>
                <td><em>num</em></td>
                <td><u>关注数量</u></td>
                <td></td>
            </tr>
            <tr>
                <td>online</td>
                <td><em>num</em></td>
                <td><u>观看人数</u></td>
                <td></td>
            </tr>
            <tr>
                <td>is_portrait</td>
                <td><em>bool</em></td>
                <td><u>是否竖屏</u></td>
                <td></td>
            </tr>
            <tr>
                <td>description</td>
                <td><em>str</em></td>
                <td><u>描述</u></td>
                <td></td>
            </tr>
            <tr>
                <td>live_status</td>
                <td><em>num</em></td>
                <td><u>直播状态</u></td>
                <td>0：未开播<br>1：直播中<br>2：轮播中</td>
            </tr>
            <tr>
                <td>area_id</td>
                <td><em>num</em></td>
                <td><u>分区id</u></td>
                <td></td>
            </tr>
            <tr>
                <td>parent_area_id</td>
                <td><em>num</em></td>
                <td><u>父分区id</u></td>
                <td></td>
            </tr>
            <tr>
                <td>parent_area_name</td>
                <td><em>str</em></td>
                <td><u>父分区名称</u></td>
                <td></td>
            </tr>
            <tr>
                <td>old_area_id</td>
                <td><em>num</em></td>
                <td><u>旧版分区id</u></td>
                <td></td>
            </tr>
            <tr>
                <td>background</td>
                <td><em>str</em></td>
                <td><u>背景图片链接</u></td>
                <td></td>
            </tr>
            <tr>
                <td>title</td>
                <td><em>str</em></td>
                <td><u>标题</u></td>
                <td></td>
            </tr>
            <tr>
                <td>user_cover</td>
                <td><em>str</em></td>
                <td><u>封面</u></td>
                <td></td>
            </tr>
            <tr>
                <td>keyframe</td>
                <td><em>str</em></td>
                <td><u>关键帧</u></td>
                <td>用于网页端悬浮展示</td>
            </tr>
            <tr>
                <td>is_strict_room</td>
                <td><em>bool</em></td>
                <td><u>未知</u></td>
                <td>未知</td>
            </tr>
            <tr>
                <td>live_time</td>
                <td><em>str</em></td>
                <td><u>直播开始时间</u></td>
                <td>YYYY-MM-DD HH:mm:ss</td>
            </tr>
            <tr>
                <td>tags</td>
                <td><em>str</em></td>
                <td><u>标签</u></td>
                <td>','分隔</td>
            </tr>
            <tr>
                <td>is_anchor</td>
                <td><em>num</em></td>
                <td><u>未知</u></td>
                <td>未知</td>
            </tr>
            <tr>
                <td>room_silent_type</td>
                <td><em>str</em></td>
                <td><u>禁言状态</u></td>
                <td></td>
            </tr>
            <tr>
                <td>room_silent_level</td>
                <td><em>num</em></td>
                <td><u>禁言等级</u></td>
                <td></td>
            </tr>
            <tr>
                <td>room_silent_second</td>
                <td><em>num</em></td>
                <td><u>禁言时间</u></td>
                <td>单位是秒</td>
            </tr>
            <tr>
                <td>area_name</td>
                <td><em>str</em></td>
                <td><u>分区名称</u></td>
                <td></td>
            </tr>
            <tr>
                <td>pardants</td>
                <td><em>str</em></td>
                <td><u>未知</u></td>
                <td>未知</td>
            </tr>
            <tr>
                <td>area_pardants</td>
                <td><em>str</em></td>
                <td><u>未知</u></td>
                <td>未知</td>
            </tr>
            <tr>
                <td>hot_words</td>
                <td><em>list(str)</em></td>
                <td><u>热词</u></td>
                <td></td>
            </tr>
            <tr>
                <td>hot_words_status</td>
                <td><em>num</em></td>
                <td><u>热词状态</u></td>
                <td></td>
            </tr>
            <tr>
                <td>verify</td>
                <td><em>str</em></td>
                <td><u>未知</u></td>
                <td>未知</td>
            </tr>
            <tr>
                <td><span style="color: green; "><strong>["new_pendants"]</strong></span></td>
                <td><em>obj</em></td>
                <td><u>头像框\\大v</u></td>
                <td></td>
            </tr>
            <tr>
                <td>up_session</td>
                <td><em>str</em></td>
                <td><u>未知</u></td>
                <td></td>
            </tr>
            <tr>
                <td>pk_status</td>
                <td><em>num</em></td>
                <td><u>pk状态</u></td>
                <td></td>
            </tr>
            <tr>
                <td>pk_id</td>
                <td><em>num</em></td>
                <td><u>pk id</u></td>
                <td></td>
            </tr>
            <tr>
                <td>battle_id</td>
                <td><em>num</em></td>
                <td><u>未知</u></td>
                <td></td>
            </tr>
            <tr>
                <td>allow_change_area_time</td>
                <td><em>num</em></td>
                <td><u></u></td>
                <td></td>
            </tr>
            <tr>
                <td>allow_upload_cover_time</td>
                <td><em>num</em></td>
                <td><u></u></td>
                <td></td>
            </tr>
            <tr>
                <td><span style="color: green; "><strong>["studio_info"]</strong></span></td>
                <td><em>obj</em></td>
                <td><u></u></td>
                <td></td>
            </tr>
            <tr>
                <td>错误日志</td>
                <td><em>str</em></td>
                <td>0<br>警告信息<br>错误信息</td>
            </tr>
            </tbody>
        </table>
        <br><h3><span style="color: green; ">["new_pendants"]对象：</span></h3>
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
                <td><strong>["frame"]</strong></td>
                <td><em>obj</em></td>
                <td><u>头像框</u></td>
                <td></td>
            </tr>
            <tr>
                <td>mobile_frame</td>
                <td><em>obj</em></td>
                <td><u>同上</u></td>
                <td>手机版, 结构一致, 可能null</td>
            </tr>
            <tr>
                <td><strong>["badge"]</strong></td>
                <td><em>obj</em></td>
                <td><u>大v</u></td>
                <td></td>
            </tr>
            <tr>
                <td>mobile_badge</td>
                <td><em>obj</em></td>
                <td><u>同上</u></td>
                <td>手机版, 结构一致, 可能null</td>
            </tr>
            </tbody>
        </table>
        <br><h3><span style="color: #00D300; ">["new_pendants"]["frame"]对象：</span></h3>
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
                <td>name</td>
                <td><em>str</em></td>
                <td><u>名称</u></td>
                <td></td>
            </tr>
            <tr>
                <td>value</td>
                <td><em>str</em></td>
                <td><u>值</u></td>
                <td></td>
            </tr>
            <tr>
                <td>position</td>
                <td><em>num</em></td>
                <td><u>位置</u></td>
                <td></td>
            </tr>
            <tr>
                <td>desc</td>
                <td><em>str</em></td>
                <td><u>描述</u></td>
                <td></td>
            </tr>
            <tr>
                <td>area</td>
                <td><em>num</em></td>
                <td><u>分区</u></td>
                <td></td>
            </tr>
            <tr>
                <td>area_old</td>
                <td><em>num</em></td>
                <td><u>旧分区</u></td>
                <td></td>
            </tr>
            <tr>
                <td>bg_color</td>
                <td><em>str</em></td>
                <td><u>背景色</u></td>
                <td></td>
            </tr>
            <tr>
                <td>bg_pic</td>
                <td><em>str</em></td>
                <td><u>背景图</u></td>
                <td></td>
            </tr>
            <tr>
                <td>use_old_area</td>
                <td><em>bool</em></td>
                <td><u>是否旧分区号</u></td>
                <td></td>
            </tr>
            </tbody>
        </table>
        <br><h3><span style="color: #00D300; ">["new_pendants"]["badge"]对象：</span></h3>
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
                <td>name</td>
                <td><em>str</em></td>
                <td><u>类型</u></td>
                <td>v_person: 个人认证(黄) <br> v_company: 企业认证(蓝)</td>
            </tr>
            <tr>
                <td>position</td>
                <td><em>num</em></td>
                <td><u>位置</u></td>
                <td></td>
            </tr>
            <tr>
                <td>value</td>
                <td><em>str</em></td>
                <td><u>值</u></td>
                <td></td>
            </tr>
            <tr>
                <td>desc</td>
                <td><em>str</em></td>
                <td><u>描述</u></td>
                <td></td>
            </tr>
            </tbody>
        </table>
        <br><h3><span style="color: green; ">["studio_info"]对象：</span></h3>
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
                <td>status</td>
                <td><em>num</em></td>
                <td><u></u></td>
                <td></td>
            </tr>
            <tr>
                <td>master_list</td>
                <td><em>array</em></td>
                <td><u></u></td>
                <td></td>
            </tr>
            </tbody>
        </table>
        """
        url = f'https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}'
        request = requests.get(url, headers=self.headers).json()
        get_info_code = request['code']
        get_info_data = {}
        try:
            if get_info_code == 0:
                get_info_data = request['data']
            else:
                print(f'错误_房间号：{room_id}')
        except Exception as r:
            print(f'请检查网络，{r}')
        return get_info_data

    def Area__getList(self) -> list:
        """
        获取B站直播分区列表
        get_url：https://api.live.bilibili.com/room/v1/Area/getList
        :return:列表的元素为由一级分区数据的字典组成，二级分区数据包含在一级分区数据中
        <br><h3><span style="color: #00D300; ">[n]</span></h3>
        <table>
            <thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead>
            <tbody>
                <tr><td>id</td><td><em>num</em></td><td><u>父分区id</u></td><td></td></tr>
                <tr><td>name</td><td><em>name</em></td><td><u>父分区名</u></td><td></td></tr>
                <tr><td><strong><span style="green">["list"]</span></strong></td><td><em>list</em></td><td><u>子分区列表</u></td><td></td></tr>
            </tbody>
        </table>
        <br><br><h3><span style="color: #00D300; ">[n]["list"][x]</span></h3>
        <table>
            <thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead>
            <tbody>
                <tr><td>id</td><td><em>str</em></td><td><u>子分区id</u></td><td></td></tr>
                <tr><td>parent_id</td><td><em>str</em></td><td><u>父分区id</u></td><td></td></tr>
                <tr><td>old_area_id</td><td><em>str</em></td><td><u>旧分区id</u></td><td></td></tr>
                <tr><td>name</td><td><em>str</em></td><td><u>子分区名</u></td><td></td></tr>
                <tr><td>act_id</td><td><em>str</em></td><td><u>0</u></td><td><strong>作用尚不明确</strong></td></tr>
                <tr><td>pk_status</td><td><em>str</em></td><td><u>？？？</u></td><td><strong>作用尚不明确</strong></td></tr>
                <tr><td>hot_status</td><td><em>num</em></td><td><u>是否为热门分区</u></td><td>0：否<br>1：是</td></tr>
                <tr><td>lock_status</td><td><em>str</em></td><td><u>0</u></td><td><strong>作用尚不明确</strong></td></tr>
                <tr><td>pic</td><td><em>str</em></td><td><u>子分区标志图片url</u></td><td></td></tr>
                <tr><td>parent_name</td><td><em>str</em></td><td><u>父分区名</u></td><td></td></tr>
                <tr><td>area_type</td><td><em>num</em></td><td><u></u></td><td></td></tr>
            </tbody>
        </table>
        """
        url = f'https://api.live.bilibili.com/room/v1/Area/getList'
        request = requests.get(url, headers=self.headers).json()
        getAreaList_code = request['code']
        getAreaList_data = []
        try:
            if getAreaList_code == 0:
                getAreaList_data = request['data']
            else:
                print(f"['错误日志'] = f'获取分区列表错误！'")
        except Exception as r:
            print(f"['错误日志'] = f'请检查网络，{r}'")
        return getAreaList_data

    def live_user__v1__Master__info(self, uid: int) -> dict:
        """
        获取直播间主播信息
        get_url：https://api.live.bilibili.com/live_user/v1/Master/info?uid=
        :param uid:目标用户mid
        :return:self["data"]
        <table><thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td>code</td><td><em>num</em></td><td><u>返回值</u></td><td>0：成功<br>1：参数错误</td></tr><tr><td>msg</td><td><em>str</em></td><td><u>错误信息</u></td><td>默认为空</td></tr><tr><td>message</td><td><em>str</em></td><td><u>错误信息</u></td><td>默认为空</td></tr><tr><td><font color="#009900">["data"]</font></td><td><em>obj</em></td><td><u>信息本体</u></td><td></td></tr></tbody></table>
        <p>&nbsp;</p>
        <p><code><font color="#00FF00">["data"]</font></code></p>
        <table><thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td><font color="#0099CC">["info"]</font></td><td><em>obj</em></td><td><u>主播信息</u></td><td></td></tr><tr><td><font color="#6D16FF">["exp"]</font></td><td><em>obj</em></td><td><u>经验等级</u></td><td></td></tr><tr><td>follower_num</td><td><em>num</em></td><td><u>主播粉丝数</u></td><td></td></tr><tr><td>room_id</td><td><em>num</em></td><td><u>直播间id（短号）</u></td><td></td></tr><tr><td>medal_name</td><td><em>str</em></td><td><u>粉丝勋章名</u></td><td></td></tr><tr><td>glory_count</td><td><em>num</em></td><td><u>主播荣誉数</u></td><td></td></tr><tr><td>pendant</td><td><em>str</em></td><td><u>直播间头像框url</u></td><td></td></tr><tr><td>link_group_num</td><td><em>num</em></td><td><u>0</u></td><td><strong>作用尚不明确</strong></td></tr><tr><td><font color="#CC2DB7">["room_news"]</font></td><td><em>obj</em></td><td><u>主播公告</u></td><td></td></tr></tbody></table>
        <p>&nbsp;</p>
        <p><code><font color="#00FF00">["data"]</font><font color="#4CBFF2">["info"]</font></code></p>
        <table><thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td>uid</td><td><em>num</em></td><td><u>主播mid</u></td><td></td></tr><tr><td>uname</td><td><em>str</em></td><td><u>主播用户名</u></td><td></td></tr><tr><td>face</td><td><em>str</em></td><td><u>主播头像url</u></td><td></td></tr><tr><td><font color="#B20C26">["official_verify"]</font></td><td><em>obj</em></td><td><u>认证信息</u></td><td></td></tr><tr><td>gender</td><td><em>num</em></td><td><u>主播性别</u></td><td>-1：保密<br>0：女<br>1：男</td></tr></tbody></table>
        <p>&nbsp;</p>
        <p><code><font color="#00FF00">["data"]</font><font color="#4CBFF2">["info"]</font></code><code><font color="#B20C26">["official_verify"]</font></code></p>
        <table><thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td>type</td><td><em>num</em></td><td><u>主播认证类型</u></td><td>-1：无<br>0：个人认证<br>1：机构认证</td></tr><tr><td>desc</td><td><em>str</em></td><td><u>主播认证信息</u></td><td></td></tr></tbody></table>
        <p>&nbsp;</p>
        <p><code><font color="#00FF00">["data"]</font><font color="#8C72FF">["exp"]</font></code>对象：</p>
        <table><thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td><font color="#FF6699">["master_level"]</font></td><td><em>obj</em></td><td><u>主播等级</u></td><td></td></tr></tbody></table>
        <p>&nbsp;</p>
        <p><code><font color="#00FF00">["data"]</font><font color="#8C72FF">["exp"]</font></code><code><font color="#FFA8DB">["master_level"]</font></code></p>
        <table><thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td>level</td><td><em>num</em></td><td><u>当前等级</u></td><td></td></tr><tr><td>color</td><td><em>num</em></td><td><u>等级框颜色</u></td><td></td></tr><tr><td>current</td><td><em>array</em></td><td><u>当前等级信息</u></td><td></td></tr><tr><td>next</td><td><em>array</em></td><td><u>下一等级信息</u></td><td></td></tr></tbody></table>
        <p>&nbsp;</p>
        <p><code><font color="#00FF00">["data"]</font><font color="#8C72FF">["exp"]</font><font color="#FFA8DB">["master_level"]</font></code><code>["current"][n]</code></p>
        <table><thead><tr><th>项</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td>0</td><td><em>num</em></td><td><u>升级积分</u></td><td></td></tr><tr><td>1</td><td><em>num</em></td><td><u>总积分</u></td><td></td></tr></tbody></table>
        <p>&nbsp;</p>
        <p><code><font color="#00FF00">["data"]</font><font color="#8C72FF">["exp"]</font><font color="#FFA8DB">["master_level"]</font></code><code>["next"][n]</code></p>
        <table><thead><tr><th>项</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td>0</td><td><em>num</em></td><td><u>升级积分</u></td><td></td></tr><tr><td>1</td><td><em>num</em></td><td><u>总积分</u></td><td></td></tr></tbody></table>
        <p>&nbsp;</p>
        <p><code><font color="#00FF00">["data"]</font><font color="#CC6BE0">["room_news"]</font></code>对象：</p>
        <table><thead><tr><th>字段</th><th><em>类型</em></th><th><u>内容</u></th><th>备注</th></tr></thead><tbody><tr><td>content</td><td><em>str</em></td><td><u>公告内容</u></td><td></td></tr><tr><td>ctime</td><td><em>str</em></td><td><u>公告时间</u></td><td></td></tr><tr><td>ctime_text</td><td><em>str</em></td><td><u>公告日期</u></td><td></td></tr></tbody></table>
        """
        url = f'https://api.live.bilibili.com/live_user/v1/Master/info?uid={uid}'
        request = requests.get(url, headers=self.headers).json()
        live_user__v1__Master__info_data = request['data']
        return live_user__v1__Master__info_data


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
        self.Danmu = self.__Danmu(self.headers, self.user__get_user_info, self.operationOnBroadcastCode,
                                  self.developerInfo_developer,
                                  self.getAppList_audit, self.start_app, self.end_app)

    class __Danmu:
        def __init__(self, headers: dict, user__get_user_info: Callable[[], dict],
                     operationOnBroadcastCode: Callable[[int], str],
                     developerInfo_developer: Callable[[], dict], getAppList_audit: Callable[[], list],
                     start_app: Callable[[str, str, str, int], dict], end_app: Callable[[str, str, str, int], dict]):
            """

            :param headers:
            :param user__get_user_info: 用于获取普通模式弹幕所需要的参数 uid
            :param operationOnBroadcastCode: 用于获取 开放平台 和 身份码 模式弹幕之中函数 start_app 所需的参数之一 code
            :param developerInfo_developer:用于获取 开放平台 和 身份码 模式弹幕之中函数 start_app 所需的参数 api_key 和 secret_key
            :param getAppList_audit: 用于获取 开放平台 和 身份码 模式弹幕之中函数 start_app 函数的参数之一 app_id
            :param start_app:用于获取 开放平台 和 身份码 模式弹幕之中的  WSS链接 和 WSS认证包 的函数
            :param end_app:关闭 start_app
            """
            self.headers = headers
            self.__user__get_user_info = user__get_user_info
            self.__operationOnBroadcastCode = operationOnBroadcastCode
            self.__developerInfo_developer = developerInfo_developer
            self.__getAppList_audit = getAppList_audit
            self.__start_app = start_app
            self.__end_app = end_app
            self.OpenZone = self.__OpenZone(self.session, self.websocket, self.__getAppList_audit,
                                            self.__operationOnBroadcastCode, self.__developerInfo_developer,
                                            self.__start_app, self.__end_app)
            self.CodeID = self.__CodeID(headers, self.__operationOnBroadcastCode, self.session, self.websocket)

        def Normal(self, roomid: int) -> '__Normal':
            Normal = self.__Normal(self.headers, roomid, self.session, self.websocket, self.__user__get_user_info)
            return Normal

        class __Normal:
            def __init__(self, headers: dict, roomid: int, session: type, websocket: type,
                         user__get_user_info: Callable[[], dict]):
                self.headers = headers
                self.roomid = roomid
                self.__session = session
                self.__websocket = websocket
                self.__user__get_user_info = user__get_user_info
                self.__BiliGeneralApi = BiliGeneralApi(headers)

            def session(self):
                self.wss_url, self.auth_body = self.__connect(self.roomid)
                session = self.__session(self.wss_url, self.auth_body)
                return session

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

        class __OpenZone:
            def __init__(self, session: type, websocket: type, getAppList_audit: Callable[[], list],
                         operationOnBroadcastCode: Callable[[int], str], developerInfo_developer: Callable[[], dict],
                         start_app: Callable[[str, str, str, int], dict],
                         end_app: Callable[[str, str, str, int], dict]):
                self.__session = session
                self.__websocket = websocket
                self.__getAppList_audit = getAppList_audit
                self.__operationOnBroadcastCode = operationOnBroadcastCode
                self.__developerInfo_developer = developerInfo_developer
                self.__start_app = start_app
                self.__end_app = end_app

            def session(self):
                self.wss_url, self.auth_body = self.__connect()
                session = self.__session(self.wss_url, self.auth_body)
                return session

            def websocket(self):
                self.wss_url, self.auth_body = self.__connect()
                websocket = self.__websocket(self.wss_url, self.auth_body)
                return websocket

            def __connect(self):
                AppList = self.__getAppList_audit()
                idcode = self.__operationOnBroadcastCode(1)
                developerInfo = self.__developerInfo_developer()
                start_app = self.__start_app(idcode,
                                             developerInfo["developer_info"]['access_key'],
                                             developerInfo["developer_info"]['access_secret_key'],
                                             AppList[0]['app_id'])
                game_id = start_app['data']['game_info']['game_id']
                auth_body = start_app['data']['websocket_info']['auth_body']
                wss_url = start_app['data']['websocket_info']['wss_link'][0]
                self.__end_app(game_id, developerInfo["developer_info"]['access_key'],
                               developerInfo["developer_info"]['access_secret_key'],
                               AppList[0]['app_id'])
                return wss_url, auth_body

        class __CodeID:
            def __init__(self, headers, operationOnBroadcastCode: Callable[[int], str], session, websocket):
                self.headers = headers
                self.__operationOnBroadcastCode = operationOnBroadcastCode
                self.__session = session
                self.__websocket = websocket

            def session(self):
                self.wss_url, self.auth_body = self.__connect()
                session = self.__session(self.wss_url, self.auth_body)
                return session

            def websocket(self):
                self.wss_url, self.auth_body = self.__connect()
                websocket = self.__websocket(self.wss_url, self.auth_body)
                return websocket

            def __connect(self):
                data = {"code": self.__operationOnBroadcastCode(1), "app_id": 0}
                start_game = requests.post("https://chat.bilisc.com/api/open_live/start_game", json=data,
                                           headers=self.headers).json()
                print(start_game['data']['websocket_info'])
                auth_body = start_game['data']['websocket_info']['auth_body']
                wss_url = start_game['data']['websocket_info']['wss_link'][0]
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
                        self.DanmuInfo = content
                        # if json.loads(content)["cmd"] == "DANMU_MSG":
                        #     print(f"{content}")
                        #     if type(json.loads(content)["info"][0][13]) == dict:
                        #         DANMU_type = '表情'
                        #     else:
                        #         DANMU_type = ''
                        #     DANMU_time = json.loads(content)["info"][9]['ts']
                        #     DANMU_uname = json.loads(content)["info"][2][1]
                        #     DANMU_ = json.loads(content)["info"][1]
                        #     print(UnixTime2UtcTime(DANMU_time), DANMU_type, DANMU_uname, '\t:\t\t', DANMU_)
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
                # await asyncio.sleep(3.125)
                # await self.connect()

            def starDanMu(self):
                asyncio.run(self.main())

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
                :param wss_url:
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

                asyncio.create_task(send_heartbeat())

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
                    # print(f"这是鉴权回复：{self.AuthenticationReply}\n")
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

    def audit__GetRoomInfo(self) -> int:
        """
        获得cookie对应的B站直播间房间号
        get_url：https://api.live.bilibili.com/xlive/open-platform/v1/audit/GetRoomInfo
        :return: B站直播间房间号_int
        """
        url = 'https://api.live.bilibili.com/xlive/open-platform/v1/audit/GetRoomInfo'
        request = requests.get(url, headers=self.headers).json()
        GetRoomInfo_data = request['data']['room_id']
        return GetRoomInfo_data

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

    def user__live_info(self) -> dict:
        """
        B站直播间后台直播用户相关信息和B币数量
        get_url：https://api.live.bilibili.com/xlive/web-ucenter/user/live_info
        :return:
        <pre>{<br>&#32;&#32;"room_id":&#32;int(B站直播间房间号),<br>&#32;&#32;"main_site_level_rank":&#32;10000,<br>&#32;&#32;"master":&#32;{<br>&#32;&#32;&#32;&#32;"level":&#32;int(主播等级),<br>&#32;&#32;&#32;&#32;"current":&#32;int(当前主播等级经验值),<br>&#32;&#32;&#32;&#32;"next":&#32;int(当前主播等级经验值槽),<br>&#32;&#32;&#32;&#32;"medal":&#32;null<br>&#32;&#32;},<br>&#32;&#32;"vip_info":&#32;{<br>&#32;&#32;&#32;&#32;"vip_endtime":&#32;"0000-00-00&#32;00:00:00",<br>&#32;&#32;&#32;&#32;"svip_endtime":&#32;"0000-00-00&#32;00:00:00",<br>&#32;&#32;&#32;&#32;"month_price":&#32;20000,<br>&#32;&#32;&#32;&#32;"year_price":&#32;233000,<br>&#32;&#32;&#32;&#32;"vip_view_status":&#32;false<br>&#32;&#32;},<br>&#32;&#32;"live_time":&#32;0,<br>&#32;&#32;"bili_coins":&#32;int(B币数量),<br>&#32;&#32;"san":&#32;int(主播SAN值),<br>&#32;&#32;"count":&#32;{<br>&#32;&#32;&#32;&#32;"guard":&#32;int(大航海粉丝牌数量，未续费也算),<br>&#32;&#32;&#32;&#32;"fans_medal":&#32;int(粉丝勋章数量),<br>&#32;&#32;&#32;&#32;"title":&#32;0,<br>&#32;&#32;&#32;&#32;"title_new":&#32;0,<br>&#32;&#32;&#32;&#32;"achieve":&#32;0<br>&#32;&#32;},<br>&#32;&#32;"anchor_switch_info":&#32;{<br>&#32;&#32;&#32;&#32;"voice_barrage":&#32;-1<br>&#32;&#32;},<br>&#32;&#32;"need_guide":&#32;0,<br>&#32;&#32;"emoticon_management":&#32;0,<br>&#32;&#32;"up_emoticon_jurisdiction":&#32;0,<br>&#32;&#32;"anchor_room_emoticon":&#32;0,<br>&#32;&#32;"anchor_violations_record":&#32;1<br>}</pre>
        """
        url = 'https://api.live.bilibili.com/xlive/web-ucenter/user/live_info'
        response = requests.get(url=url, headers=self.headers).json()
        user__live_info_data = response["data"]
        return user__live_info_data

    def getRoomNews(self, room_id: int) -> str:
        """
        获得直播间公告
        get_url：https://api.live.bilibili.com/xlive/app-blink/v1/index/getRoomNews?room_id=
        :param __headers: 带cookie的headers
        :param room_id: B站直播间房间号
        :return: 直播间公告
        """
        url = f'https://api.live.bilibili.com/xlive/app-blink/v1/index/getRoomNews?room_id={room_id}'
        response = requests.get(url=url, headers=self.headers).json()
        News = response["data"]["content"]
        room_id = response["data"]["room_id"]
        if News == "":
            url = f'https://api.live.bilibili.com/xlive/app-blink/v1/index/getRoomNews?room_id={room_id}'
            response = requests.get(url=url, headers=self.headers).json()
            News = response["data"]["content"]
        return News

    def operationOnBroadcastCode(self, action: int = 1) -> str:
        """
        直播创作者服务中心,获得开放平台身份码
        post_url：https://api.live.bilibili.com/xlive/open-platform/v1/common/operationOnBroadcastCode
        data：{'csrf': csrf, 'action': int}
        :param action: 1 => 查看身份码，2=> 刷新身份码
        :param csrf:
        :return:开放平台身份码
        """
        url = 'https://api.live.bilibili.com/xlive/open-platform/v1/common/operationOnBroadcastCode'
        cookie = self.headers['cookie']
        csrf = cookieFormat2dict(cookie)['bili_jct']
        data = {'csrf': csrf, 'action': action}
        response = requests.post(url=url, data=data, headers=self.headers).json()
        operationOnBroadcastCode_data = response['data']
        return operationOnBroadcastCode_data['code']

    def start_app(self, code: str, api_key: str, secret_key: str, app_id: int) -> dict:
        """
        直播创作者服务中心,开启项目，基于直播开放平台获取B站直播弹幕wss://链接，wss心跳，wss认证
        post_url：https://live-open.biliapi.com/v2/app/start
        data：{"code": 开放平台身份码, "app_id": 项目id}
        hearder：
        **Accept:** application/json
        **Content-Type:** 必须为application/json，后面加; charset=utf-8都不行
        **x-bili-content-md5:** post参数的json字符串进行MD5后得到的32位字符串
        ## 比如/v2/app/start的post参数{"code":"SSSS8SSS88S88", "app_id":123456789101}，md5计算后得到0b010df38273f74f17772b286b1a8406
        **x-bili-timestamp:** 十位的时间戳
        **x-bili-signature-version:** 目前1.0
        **x-bili-signature-nonce:** 随机数，官方用的是uuid
        **x-bili-signature-method:** 签名算法：目前固定HMAC-SHA256
        **x-bili-accesskeyid:** 个人开发者的access_key_id
        **Authorization:** sha256计算后的字符串，具体计算方法在下面

        Authorization计算
        声明字符串，赋值以下参数
        String preAuthorization =
        "x-bili-accesskeyid:"+ 个人开发者的access_key_id +"\\n"
        +"x-bili-content-md5:"+ 0b010df38273f74f17772b286b1a8406 +"\\n"
        +"x-bili-signature-method:HMAC-SHA256\\n"
        +"x-bili-signature-nonce:"+ 1b4c4604-a446-45c3-b918-8795c7419e16 +"\\n"
        +"x-bili-signature-version:1.0\\n"
        +"x-bili-timestamp:"+ 1695448824

        :param code:开放平台身份码
        :param api_key:
        :param secret_key:
        :param app_id:
        :return:
        <pre>{<br>&#32;&#32;'code':&#32;0,<br>&#32;&#32;'message':&#32;'0',<br>&#32;&#32;'request_id':&#32;'1763191294904795136',<br>&#32;&#32;'data':&#32;{<br>&#32;&#32;&#32;&#32;'anchor_info':&#32;{<br>&#32;&#32;&#32;&#32;&#32;&#32;'room_id':&#32;int(主播房间号),<br>&#32;&#32;&#32;&#32;&#32;&#32;'uface':&#32;str(主播头像),<br>&#32;&#32;&#32;&#32;&#32;&#32;'uid':&#32;int(主播uid(即将废弃)),<br>&#32;&#32;&#32;&#32;&#32;&#32;'uname':&#32;str(主播昵称),<br>&#32;&#32;&#32;&#32;&#32;&#32;"open_id":&#32;str(用户唯一标识(2024-03-11后上线))<br>&#32;&#32;&#32;&#32;},<br>&#32;&#32;&#32;&#32;'game_info':&#32;{<br>&#32;&#32;&#32;&#32;&#32;&#32;'game_id':str(&#32;场次id,心跳key(心跳保持20s-60s)调用一次,超过60s无心跳自动关闭,长连停止推送消息)<br>&#32;&#32;&#32;&#32;},<br>&#32;&#32;&#32;&#32;'websocket_info':&#32;{<br>&#32;&#32;&#32;&#32;&#32;&#32;'auth_body':&#32;str(长连使用的请求json体)='{"roomid":0,"protover":2,"uid":随机uid,"key":"","group":"open"}',<br>&#32;&#32;&#32;&#32;&#32;&#32;'wss_link':&#32;[<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;["wss_link"][0],<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;["wss_link"][1],<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;["wss_link"][2]<br>&#32;&#32;&#32;&#32;&#32;&#32;]<br>&#32;&#32;&#32;&#32;}<br>&#32;&#32;}<br>}<br>
        </pre>
        """
        url = "https://live-open.biliapi.com/v2/app/start"
        data = {"code": code, "app_id": app_id}
        headers = {
            "x-bili-accesskeyid": api_key,
            "x-bili-content-md5": hashlib.md5(json.dumps(data, ensure_ascii=False).encode('utf-8')).hexdigest(),
            "x-bili-signature-method": "HMAC-SHA256",
            "x-bili-signature-nonce": str(int(random.random() * 1e5) + int(time.time())),
            "x-bili-signature-version": "1.0",
            "x-bili-timestamp": str(int(time.time())),
        }
        # print(hashlib.md5(json.dumps(data, ensure_ascii=False).encode('utf-8')).hexdigest())
        signature_string = "\n".join([f"{key}:{headers[key]}" for key in sorted(headers.keys())])
        # print(signature_string)
        signature = hmac.new(secret_key.encode('utf-8'), signature_string.encode('utf-8'), hashlib.sha256).hexdigest()
        # print(signature)
        headers.update(self.headers)
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        headers["Authorization"] = signature
        # print(__headers)
        response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False)).json()
        return response

    def end_app(self, game_id: str, api_key: str, secret_key: str, app_id: int) -> dict:
        """
        直播创作者服务中心,项目关闭,，调用后会同步下线互动道具等内容，项目关闭后才能进行下一场次互动。<br>
        游戏结束的时候，一定要调用end接口，否则将会影响礼物投放，会直接影响到您的收益。
        post_url：https://live-open.biliapi.com/v2/app/end
        data：{"app_id": 项目id, "game_id": 场次id}
        hearder：
        **Accept:** application/json
        **Content-Type:** 必须为application/json，后面加; charset=utf-8都不行
        **x-bili-content-md5:** post参数的json字符串进行MD5后得到的32位字符串
        ## 比如/v2/app/start的post参数{"code":"SSSS8SSS88S88", "app_id":123456789101}，md5计算后得到0b010df38273f74f17772b286b1a8406
        **x-bili-timestamp:** 十位的时间戳
        **x-bili-signature-version:** 目前1.0
        **x-bili-signature-nonce:** 随机数，官方用的是uuid
        **x-bili-signature-method:** 签名算法：目前固定HMAC-SHA256
        **x-bili-accesskeyid:** 个人开发者的access_key_id
        **Authorization:** sha256计算后的字符串，具体计算方法在下面

        Authorization计算
        声明字符串，赋值以下参数
        String preAuthorization = "x-bili-accesskeyid:"+ 个人开发者的access_key_id +"\\n"
        +"x-bili-content-md5:"+ 0b010df38273f74f17772b286b1a8406 +"\\n"
        +"x-bili-signature-method:HMAC-SHA256\\n"
        +"x-bili-signature-nonce:"+ 1b4c4604-a446-45c3-b918-8795c7419e16 +"\\n"
        +"x-bili-signature-version:1.0\\n"
        +"x-bili-timestamp:"+ 1695448824

        :param game_id:场次id
        :param api_key:
        :param secret_key:
        :param app_id:
        :return:
        成功：
        <pre>{<br>&#32;&#32;"code":&#32;0,<br>&#32;&#32;"message":&#32;"ok",<br>&#32;&#32;"data":&#32;{}<br>}</pre>
        """
        url = 'https://live-open.biliapi.com/v2/app/end'
        data = {"app_id": app_id, "game_id": game_id}
        headers = {
            "x-bili-accesskeyid": api_key,
            "x-bili-content-md5": hashlib.md5(json.dumps(data, ensure_ascii=False).encode('utf-8')).hexdigest(),
            "x-bili-signature-method": "HMAC-SHA256",
            "x-bili-signature-nonce": str(int(random.random() * 1e5) + int(time.time())),
            "x-bili-signature-version": "1.0",
            "x-bili-timestamp": str(int(time.time())),
        }
        # print(hashlib.md5(json.dumps(data, ensure_ascii=False).encode('utf-8')).hexdigest())
        signature_string = "\n".join([f"{key}:{headers[key]}" for key in sorted(headers.keys())])
        # print(signature_string)
        signature = hmac.new(secret_key.encode('utf-8'), signature_string.encode('utf-8'), hashlib.sha256).hexdigest()
        # print(signature)
        headers.update(self.headers)
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        headers["Authorization"] = signature
        # print(__headers)
        response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False)).json()
        return response

    def sendEmailCode_developer(self, csrf: str, email: str) -> dict:
        """
        直播创作者服务中心,获取注册B站开放平台个人开发者的邮箱验证码
        <span style="color: red; ">每日有次数限制</span>
        post_url：https://api.live.bilibili.com/xlive/open-platform/v1/developer/sendEmailCode
        data：{'csrf_token': csrf, 'csrf': csrf, 'email': email}
        :param csrf:
        :param email:注册邮箱
        :return:
        {'code': 0, 'message': '0', 'ttl': 1, 'data': {}}
        """
        url = 'https://api.live.bilibili.com/xlive/open-platform/v1/developer/sendEmailCode'
        data = {'csrf_token': csrf, 'csrf': csrf, 'email': email}
        response = requests.post(url=url, data=data, headers=self.headers).json()
        return response

    def apply_developer(self, csrf: str, nick: str, email: str, verify: str, qq: str = '', wechat: str = '',
                        phone: str = '') -> dict:
        """
        直播创作者服务中心,提交注册B站开放平台个人开发者的个人信息
        post_url：https://api.live.bilibili.com/xlive/open-platform/v1/developer/apply?
        data：<pre>{<br>&#32;&#32;"data":&#32;{<br>&#32;&#32;&#32;&#32;"user_info":&#32;{<br>&#32;&#32;&#32;&#32;&#32;&#32;"nick":&#32;nick<br>&#32;&#32;&#32;&#32;},<br>&#32;&#32;&#32;&#32;"contact_info":&#32;{<br>&#32;&#32;&#32;&#32;&#32;&#32;"email":&#32;email,<br>&#32;&#32;&#32;&#32;&#32;&#32;"qq":&#32;qq,<br>&#32;&#32;&#32;&#32;&#32;&#32;"wechat":&#32;wechat,<br>&#32;&#32;&#32;&#32;&#32;&#32;"phone":&#32;phone<br>&#32;&#32;&#32;&#32;},<br>&#32;&#32;&#32;&#32;"verify":&#32;verify,<br>&#32;&#32;&#32;&#32;"type":&#32;11003<br>&#32;&#32;},<br>&#32;&#32;"csrf_token":&#32;csrf,<br>&#32;&#32;"csrf":&#32;csrf,<br>&#32;&#32;"visit_id":&#32;""<br>}</pre>
        :param csrf:
        :param nick: 注册开发者昵称，不需要是B站昵称
        :param email: 注册邮箱
        :param verify: 邮箱验证码
        :param qq:
        :param wechat:
        :param phone:
        :return:
        {'code': 20003, 'message': '已认证通过', 'ttl': 1, 'data': {}}<br>
        {'code': 20013, 'message': '获取开发者房间信息失败', 'ttl': 1, 'data': {}}
        """
        data = {"data": {"user_info": {"nick": nick},
                         "contact_info": {"email": email, "qq": qq, "wechat": wechat, "phone": phone},
                         "verify": verify, "type": 11003},
                "csrf_token": csrf,
                "csrf": csrf,
                "visit_id": ""}
        data = Payload2HtmlUrlCode(data)
        url = f'https://api.live.bilibili.com/xlive/open-platform/v1/developer/apply?{data}'
        response = requests.post(url=url, headers=self.headers).json()
        return response

    def info_developer(self) -> dict:
        """
        直播创作者服务中心,个人开发者的少量信息
        post_url：https://api.live.bilibili.com/xlive/open-platform/v1/developer/info
        :return:
        <pre>{<br>&#32;&#32;&#32;&#32;"code":&#32;0,<br>&#32;&#32;&#32;&#32;"message":&#32;"0",<br>&#32;&#32;&#32;&#32;"ttl":&#32;1,<br>&#32;&#32;&#32;&#32;"data":&#32;{<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"user_info":&#32;{<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"nick":&#32;"开发者昵称，不是B站昵称"<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;},<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"company_info":&#32;{},<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"admin_info":&#32;{},<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"contact_info":&#32;{<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"email":&#32;"开发者注册邮箱"<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;},<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"type":&#32;11003,<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"status":&#32;1,<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"ctime":&#32;int(疑似申请通过时间，Unix时间戳),<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"mtime":int(申请时间，Unix时间戳),<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"reason":&#32;"",<br>&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;"settlement_info":&#32;{}<br>&#32;&#32;&#32;&#32;}<br>}</pre>
        """
        url = 'https://api.live.bilibili.com/xlive/open-platform/v1/developer/info'
        response = requests.post(url=url, headers=self.headers).json()
        info_developer_data = response['data']
        return info_developer_data

    def developerInfo_developer(self) -> dict:
        """
        直播创作者服务中心,个人开发者的一些开发信息
        <span style="color: green; ">未注册也有输出</span>
        get_url：https://api.live.bilibili.com/xlive/open-platform/v1/developer/developerInfo?
        :return:
        <pre>{<br>    &quot;code&quot;: 0,<br>    &quot;message&quot;: &quot;0&quot;,<br>    &quot;ttl&quot;: 1,<br>    &quot;data&quot;: {<br>        &quot;developer_info&quot;: {<br>            &quot;nick&quot;: &quot;开发者昵称，不是B站昵称&quot;,<br>            &quot;type&quot;: 11003,<br>            &quot;level&quot;: 4,<br>            &quot;credit_level&quot;: 10,<br>            &quot;room_id&quot;: int(直播间房间号),<br>            &quot;access_key&quot;: &quot;str(access_key_id)&quot;,<br>            &quot;access_secret_key&quot;: &quot;str(access_key_secred)&quot;,<br>            &quot;phone&quot;: &quot;手机号&quot;,<br>            &quot;mail&quot;: &quot;注册邮箱&quot;,<br>            &quot;level_update_time&quot;: &quot;时间&quot;,<br>            &quot;credit_update_time&quot;: &quot;创建时间&quot;<br>        }<br>    }<br>}</pre>
        """
        url = 'https://api.live.bilibili.com/xlive/open-platform/v1/developer/developerInfo?'
        response = requests.get(url=url, headers=self.headers).json()
        developerInfo_developer_data = response['data']
        return developerInfo_developer_data

    def createApp_audit(self, app_name: str, app_type: int, app_introduction: str, app_icon: str, csrf: str) -> dict:
        """
        直播创作者服务中心,创建项目
        post_url：https://api.live.bilibili.com/xlive/open-platform/v1/audit/createApp
        data：<pre>{<br>&#32;&#32;"app_name":&#32;项目名称,<br>&#32;&#32;"app_type":&#32;项目分类,<br>&#32;&#32;"app_introduction":&#32;项目简介,<br>&#32;&#32;"app_icon":&#32;项目图标链接,<br>&#32;&#32;"csrf_token":&#32;csrf,<br>&#32;&#32;"csrf":&#32;csrf,<br>&#32;&#32;"visit_id":&#32;""<br>}<br></pre>
        :param app_name: 项目名称
        :param app_type:项目分类：0 => 互动玩法 ,1 => H5插件 ,2 => 直播工具
        :param app_introduction:项目简介
        :param app_icon:项目图标链接（尺寸为200*200，大小在1M以内，格式为png或jpg图片）url
        :param csrf:
        :return:
        创建成功：{}<br>
        创建失败：None
        """
        url = 'https://api.live.bilibili.com/xlive/open-platform/v1/audit/createApp'
        data = {
            "app_name": app_name,
            "app_type": app_type,
            "app_introduction": app_introduction,
            "app_icon": app_icon,
            "csrf_token": csrf,
            "csrf": csrf,
            "visit_id": ""
        }
        response = requests.post(url=url, data=data, headers=self.headers).json()
        # print(response['message'])  # 成功为0，失败为错误消息
        createApp_audit_data = response['data']
        return createApp_audit_data

    def getAppList_audit(self) -> list:
        """
        直播创作者服务中心,项目列表
        get_url：https://api.live.bilibili.com/xlive/open-platform/v1/audit/getAppList
        :return:
        <pre>{<br>    &quot;code&quot;: 0,<br>    &quot;message&quot;: &quot;0&quot;,<br>    &quot;ttl&quot;: 1,<br>    &quot;data&quot;: {<br>        &quot;app_list&quot;: [<br>            {<br>                &quot;app_name&quot;: &quot;项目名称&quot;,<br>                &quot;app_type&quot;: int(项目分类)：0&#32;=&gt;&#32;互动玩法&#32;,1&#32;=&gt;&#32;H5插件&#32;,2&#32;=&gt;&#32;直播工具,<br>                &quot;app_icon&quot;: &quot;项目图标url&quot;,<br>                &quot;app_version&quot;: &quot;线上版本&quot;,<br>                &quot;create_time&quot;: &quot;创建时间&quot;,<br>                &quot;update_time&quot;: &quot;最近修改时间&quot;,<br>                &quot;app_id&quot;: int(项目ID),<br>                &quot;app_owner_id&quot;: int(B站uid),<br>                &quot;app_status&quot;: 0,<br>                &quot;app_release_status&quot;: 0,<br>                &quot;level&quot;: 5,<br>                &quot;level_update_time&quot;: &quot;2024-02-21 18:30:23&quot;,<br>                &quot;can_delete&quot;: 1,<br>                &quot;can_rename&quot;: 1<br>            },<br>            &hellip;&hellip;<br>    }<br>}</pre>
        没有项目则为：None
        """
        url = 'https://api.live.bilibili.com/xlive/open-platform/v1/audit/getAppList'
        response = requests.get(url=url, headers=self.headers).json()
        getAppList_audit_data = response['data']
        return getAppList_audit_data["app_list"]

    def deleteApp_audit(self, app_id, csrf) -> dict:
        """
        直播创作者服务中心,删除项目
        post_url：https://api.live.bilibili.com/xlive/open-platform/v1/audit/deleteApp
        data：{"app_id": 项目ID, "csrf_token": csrf, "csrf": csrf, "visit_id": ""}
        :param app_id:项目ID
        :param csrf:
        :return:
        <pre>{&quot;code&quot;:5002,&quot;message&quot;:&quot;内部错误&quot;,&quot;ttl&quot;:1,&quot;data&quot;:null}</pre>
        成功data：{'is_success': True}<br>
        失败data：None
        """
        url = 'https://api.live.bilibili.com/xlive/open-platform/v1/audit/deleteApp'
        data = {
            "app_id": app_id,
            "csrf_token": csrf,
            "csrf": csrf,
            "visit_id": ""
        }
        response = requests.post(url=url, data=data, headers=self.headers).json()
        # print(response['message'])  # 成功为0，没有项目ID对应的为内部错误
        deleteApp_audit_data = response['data']
        return deleteApp_audit_data



