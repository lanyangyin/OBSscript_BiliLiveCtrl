---
--- Generated by EmmyLua(https://github.com/EmmyLua)
--- Created by lanan.
--- DateTime: 2024/2/27 12:33
---
--[[
【{"qrcode", package2="requests", "aiohttp"}这种格式在lua中为table表，类似python中的dict字典】
【table表无key的value会自动从1开始添加一个数字key，例如：
    {"qrcode", package2="requests", "aiohttp"} 等同于 {[1]="qrcode", package2="requests", [2]="aiohttp"}】
【lua中使用pairs()可以将table格式中{{有key的元素}}转换成类似python中list列表，列表元素类似为python的元组(key, value)】
【lua中使用ipairs()可以将table格式中{{无key的元素}}转换成类似python中list列表，列表元素类似为python的元组(key, value)】
【可以用table.key = value 和 table["key"] = value table的key添加元素key=value】
【table.insert(table, value)给table添加元素value】
【string = table.concat(table【, str【, start, stop】】) string为table的没有key的元素且用str做隔断】
【#table table中没有key的元素的元素数量】
【local success, table = pcall(load("return " .. str))将str转化为table，str格式值要用双引号，如：
    '{"qrcode", "requests", "aiohttp"}'，success为布尔值判断成功与否】
--]]


obs = obslua

--[[路径常量]]
--- 当前脚本文件所在路径
local LuaSelf_Filepath = string.sub(debug.getinfo(1).source, 1)
--- 当前脚本文件文件夹所在路径，末尾带/
local LuaSelf_Dir_path = string.match(LuaSelf_Filepath, "(.*/)[^/]+")
--- 插件的配置文件所在文件夹所在路径，末尾带/
local BliveCtrl_Dir_Path = LuaSelf_Dir_path .. "BiliLiveCtrl_lua/"
--- 配置文件之一temp 文件路径
local temp_Filepath = BliveCtrl_Dir_Path .. '/BiliLiveCtrl_lua.temp'
--- 参数文件的路径
local bilibili_cookie_Filepath = BliveCtrl_Dir_Path .. 'devices.json'
--- OBS的B站直播后台控制脚本辅助运行python文件：obsScripts_BliveSettingPythonNeed.py 文件路径
local BliveSettingPythonNeed_Filepath = BliveCtrl_Dir_Path .. "obsScripts_BliveSettingPythonNeed.py"

--构造函数
--[[通用函数]]
---[[[获取操作系统类型]]]
---@type function
---@return string|boolean Windows|Linux|macOS||false
local function getOSType()
    local os_name = false
    local os_type = string.lower(package.config:sub(1, 1) == '\\' and 'windows' or io.popen('uname -s'):read('*l') or 'unknown')
    if os_type == 'windows' then
        os_name = "Windows"
    elseif os_type == 'linux' then
        os_name = "Linux"
    elseif os_type == 'darwin' then
        os_name = "macOS"
    else
        os_name = nil
    end
    return os_name
end -- 获取操作系统类型
--- 获取操作系统类型
local os_name = getOSType()
---[[[创建配置文件所在文件夹]]]
---@type function
---@return nil
local function buildDirBliveCtrl()
    if os_name then
        local command
        print('尝试创建 BliveCtrl 文件夹')
        local result
        if os_name == 'Windows' then
            command = 'mkdir \"' .. BliveCtrl_Dir_Path .. '\" && echo 1 || echo 0'
        elseif os_name == 'Linux' or os_name == 'macOS' then
            command = 'mkdir -p \"' .. BliveCtrl_Dir_Path .. '\" -m 777 && echo 1 || echo 0'
        end
        print(command)
        result = io.popen(command)
        local resultall = result:read('*a'):gsub("^[\n%s]*(.-)[\n%s]*$", "%1")
        if resultall == '0' then
            print("BliveCtrl 文件夹已存在或创建失败")
        elseif resultall == '1' then
            print("BliveCtrl 文件夹创建成功")
        end
        result:close()
    end
end -- 创建配置文件所在文件夹
---[[[创建 temp 文件]]]
---@type function
---@return nil
local function BuildTemp()
    local command
    local temp_OpenR = io.open(temp_Filepath, "r")
    if temp_OpenR then
        print("temp 文件已存在")
        temp_OpenR:close()
    else
        buildDirBliveCtrl() -- 创建配置文件所在文件夹
        local temp_OpenW, err = io.open(temp_Filepath, "w")
        if temp_OpenW then
            -- 一般情况下”w“模式的”io.open“会在目标文件不存在的时候将目标文件创建出来
            temp_OpenW:write('')
            temp_OpenW:close()
            print("temp 文件创建成功")
            if os_name == 'Linux' or os_name == 'macOS' then
                -- 只有Linux、macOS才能开放 temp 文件的权限
                command = 'chmod 777 \"' .. temp_Filepath .. '\"'
                print(command)
                local chmodpopen = io.popen(command)
                local chmodpopenall = chmodpopen:read('*a')
                print(chmodpopenall)
                chmodpopen:close()
            end -- 开放 temp 文件的权限
        else
            -- 尝试创建 temp 文件 如果是Linux、macOS则开放 temp 文件的权限
            print("无法创建 temp 文件:" .. err)
        end -- 没有temp 文件则 尝试创建 temp 文件
    end
end -- 创建 temp 文件
---[[写入 temp 文件]]]
---@type function
---@param temp_text string 要写入Temp文件的文本内容
---@return nil
local function writeTemp(temp_text)
    local temp_OpenW, err = io.open(temp_Filepath, "w") -- 以写入模式打开文件
    if temp_OpenW then
        temp_OpenW:write(temp_text)
        temp_OpenW:close()
        print("temp 文件写入成功")
    else
        print("无法打开 temp 文件:" .. err)
    end
end -- 写入 temp 文件
---[[输出文件第lineNUM行的内容]]]
---@type function
---@param filePath string 文件路径
---@param lineNUM number 文本行数
---@return string
local function showline(filePath, lineNUM)
    local lineshow
    local lineNumber = 0 -- 行号计数器
    for line in io.lines(filePath) do
        lineNumber = lineNumber + 1 -- 增加行号计数器
        if lineNumber == lineNUM then
            lineshow = line
        end
    end
    return lineshow
end
---[[[检查 参数文件]]]
---@type function
---@return boolean
local function isCookie()
    local cookieis = false
    --print('检查的 参数文件' .. bilibili_cookie_Filepath)
    -- 定义一个远程 URL
    local url = "www.baidu.com"
    -- 使用 ping 命令来检查是否可以访问该 URL
    local command
    if os_name == 'Windows' then
        command = "ping -n 1 " .. url  -- Windows系统下的命令
    else
         command = "ping -c 1 " .. url  -- Linux/Mac系统下的命令
    end
    -- 执行系统命令
    local result = os.execute(command)
    --print(result)
    -- 解析命令执行结果
    if result == 0 then
        local cookie_OpenR = io.open(bilibili_cookie_Filepath, "r")
        if cookie_OpenR then
            for cookie_OpenRine in cookie_OpenR:lines() do
                if string.find(cookie_OpenRine, '"cookie": "') and cookieis == false then
                    cookieis = true
                    --print("有 参数文件")
                end
            end
            cookie_OpenR:close()
        else
            print("无 参数文件")
        end
    end
    return cookieis
end -- 检查 参数文件
---[[[逐行打印 temp 文件内容]]]
---@type function
---@return nil
local function TempShowPrint()
    printTemp = temp
    local temp_OpenR = io.open(temp_Filepath, "r")
    if temp_OpenR then
        temp = temp_OpenR:read('*a')
        temp_OpenR:close()
        if temp ~= printTemp then
            temp_OpenR = io.open(temp_Filepath, "r")
            for templine in temp_OpenR:lines() do
                if templine:gsub("^[\n%s]*(.-)[\n%s]*$", "%1") == '{【[{timerShowTempValue}AUTO]OFF】}' then
                    obs.remove_current_callback()
                else
                    print(templine)
                end
            end
            temp_OpenR:close()
        end
    else
        BuildTemp()
    end
end -- 读取 temp 文件
---[[[创建一个钟每隔0.5秒将 temp文件内容输出到日志]]]
---@type function
---@param activating boolean
---@return nil
local function timerShowTempValue(activating)
    if timer_showtemp_value_activated == activating then
        return
    end
    timer_showtemp_value_activated = activating
    if activating then
        local firsttimer_showtemp_value = io.open(temp_Filepath, 'r')
        if firsttimer_showtemp_value then
            printTemp = firsttimer_showtemp_value:read('*a')
            temp = printTemp
            firsttimer_showtemp_value:close()
        else
            BuildTemp()
        end
        obs.timer_add(TempShowPrint, 300)
        print('showtemp_on')
    else
        obs.timer_remove(TempShowPrint)
        print('showtemp_off')
    end
end -- 创建一个钟每隔0.5秒将 temp文件内容输出到日志
---[[[table转list]]]
---@type function
---@param myTable table
---@return function list
local function list(myTable)
    return pairs(myTable)
end
---[[[table转str]]]
---@type function
---@param myTable table
---@return string
local function tableDumps(myTable)
    local endkey
    for key, value in pairs(myTable) do
        endkey = key
    end
    local myTableStr = '{'
    for key, value in pairs(myTable) do
        if type(key) == 'number' and key ~= endkey then
            myTableStr = myTableStr .. '[' .. key .. ']="' .. value .. '", '
        elseif type(key) ~= 'number' and key ~= endkey then
            myTableStr = myTableStr .. key .. '="' .. value .. '", '
        end
        if type(key) == 'number' and key == endkey then
            myTableStr = myTableStr .. '[' .. key .. ']="' .. value .. '"'
        elseif type(key) ~= 'number' and key == endkey then
            myTableStr = myTableStr .. key .. '="' .. value .. '"'
        end
    end
    myTableStr = myTableStr .. '}'
    return myTableStr
end
---[[[table格式的str转table]]]
---@type function
---@param myTableStr string
---@return table|boolean
local function tableLoads(myTableStr)
    local success, table = pcall(load("return " .. myTableStr))
    if success then
        return table
    else
        return success
    end
end
---[[[json格式的str转table]]]
---@type function
---@param str string
---@return table
local function json2table(str)
    local result = {}
    str = str:gsub("%s+", "") -- 去除空白字符
    str = str:sub(2, -2) -- 移除最外层的大括号
    for k, v in str:gmatch('"([^"]+)":"?([^",}]+)"?') do
        if v:sub(1, 1) == "{" then
            -- 处理嵌套的table
            result[k] = json2table(v)
        else
            result[k] = v
        end
    end
    return result
end
---[[[cookie格式的str转table]]]
---@type function
---@param cookieStr string
---@return table|boolean
local function cookieFormat2table(cookieStr)
    local result = {}
    for k, v in string.gmatch(cookieStr, "([^=;]+)=([^;]*)") do
        -- 对URL编码的值进行解码
        v = v:gsub('%%(%x%x)', function(hex)
            return string.char(tonumber(hex, 16))
        end)
        result[k:gsub("^[\n%s]*(.-)[\n%s]*$", "%1")] = v:gsub("^[\n%s]*(.-)[\n%s]*$", "%1")
    end
    return result
end
---[[[更新table]]]
---@type function
---@param myTable table 原始表
---@param addTable table 参考表
---@return table
local function tableUpdate(myTable, addTable)
    for key, value in pairs(addTable) do
        if type(key) == 'number' then
            table.insert(myTable, value)
        else
            myTable[key] = value
            table.insert(myTable, nil)
        end
    end
    return myTable
end
--- [[[解析Unicode转义序列]]]
---@type function
---@param s string U?????
---@return string
local function decodeUnicodeEscape(s)
    return (s:gsub("U([0-9A-Fa-f]+)", function(unicode)
        local codepoint = tonumber(unicode, 16)
        if codepoint <= 0x7F then
            return string.char(codepoint)
        elseif codepoint <= 0x7FF then
            return string.char(0xC0 + codepoint / 0x40, 0x80 + codepoint % 0x40)
        elseif codepoint <= 0xFFFF then
            return string.char(0xE0 + codepoint / 0x1000, 0x80 + codepoint / 0x40 % 0x40, 0x80 + codepoint % 0x40)
        elseif codepoint <= 0x10FFFF then
            return string.char(0xF0 + codepoint / 0x40000, 0x80 + codepoint / 0x1000 % 0x40, 0x80 + codepoint / 0x40 % 0x40, 0x80 + codepoint % 0x40)
        end
    end))
end

--- [[[解析Unicode转义序列]]]
---@type function
---\u?????
---@param s string
---@return string
local function decode_UnicodeEscape(s)
    return (s:gsub("\\u([0-9A-Fa-f]+)", function(unicode)
        local codepoint = tonumber(unicode, 16)
        if codepoint <= 0x7F then
            return string.char(codepoint)
        elseif codepoint <= 0x7FF then
            return string.char(0xC0 + codepoint / 0x40, 0x80 + codepoint % 0x40)
        elseif codepoint <= 0xFFFF then
            return string.char(0xE0 + codepoint / 0x1000, 0x80 + codepoint / 0x40 % 0x40, 0x80 + codepoint % 0x40)
        elseif codepoint <= 0x10FFFF then
            return string.char(0xF0 + codepoint / 0x40000, 0x80 + codepoint / 0x1000 % 0x40, 0x80 + codepoint / 0x40 % 0x40, 0x80 + codepoint % 0x40)
        end
    end))
end

--将 常规函数 归纳到 常规函数类 中
local fun_NORMAL = {}
---[[[获取操作系统类型]]]
---@type function
---@return string|boolean Windows|Linux|macOS||false
fun_NORMAL.getOSType = getOSType
---[[[创建配置文件所在文件夹]]]
---@type function
---@return nil
fun_NORMAL.buildDirBliveCtrl = buildDirBliveCtrl
---[[[创建 temp 文件]]]
---@type function
---@return nil
fun_NORMAL.BuildTemp = BuildTemp
---[[写入 temp 文件]]]
---@type function
---@param temp_text string 要写入Temp文件的文本内容
---@return nil
fun_NORMAL.writeTemp = writeTemp
---[[输出文件第lineNUM行的内容]]]
---@type function
---@param filePath string 文件路径
---@param lineNUM number 文本行数
---@return string
fun_NORMAL.showline = showline
---[[[检查 参数文件]]]
---@type function
---@return boolean
fun_NORMAL.isCookie = isCookie
---[[[逐行打印 temp 文件内容]]]
---@type function
---@return nil
fun_NORMAL.TempShowPrint = TempShowPrint
---[[[创建一个钟每隔0.5秒将 temp文件内容输出到日志]]]
---@type function
---@param activating boolean
---@return nil
fun_NORMAL.timerShowTempValue = timerShowTempValue
---[[[table转list]]]
---@type function
---@param myTable table
---@return function list
fun_NORMAL.list = list
---[[[table转str]]]
---@type function
---@param myTable table
---@return string
fun_NORMAL.json_Dumps = tableDumps
---[[[table格式的str转table]]]
---@type function
---@param myTableStr string
---@return table|boolean
fun_NORMAL.json_Loads = tableLoads
---[[[json格式的str转table]]]
---@type function
---@param str string
---@return table
fun_NORMAL.json2table = json2table
---[[[cookie格式的str转table]]]
---@type function
---@param cookieStr string
---@return table|boolean
fun_NORMAL.cookieFormat2dict = cookieFormat2table
---[[[更新table]]]
---@type function
---@param myTable table 原始表
---@param addTable table 参考表
---@return table
fun_NORMAL.dict_Update = tableUpdate
--- [[[解析Unicode转义序列]]]
---@type function
---@param s string U?????
---@return string
fun_NORMAL.decodeUnicodeEscape = decodeUnicodeEscape
--- [[[解析Unicode转义序列]]]
---@type function
---\u?????
---@param s string
---@return string
fun_NORMAL.decode_UnicodeEscape = decode_UnicodeEscape

--[[内部通用常量]]
--- 操作系统类型Windows、Linux、macOS
--local os_name = fun_NORMAL.getOSType()
local is_Cookie = fun_NORMAL.isCookie()
local devicesline = {}
devicesline.setting = 1
devicesline.edit = 2
devicesline.areav1id_areav1name = 3
devicesline.areav2id_areav2name = 4
devicesline.areav2id_areav1id = 5
timerShowTempValue(true)


--[[特殊常量]]
--- 所需python包
local NeedPythonPackages = { "qrcode", "requests", "aiohttp" }
fun_NORMAL.dict_Update(NeedPythonPackages, {})
--- obsScripts_BliveSettingPythonNeed.py 文件内容
local obsScripts_BliveSettingPythonNeed_text = ''

--[[正式插件]]
--- 设置默认值
function script_defaults(settings)
    obs.obs_data_set_string(settings, "cookie", '')
    fun_NORMAL.BuildTemp() -- 加载插件时创建BliveCtrl文件夹和temp文件
    if is_Cookie then
        local settingdevice = fun_NORMAL.showline(bilibili_cookie_Filepath, devicesline.setting)
        local settingdevicetable = fun_NORMAL.json2table(settingdevice)
        fun_NORMAL.writeTemp('{\"model\": \"updatacookie\", \"cookie\": \"' .. settingdevicetable.cookie .. '\"}')
        if os_name == 'Windows' then
            local command = 'python \"' .. BliveSettingPythonNeed_Filepath .. '\"'
            print(command)
            io.popen(command .. '')
        else
            local command = 'python3 \"' .. BliveSettingPythonNeed_Filepath .. '\"'
            print(command)
            io.popen(command .. '')
        end
    end
end
--- 一个名为script_description的函数返回显示给的描述
function script_description()
    local t = '<html lang="zh-CN"><body><pre>\
本插件基于python3\
    如果未安装python3，请前往\
        <a href="https://www.python.org/">python官网</a>\
        或者\
        <a href="https://python.p2hp.com/">python中文网 官网</a>下载安装\
        不同操作系统请查看\
            菜鸟教程<a href="https://www.runoob.com/python3/python3-install.html">Python3 环境搭建</a>\
<font color=yellow>!脚本路径中尽量不要有中文</font>\
<font color=green size=4>请在认为完成全部操作后点击<font color="white" size=5>⟳</font>重新载入插件</font>\
配置cookie：\
<font color=yellow>！请看着脚本日志操作</font>\
扫描配置cookie请 提前增加\
   脚本日志窗口 宽高\
手动配置cookie请前往\
   <a href="https://link.bilibili.com/p/center/index#/my-room/start-live">B站直播设置后台</a> 使用\
       浏览器的开发人员工具获取cookie<br>\
<font color="#ee4343">【cookie！为账号的{极重要}的隐私信息!】</font>\
<font color="#ee4343">【！请 不要泄露给他人!】</font>\
\
如果报错：\
   请关闭梯子和加速器\
   Windows请尝试使用管理员权限运行obs\
   其它系统请联系制作者<br></pre></body></html>'
    if not os_name then
        t = '<span style="color: red; ">不支持该系统</span>'
    end
    return t
end
--- 一个名为script_load的函数将在启动时调用
function script_load(settings)
    if os_name then
        local tl = '已载入：' .. LuaSelf_Filepath:match("[^/]*$") .. '\n'
        data = settings
        print(tl)
    end
end
--- 一个名为script_properties的函数定义了用户可以使用的属性
function script_properties()
    props = obs.obs_properties_create()
    --- 设置只读文本框
    ---@param props userdata 分组框对应的属性集
    ---@param name string 控件名称
    ---@param content string 内容
    ---@param type number obs.OBS_TEXT_INFO_NORMAL|obs.OBS_TEXT_INFO_WARNING
    local function setCookieInfo(props, name, content, type)
        --- 设置只读文本框所显示的内容
        obs.obs_data_set_string(data, name, content)
        obs.obs_properties_apply_settings(props, data)
        --- 设置只读文本框的信息类型
        obs.obs_property_text_set_info_type(obs.obs_properties_get(props, name), type)
    end
    if os_name then
        --- ## 创建 配置项 分组框对应的属性集
        setting_props = obs.obs_properties_create()
        --- ### 添加 配置项 分组框
        prop_group_setting = obs.obs_properties_add_group(props, 'group_setting', "配置项", obs.OBS_GROUP_NORMAL, setting_props)
        obs.obs_properties_add_text(setting_props, "cookie", "cookie", obs.OBS_TEXT_PASSWORD)
        obs.obs_properties_add_button(setting_props, "buildBliveSettingFile", "扫码/手动配置cookie", buildBliveSettingFile)
        obs.obs_properties_add_text(setting_props, "cookieInfo", "消息：", obs.OBS_TEXT_INFO)
        local settingdevice
        local settingKey
        local function is_setting()
            if not fun_NORMAL.isCookie() then
                return false
            end
            settingdevice = fun_NORMAL.showline(bilibili_cookie_Filepath, devicesline.setting)
            settingKey = { "cookie", 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'Expires', 'SESSDATA', 'buvid3', "uname", "uid", "room_id" }
            for k, v in fun_NORMAL.list(settingKey) do
                if not string.find(settingdevice, v) then
                    return false
                end
            end
            return true
        end
        if is_setting() then
            local settingdevicetable = fun_NORMAL.json2table(settingdevice)
            local connect
            if settingdevicetable.room_id ~= '0' then
                connect = "Hi! " .. settingdevicetable.uname .. '\n您的房间号为：' .. settingdevicetable.room_id
                setCookieInfo(props, 'cookieInfo', connect, obs.OBS_TEXT_INFO_NORMAL)
            else
                connect = "Hi! " .. settingdevicetable.uname .. '\n您未开通B站直播房间！'
                setCookieInfo(props, 'cookieInfo', connect, obs.OBS_TEXT_INFO_WARNING)
            end
        else
            local cookie_OpenR = io.open(bilibili_cookie_Filepath, "r")
            if cookie_OpenR then
                setCookieInfo(props, 'cookieInfo', '登录失败！请检查cookie或网络\n配置完成后重新载入脚本', obs.OBS_TEXT_INFO_WARNING)
            else
                setCookieInfo(props, 'cookieInfo', '未配置！请检查cookie或网络\n配置完成后重新载入脚本', obs.OBS_TEXT_INFO_WARNING)
            end
        end
        return props
    end
end

-- [[按钮事件]]
---配置cookie
function buildBliveSettingFile(props, p)
    local cookie = obs.obs_data_get_string(data, "cookie"):gsub("^[\n%s]*(.-)[\n%s]*$", "%1")
    local bilibili_cookie_Filepath_openW = io.open(bilibili_cookie_Filepath, 'w')
    bilibili_cookie_Filepath_openW:write('')
    bilibili_cookie_Filepath_openW:close()
    if cookie ~= '' then
        local cookie2dict = fun_NORMAL.cookieFormat2dict(cookie)
        local cookieKey = { 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'Expires', 'SESSDATA', 'buvid3' }
        local keyhavenum = 0
        for k, v in fun_NORMAL.list(cookie2dict) do
            k = k:gsub("^[\n%s]*(.-)[\n%s]*$", "%1")
            for ke, va in fun_NORMAL.list(cookieKey) do
                va = va:gsub("^[\n%s]*(.-)[\n%s]*$", "%1")
                if k == va then
                    keyhavenum = keyhavenum + 1
                end
            end
        end
        local cookieKeynum = 0
        for k, v in fun_NORMAL.list(cookieKey) do
            cookieKeynum = cookieKeynum + 1
        end
        if keyhavenum == cookieKeynum then
            bilibili_cookie_Filepath_openW = io.open(bilibili_cookie_Filepath, 'w')
            bilibili_cookie_Filepath_openW:write(cookie)
            bilibili_cookie_Filepath_openW:close()
        else
            print('手动配置的cookie有缺失字段')
            cookie = ''
        end
    end
    fun_NORMAL.writeTemp('{\"model\": \"updatacookie\", \"cookie\": \"' .. cookie .. '\"}')
    --timerShowTempValue(true)
    if os_name == 'Windows' then
        local command = 'python \"' .. BliveSettingPythonNeed_Filepath .. '\"'
        print(command)
        io.popen(command .. '')
    else
        local command = 'python3 \"' .. BliveSettingPythonNeed_Filepath .. '\"'
        print(command)
        io.popen(command .. '')
    end
end
