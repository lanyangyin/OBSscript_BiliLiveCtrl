import requests

from BiliBiliAPI_limited import start_login

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/58.0.3029.110 Safari/537.3',
    'cookie': start_login(3546559824267399)
}

def update_member(uname, usersign, sex, birthday):
    print(uname)
    api = "https://api.bilibili.com/x/member/web/update"
    data = {'uname': uname,
            'usersign': usersign,
            'sex': sex,
            'birthday': birthday,
            'csrf': 'a53e401d3ad92bdea88918773b574589'
            }
    response = requests.post(api, headers=headers, params=data).json()
    return response


print(update_member("\u309a橡塑乐ヾl-v-lヾ", "", "男", "1980-01-01"))
