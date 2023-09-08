import json
import os
import re
from io import StringIO
import pandas as pd
import requests
import yaml
from dotenv import dotenv_values
from jsonpath import jsonpath

# 文件大小单位,相邻单位相差1024倍
file_size_units = "BKMGT";

# 文件大小单位换算为字节数
# @param unit
# @return int
def file_size_unit2bytes(unit):
    i = file_size_units.find(unit);
    if i == -1:
        raise Exception(f"无效文件大小单位: {unit}");
    return 1024.0 ** i

# 文件大小字符串换算为字节数
# @param sizeStr
# @return int
def file_size2bytes(sizeStr):
    size = int(sizeStr[:-1]) # 大小
    unit = sizeStr[-1] # 单位
    return size * file_size_unit2bytes(unit)

# 字节数换算为文件大小字符串
# @param bytes
# @param unit
# @return str
def bytes2file_size(bytes, unit, print_unit = True):
    size = bytes / file_size_unit2bytes(unit)
    size = '%.4f' % size
    if print_unit:
        return size + unit
    return size

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

# 读json文件
# :param json_file json文件，支持本地文件与http文件
def read_json(json_file):
    txt = read_local_or_http_file(json_file)
    return json.loads(txt)

# 读.env文件
# :param env_file env文件，支持本地文件与http文件
def read_env(env_file):
    #return dotenv_values(env_file) # 仅支持本地文件
    txt = read_local_or_http_file(env_file)
    return dotenv_values(stream=StringIO(txt))

# 读properties文件
# :param properties_file properties文件，支持本地文件与http文件
def read_properties(properties_file):
    return read_env(properties_file)

# 读csv文件
# :param csv_file csv文件，支持本地文件与http文件
# :return pd.DataFrame
def read_csv(csv_file):
    return pd.read_csv(csv_file)

# 读excel文件
# :param excel_file excel文件，支持本地文件与http文件
# :param sheet_name sheet名
# :return pd.DataFrame
def read_excel(excel_file, sheet_name):
    return pd.read_excel(excel_file, sheet_name)

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

# 读 __init__ 文件中的元数据：author/version/description
def read_init_file_meta(init_file):
    with open(init_file, 'rb') as f:
        text = f.read().decode('utf-8')
        items = re.findall(r'__(\w+)__ = "(.+)"', text)
        meta = dict(items)
        return meta

# 读本地或远端url返回的json/yaml形式的变量
def read_vars(url):
    #return read_yaml(option.dataurl)
    txt = read_http_file(url)
    if txt[0] == '{':
        return json.loads(txt)
    return yaml.load(txt, Loader=yaml.FullLoader)

if __name__ == '__main__':
    rows = read_csv('/home/shi/tk.csv')
    print(rows)
    for r in rows:
        print(r['uid'])
        print(jsonpath(r, '$.token'))
