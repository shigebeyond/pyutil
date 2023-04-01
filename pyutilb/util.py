#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import yaml
import re
import os
import sys
import random
import json
from jsonpath import jsonpath
import csv
import requests
from optparse import OptionParser
import query_string
from pyutilb.threadlocal import ThreadLocal
from pyutilb.module_loader import load_module_funs
import pandas as pd
import threading

# -------------------- 读写文件 ----------------------
# 写文本文件
def write_file(path, content, append = False):
    if append:
        mode = 'a'
    else:
        mode = 'w'
    with open(path, mode, encoding="utf-8") as file:
        file.write(content)

# 读文本文件
def read_file(path):
    with open(path, 'r', encoding="utf-8") as file:
        return file.read()

# 写二进制文件
def write_byte_file(path, content, append = False):
    if append:
        mode = 'ab'
    else:
        mode = 'wb'
    with open(path, mode) as file:
        file.write(content)

# 读二进制文件
def read_byte_file(path):
    with open(path, 'rb') as file:
        return file.read()

# 读http文件内容
def read_http_file(url):
    res = requests.get(url)
    if res.status_code == 404:
        raise Exception(f"Remote file not exist: {url}")
    if res.status_code != 200:
        raise Exception(f"Fail to read remote file: {url} ")
    # return res.content.decode("utf-8")
    return res.text

# 读yaml文件
# :param yaml_file yaml文件，支持本地文件与http文件
def read_yaml(yaml_file):
    txt = read_local_or_http_file(yaml_file)
    return yaml.load(txt, Loader=yaml.FullLoader)

# 读yaml文件
# :param json_file json文件，支持本地文件与http文件
def read_json(json_file):
    txt = read_local_or_http_file(json_file)
    return json.loads(txt)

# 读csv文件
# :param csv_file csv文件，支持本地文件与http文件
# :return pd.DataFrame
def read_csv(csv_file):
    return pd.read_csv(csv_file)

# 是否是http文件
def is_http_file(file):
    return file.startswith('https://') or file.startswith('http://')

# 本地文件或http文件
def read_local_or_http_file(file):
    if is_http_file(file):
        txt = read_http_file(file)
    else:
        if not os.path.exists(file):
            raise Exception(f"File not exist: {file}")
        txt = read_file(file)
    return txt

# 输出异常
def print_exception(ex):
    print('\033[31mException occurs: ' + str(ex) + '\033[0m')

# -------------------- 变量读写+表达式解析与执行 ----------------------
# 变量: vars
vars = ThreadLocal(lambda : {})

# 设置变量
def set_var(name, val):
    get_vars()[name] = val

# 获取全部变量
def get_vars():
    return vars.get()

# 获取单个变量
# :param name 变量名
# :param throw_key_exception 当变量不存在，是否抛异常
def get_var(name, throw_key_exception = True):
    if name not in get_vars():
        if throw_key_exception:
            raise Exception(f'Variable not exist: {name}')
        return None

    return get_vars()[name]

# -------------------- 系统函数 ----------------------
base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
# 生成一个指定长度的随机字符串
def random_str(n):
    n = int(n)
    random_str = ''
    length = len(base_str) - 1
    for i in range(n):
        random_str += base_str[random.randint(0, length)]
    return random_str

# 生成一个指定长度的随机数字
def random_int(n):
    n = int(n)
    random_str = ''
    for i in range(n):
        random_str += str(random.randint(0, 9))
    return random_str

# 从list变量中随机挑选一个元素
def random_element(var):
    items = get_var(var)
    if isinstance(items, list, tuple, set, range):
        raise Exception('Param in random_element(param) must be list/tuple/set/range/range type')
    return random.choice(items)

# 自增的值
incr_vals = {}

# 自增值，从1开始
def incr(key):
    if key not in incr_vals:
        incr_vals[key] = 0
    incr_vals[key] = incr_vals[key] + 1
    return incr_vals[key]

# 获得list变量长度
def get_len(var):
    items = get_var(var)
    if items == None:
        return 0
    return len(items)

# -------------------- ExcelBoot用到的系统函数 ----------------------
# 添加sheet链接
# https://www.cnblogs.com/pythonwl/p/14363360.html
def link_sheet(sheet, label=None):
    if label == None:
        label = sheet
    return f'=HYPERLINK("#{sheet}!B2", "{label}")'

# 添加链接
def link(label, url):
    return f'=HYPERLINK("{url}", "{label}")'

# -------------------- 表达式解析与执行 ----------------------
# 替换变量： 将 $变量名 或 ${变量表达式} 替换为 变量值
# :param txt 兼容基础类型+字符串+列表+字典等类型, 如果是字符串, 则是带变量的表达式
# :param to_str 是否转为字符串, 否则原样返回, 可能是int/dict之类的, 主要是使用post动作的data是dict变量; 只针对整体匹配的情况
# :return
def replace_var(txt, to_str = True):
    # 如果是基础类型，直接返回
    if isinstance(txt, (int, float, complex, bool)):
        return txt

    # 如果是列表/元组/集合，则每个元素递归替换
    if isinstance(txt, (list, tuple, set, range)):
        return list(map(replace_var, txt))

    # 如果是字典，则每个元素递归替换
    if isinstance(txt, dict):
        txt = txt.copy() # 要拷贝, 不能直接改原来的参数值, 否则在for中循环调用同一个动作时, 该动作的参数只能替换一次变量
        for k, v in txt.items():
            txt[k] = replace_var(v)  # 替换变量
        return txt

    # 字符串：直接替换
    return do_replace_var(txt, to_str)

# 中文正则: \u4e00-\u9fa5
# 属性正则
reg_prop_pure = '[\w\d_\u4e00-\u9fa5]+'
# 变量的正则
reg_var_pure = '[\w\d_]+'
# 简单变量, 如 $xxx
reg_var = f'\$({reg_var_pure})'
# 表达式正则: 需兼容 random_str(1) / data.msg / df[name]
# reg_expr = '\$\{([\w\d_,\.\(\)\[\]\u4e00-\u9fa5]+)\}' # 太多情况不能匹配, 因为参数值可能各种各样字符都有
# 函数调用的正则: 如 random_str(1)
reg_func_pure = '([\w\d_]+)\((.*)\)'
reg_func = '\$\{(' + reg_func_pure + ')\}'
# 多级属性的正则: 如 data.msg
reg_props = '\$\{(' + f'({reg_var_pure})(\.{reg_prop_pure})*' + ')\}'
# df属性的正则: 如 df[name]
reg_df_prop = '\$\{(' + f'({reg_var_pure})\[{reg_prop_pure}\]' + ')\}'
# 所有的表达式正则
reg_exprs = [reg_var, reg_func, reg_props, reg_df_prop]

# re正则匹配替换纯变量表达式
# https://cloud.tencent.com/developer/article/1774589
def replace_pure_var_expr(match, to_str = True) -> str:
    r = analyze_var_expr(match.group(1))
    if to_str: # 转字符串
        return str(r)
    return r # 原样返回, 可能是int/dict之类的, 主要是使用post动作的data是dict变量

# 真正的替换变量: 将 $变量名 替换为 变量值
# :param txt 只能接收字符串
# :param txt 是否转为字符串, 否则原样返回, 可能是int/dict之类的, 主要是使用post动作的data是dict变量; 只针对整体匹配的情况
# :param replace 正则替换函数, 用于替换纯变量表达式
def do_replace_var(txt, to_str = True, replace = replace_pure_var_expr):
    if txt == None:
        return ''

    if not isinstance(txt, str):
        raise Exception("Variable expression is not a string")

    if '$' not in txt: # 无需替换
        return txt

    # 1 整体匹配: 整个是纯变量表达式
    for reg in reg_exprs:
        mat = re.match(rf'{reg}', txt)
        if mat:
            return replace(mat, to_str)

    # 2 局部匹配: 由 普通字符串 + 变量表达式 组成
    # (?<!\\)\$ 表示 $ 前面不能是 \，也就是 \$ 是不替换参数的
    for reg in reg_exprs:
        txt = re.sub(rf'(?<!\\){reg}', replace, txt)  # 处理变量
    txt = re.sub(r'\\\$', '$', txt)  # 将 \$ 反转义为 $, jkmvc调用php controller时url有$
    return txt

# 解析变量表达式
# :param expr 变量表达式
# :return 表达式的值
def analyze_var_expr(expr):
    # 单独处理
    if '(' in expr:  # 函数调用, 如 random_str(1)
        return parse_and_call_func(expr)

    if '.' in expr:  # 有多级属性, 如 data.msg
        return jsonpath(get_vars(), '$.' + expr)[0]

    if '[' in expr:  # 有属性, 如 df[name]
        return parse_df_prop(expr)

    return get_var(expr)

# 解析pandas df字段表达式
def parse_df_prop(expr):
    mat = re.match(r'([\w\d_]+)\[(.+)\]', expr)
    if mat == None:
        raise Exception("Mismatch [] syntax: " + expr)

    var = mat.group(1)  # df变量
    prop = mat.group(2)  # 属性名
    val = get_vars()[var]
    if not isinstance(val, pd.DataFrame):
        raise Exception(f"变量[{var}]值不是DataFrame: {val}")
    return val[prop]

# -------------------- 函数解析与调用 ----------------------
# 替换变量时用到的函数
# 系统函数
sys_funcs = {
    'random_str': random_str,
    'random_int': random_int,
    'random_element': random_element,
    'incr': incr,
    'len': get_len,
    'link': link,
    'link_sheet': link_sheet,
}
# 自定义函数, 通过 -c 注入的外部python文件定义的函数
custom_funs = {}

# 解析并调用函数
def parse_and_call_func(expr):
    func, params = parse_func(expr)
    return call_func(func, params)

# 解析函数与参数
def parse_func(expr):
    mat = re.match(rf'{reg_func_pure}', expr)
    if mat == None:
        raise Exception("Mismatch function call syntax: " + expr)

    func = mat.group(1)  # 函数名
    param = mat.group(2)  # 函数参数
    params = split_param(param)
    return func, params

# 用,分割参数
def split_param(param):
    # return param.split(',')

    # 处理某个参数中包含\,的情况 + 逗号后有空格
    params = re.split(r'(?<!\\),\s*', param)
    for i in range(0, len(params)):
        params[i] = params[i].replace('\,', ',')
    return params


# 调用函数
def call_func(name, params):
    if name in sys_funcs:
        func = sys_funcs[name]
    elif name in custom_funs:
        func = custom_funs[name]
    else:
        raise Exception(f'Invalid function: {name}')
    # 调用函数
    return func(*params)

# -------------------- selenium/appium用到的函数 ----------------------
# 分离xpath与属性
def split_xpath_and_prop(path):
    # 检查xpath是否最后有属性
    mat = re.search('/@[\w\d_-]+$', path)
    prop = ''
    if (mat != None):  # 有属性
        # 分离元素path+属性
        prop = mat.group()
        path = path.replace(prop, '')
        prop = prop.replace('/@', '')
    return path, prop

# 分离css选择器与属性, 如 a::attr(href)
def split_css_and_prop(path):
    # 检查css选择器是否最后有属性
    mat = re.search('::attr\(([\w\d_-]+)\)$', path)
    prop = ''
    if (mat != None):  # 有属性
        # 分离元素css选择器+属性
        path = path.replace(mat.group(), '')
        prop = mat.group(1)
    return path, prop

# 类型转by
def type2by(type):
    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        print('Selenium libary is not installed, please do not use type2by() method')

    if type == 'id':
        return By.ID
    if type == 'name':
        return By.NAME
    if type == 'css':
        return By.CSS_SELECTOR
    if type == 'xpath':
        return By.XPATH
    if type == 'tag':
        return By.TAG_NAME
    if type == 'link_text': # 精确匹配<a>的全部文本
        return By.LINK_TEXT
    if type == 'partial_link_text': # 匹配<a>的部分文本
        return By.PARTIAL_LINK_TEXT
    # app
    if type == 'aid':
        return By.ACCESSIBILITY_ID
    if type == 'class':
        return By.CLASS_NAME

    raise Exception(f"Invalid find type: {type}")

# -------------------- 命令解析 ----------------------
# 读 __init__ 文件中的元数据：author/version/description
def read_init_file_meta(init_file):
    with open(init_file, 'rb') as f:
        text = f.read().decode('utf-8')
        items = re.findall(r'__(\w+)__ = "(.+)"', text)
        meta = dict(items)
        return meta

# 解析命令的选项与参数
# :param name 命令名
# :param version 版本
# :return 命令参数
def parse_cmd(name, version):
    # py文件外的参数
    args = sys.argv[1:]

    usage = f'Usage: {name} [options...] <yaml_file1> <yaml_file2> <yaml_dir1> <yaml_dir2> ...'
    optParser = OptionParser(usage)

    # 添加选项规则
    # optParser.add_option("-h", "--help", dest="help", action="store_true") # 默认自带help
    optParser.add_option('-v', '--version', dest='version', action="store_true", help = 'Show version number and quit')
    optParser.add_option("-d", "--data", dest="data", type="string", help="set variable data, eg: a=1&b=2")
    optParser.add_option("-D", "--dataurl", dest="dataurl", type="string", help="set variable data from yaml url")
    optParser.add_option("-f", "--funs", dest="funs", type="string", help="set custom functions file, eg: cf.py")
    optParser.add_option("-l", "--locustopt", dest="locustopt", type="string", help="locust options, eg: '--headless -u 10 -r 5 -t 20s --csv=result --html=report.html'")

    # 解析选项
    option, args = optParser.parse_args(args)

    # 输出帮助文档 -- 默认自带help
    # if option.help == True:
    #     print(usage)
    #     sys.exit(1)

    # 输出版本
    if option.version == True:
        print(version)
        sys.exit(1)

    # 更新变量: 直接指定
    if option.data != None:
        data = query_string.parse(option.data)
        get_vars().update(data)

    # 更新变量: 通过yaml url来指定, 该url返回变量的yaml
    if option.dataurl != None:
        data = read_yaml(option.dataurl)
        get_vars().update(data)

    # 加载自定义函数
    if option.funs != None:
        global custom_funs
        custom_funs = load_module_funs(option.funs)

    # print(option)
    # print(args)
    return args, option

# 抓取pypi.org上指定项目的版本
def fetch_pypi_project_version(project):
    html = read_http_file(f"https://pypi.org/project/{project}")
    # mat = re.search('<h1 class="package-header__name">(.+)</h1>', html)
    mat = re.search(f'package-header__name">\s*{project} ([\d\.]+)', html)
    if mat == None:
        return None
    return mat.group(1)

# 解析范围表达式，如[1,3]
def parse_range(str):
    # 找到范围表达式，如[1,3]
    mat = re.search(r'\[(\d+):(\d+)\]', str)
    if mat == None:
        raise Exception("r没有范围表达式")
    range_exp = mat.group()
    start = int(mat.group(1))
    end = int(mat.group(2))
    if end < start:
        raise Exception("r范围表达式错误，结束值应该大于等于初始值")
    return start, end, range_exp

# 迭代范围表达式，如将 a[1,3].html 转变为迭代器，包含 a1.html a2.html a3.html
# :param str 范围字符串
# :param zfill_width 填充0的长度, 如对1要转为01
def iterate_range_str(range_str, zfill_width = None):
    start, end, range_exp = parse_range(range_str)
    for i in range(start, end + 1):
        it = str(i)
        if zfill_width != None: # 按长度补0
            it = it.zfill(int(zfill_width))
        yield range_str.replace(range_exp, it)

if __name__ == '__main__':
    '''
    set_var('name', 'shi')
    set_var('age', 1)
    print(parse_and_call_func('random_int(3)'))
    print(parse_and_call_func('link_sheet(目录,返回目录)'))
    print(do_replace_var('${random_int(3)}'))
    print(do_replace_var('${link_sheet(目录,返回目录)}'))
    print(do_replace_var('hello, ${name}'))
    print(do_replace_var('$name'))
    '''
    '''
    rows = read_csv('/home/shi/tk.csv')
    print(rows)
    for r in rows:
        print(r['uid'])
        print(jsonpath(r, '$.token'))
   '''
    project = 'AppiumBoot'
    version = fetch_pypi_project_version(project)
    print(f"{project} = {version}")