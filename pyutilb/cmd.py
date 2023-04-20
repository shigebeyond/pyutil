# 执行命令
import asyncio
import os
import re
import socket
import sys

import pandas as pd
import requests
import query_string
from optparse import OptionParser
from pyutilb.module_loader import load_module_funs
from pyutilb.file import read_http_file, read_remote_vars
from pyutilb.log import log
from pyutilb.file import read_http_file
from pyutilb.log import log
from pyutilb.util import get_vars

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
    optParser.add_option("-D", "--dataurl", dest="dataurl", type="string", help="set variable data from yaml/json url")
    optParser.add_option("-f", "--funs", dest="funs", type="string", help="set custom functions file, eg: cf.py")
    optParser.add_option("-l", "--locustopt", dest="locustopt", type="string", help="locust options in LocustBoot command, eg: '--headless -u 10 -r 5 -t 20s --csv=result --html=report.html'")
    optParser.add_option("-c", "--autoclose", dest="autoclose", action="store_true", help="auto close when finish or exception")

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

    # 指定变量: 直接指定
    if option.data != None:
        data = query_string.parse(option.data)
        get_vars().update(data)

    # 指定变量: 通过http url来指定, 该url返回yaml/json形式的变量
    if option.dataurl != None:
        data = read_remote_vars(option.dataurl)
        log.debug(f"set variables: {data}")
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

# 同步执行命令
def run_command(cmd):
    return os.popen(cmd).read()

# 同步执行命令，并将输出整理为df
def run_command_return_dataframe(cmd):
    output = run_command(cmd)
    return cmd_output2dataframe(output)

# 异步执行命令
async def run_command_async(cmd, shell = True):
    #log.debug(f'Run command: {cmd}')
    if shell:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
    else:
        args = cmd.split(" ")
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    log.debug(f'Run command `{cmd}` exited with {proc.returncode}') # returncode为0则成功, 否则失败
    # if stdout:
    #     log.debug(f'[stdout]\n{stdout.decode()}')
    if stderr:
        #log.debug(f'[stderr]\n{stderr.decode()}')
        raise Exception(f"Fail to run command `{cmd}`: \n{stderr.decode()}")

    return stdout

# 异步执行命令，并将输出整理为df
async def run_command_return_dataframe_async(cmd):
    output = await run_command_async(cmd)
    return cmd_output2dataframe(output)

# 根据grep模式来获得进程id
def get_pid_by_grep(*greps):
    # 如 ps -ef | grep 'java' | grep 'com.jetbrains.www.pychar' | grep -v grep |awk '{print $2}'
    greps = [f"grep '{p}'" for p in greps]
    cmd = "ps -ef | " + ' | '.join(greps) + " | grep -v grep | awk '{print $2}'"
    # print(cmd)
    output = run_command(cmd).strip()
    if output:
        return output

    return None

# 根据端口获得进程id
def get_pid_by_port(port):
    # 如 tcp 0 0 0.0.0.0:8000 0.0.0.0:* LISTEN 26411/python3.10
    output = run_command(f'netstat -nlp|grep {port} |tr -s " "')
    # 匹配端口+pid
    mat = re.search(f':{port} .+LISTEN (\d+)/', output)
    if (mat != None):  # pid
        return mat.group(1)

    return None

# 获得ip
_ip = None
def get_ip():
    global _ip
    if _ip is None:
        st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            st.connect(('10.255.255.255', 1))
            _ip = st.getsockname()[0]
        except Exception:
            _ip = '127.0.0.1'
        finally:
            st.close()
    return _ip

# 根据空格来分割字符串
def split_by_space(line):
    return re.split("\s+", line.strip())

# 命令行输出转表格
def cmd_output2dataframe(out):
    lines = out.strip().split("\n")
    # 表头行
    columns = split_by_space(lines[0])
    # 数据行
    data = [split_by_space(line) for line in lines[1:]]
    return pd.DataFrame(data,columns=columns)

if __name__ == '__main__':
    '''
    project = 'AppiumBoot'
    version = fetch_pypi_project_version(project)
    print(f"{project} = {version}")
    '''
    '''
    pid = get_pid_by_port('8000')
    print(pid)
    pid = get_pid_by_grep(['java', 'com.jetbrains.www.pycharm'])
    print(pid)
    '''
    df = run_command_return_dataframe('jstat -gc  7061')
    print(df)
    print('------')
    print(dict(df.loc[0]))
    print('------')
    print(df.dtypes)
    print('------')
    for col in df.columns:
        # 将列类型转为float
        df[col] = df[col].astype(float)
    print(df.dtypes)

