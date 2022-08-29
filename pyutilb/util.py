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
import requests
from optparse import OptionParser
import query_string
from pyutilb.module_loader import load_module_funs

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
    # return res.content.decode("utf-8")
    return res.text

# 读yaml配置
# :param yaml_file (步骤配置的)yaml文件，支持本地文件与http文件
def read_yaml(yaml_file):
    txt = read_local_or_http_file(yaml_file)
    return yaml.load(txt, Loader=yaml.FullLoader)

# 读yaml配置
# :param json_file (步骤配置的)json文件，支持本地文件与http文件
def read_json(json_file):
    txt = read_local_or_http_file(json_file)
    return json.loads(txt)

# 本地文件或http文件
def read_local_or_http_file(file):
    if file.startswith('https://') or file.startswith('http://'):
        txt = read_http_file(file)
    else:
        if not os.path.exists(file):
            raise Exception(f"没找到文件: {file}")
        txt = read_file(file)
    return txt


# 输出异常
def print_exception(ex):
    print('\033[31m发生异常: ' + str(ex) + '\033[0m')

# 生成一个指定长度的随机字符串
def random_str(n):
    n = int(n)
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
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

# 自增的值
incr_vals = {}

# 自增值，从1开始
def incr(key):
    if key not in incr_vals:
        incr_vals[key] = 0
    incr_vals[key] = incr_vals[key] + 1
    return incr_vals[key]

# 变量
bvars = {}

# 设置变量
def set_var(name, val):
    bvars[name] = val

# 获取变量
# :param name 变量名
# :param throw_key_exception 当变量不存在，是否抛异常
def get_var(name, throw_key_exception = True):
    if name not in bvars:
        if throw_key_exception:
            raise Exception(f'不存在变量: {name}')
        return None

    return bvars[name]

# 替换变量： 将 $变量名 或 ${变量表达式} 替换为 变量值
# :param txt 兼容基础类型+字符串+列表+字典等类型, 如果是字符串, 则是带变量的表达式
# :param to_str 是否转为字符串, 否则原样返回, 可能是int/dict之类的, 主要是使用post动作的data是dict变量; 只针对整体匹配的情况
# :return
def replace_var(txt, to_str = True):
    # 如果是基础类型，直接返回
    if isinstance(txt, (int, float, complex, bool)):
        return txt

    # 如果是列表/元组/集合，则每个元素递归替换
    if isinstance(txt, (list, tuple, set)):
        return list(map(replace_var, txt))

    # 如果是字典，则每个元素递归替换
    if isinstance(txt, dict):
        for k, v in txt.items():
            txt[k] = replace_var(v)  # 替换变量
        return txt

    # 字符串：直接替换
    return do_replace_var(txt, to_str)

# 真正的替换变量: 将 $变量名 替换为 变量值
# :param txt 只能接收字符串
# :param txt 是否转为字符串, 否则原样返回, 可能是int/dict之类的, 主要是使用post动作的data是dict变量; 只针对整体匹配的情况
def do_replace_var(txt, to_str = True):
    if not isinstance(txt, str):
        raise Exception("变量表达式非字符串")

    # re正则匹配替换字符串 https://cloud.tencent.com/developer/article/1774589
    def replace(match, to_str = True) -> str:
        r = analyze_var_expr(match.group(1))
        if to_str: # 转字符串
            return str(r)
        return r # 原样返回, 可能是int/dict之类的, 主要是使用post动作的data是dict变量

    # 1 整体匹配: 整个是纯变量表达式
    mat1 = re.match(r'\$([\w\d_]+)', txt)
    mat2 = re.match(r'\$\{([\w\d_\.\(\)]+)\}', txt)
    if mat1 or mat2:
        if mat1:
            mat = mat1
        else:
            mat = mat2
        return replace(mat, to_str)

    # 2 局部匹配: 由 普通字符串 + 变量表达式 组成
    txt = re.sub(r'\$([\w\d_]+)', replace, txt)  # 处理变量 $msg
    txt = re.sub(r'\$\{([\w\d_\.\(\)]+)\}', replace, txt)  # 处理变量 ${data.msg} 或 函数调用 ${random_str(1)}
    return txt

# 解析变量表达式
# :param expr 变量表达式
# :return 表达式的值
def analyze_var_expr(expr):
    # 单独处理
    if '(' in expr:  # 函数调用, 如 random_str(1)
        r = parse_and_call_func(expr)
        return r

    if '.' in expr:  # 有多级属性, 如 data.msg
        return jsonpath(bvars, '$.' + expr)[0]

    return get_var(expr)


# 替换变量时用到的函数
# 系统函数
sys_funcs = {
    'random_str': random_str,
    'random_int': random_int,
    'incr': incr
}
# 自定义函数, 通过 -c 注入的外部python文件定义的函数
custom_funs = {}

# 解析并调用函数
def parse_and_call_func(expr):
    mat = re.match(r'([\w\d_]+)\((.+)\)', expr)
    if mat == None:
        raise Exception("不符合函数调用语法: " + expr)

    func = mat.group(1) # 函数名
    param = mat.group(2) # 函数参数

    return call_func(func, param)

# 调用函数
def call_func(name, param):
    if name in sys_funcs:
        func = sys_funcs[name]
    elif name in custom_funs:
        func = custom_funs[name]
    else:
        raise Exception(f'无效函数: {name}')
    # 调用函数
    return func(param)

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
    optParser.add_option("-f", "--f", dest="funs", type="string", help="set custom functions file, eg: cf.py")

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

    # 更新变量
    if option.data != None:
        data = query_string.parse(option.data)
        bvars.update(data)

    # 加载自定义函数
    if option.funs != None:
        global custom_funs
        custom_funs = load_module_funs(option.funs)

    # print(option)
    # print(args)
    return args

# 类型转by
def type2by(type):
    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        print('未安装selenium, 请不要使用方法 type2by()')

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

    raise Exception(f"不支持查找类型: {type}")
