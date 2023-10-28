# 执行命令
import asyncio
import os
import re
import socket
import sys
import pandas as pd
import requests
import query_string
import yaml
from optparse import OptionParser
from pyutilb.module_loader import load_module_funs
from pyutilb.file import read_http_file, read_vars
from pyutilb.file import read_http_file
from pyutilb.log import log
from pyutilb.strs import substr_after_lines
from pyutilb.util import set_vars, custom_funs, extend_list

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
    optParser.add_option("-d", "--data", dest="data", type="string", help="Set variable data, eg: a=1&b=2")
    optParser.add_option("-D", "--dataurl", dest="dataurl", type="string", help="Set variable data from yaml/json url")
    optParser.add_option("-f", "--funs", dest="funs", type="string", help="Custom functions python file, eg: cf.py")
    # LocustBoot用到的参数
    optParser.add_option("-l", "--locustopt", dest="locustopt", type="string", help="Locust options in LocustBoot command, eg: '--headless -u 10 -r 5 -t 20s --csv=result --html=report.html'")
    # ui自动化测试项目用到的参数
    optParser.add_option("-c", "--autoclose", dest="autoclose", action="store_true", help="Auto close when finish or exception")
    # MonitorBoot用到的参数
    optParser.add_option("-t", "--runtime", dest="runtime", type="int", help="Stop after the specified amount of seconds")
    # K8sBoot/SparkBoot用到的参数
    optParser.add_option("-o", "--output", dest="output", type="string", help="Output directory for K8sBoot/SparkBoot generate file")
    # SparkBoot用到的参数
    optParser.add_option("-u", "--udf", dest="udf", type="string", help="Udf python file")

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
        set_vars(data)

    # 指定变量: 通过http url来指定, 该url返回yaml/json形式的变量
    if option.dataurl != None:
        data = read_vars(option.dataurl)
        log.debug(f"set variables: %s", data)
        set_vars(data)

    # 加载自定义函数
    if option.funs != None:
        funs = load_module_funs(option.funs)
        custom_funs.update(funs)

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

# 同步执行命令，并将输出转为yaml对象
def run_command_return_yaml(cmd):
    output = run_command(cmd)
    return yaml.load(output, Loader=yaml.FullLoader)

# 同步执行命令，并将输出整理为df
def run_command_return_dataframe(cmd, fix_output = None):
    output = run_command(cmd)
    # 有些输出不是规范的，如某列会有多个空格，需要调用者手动修复
    if fix_output:
        output = fix_output(output)
    return cmd_output2dataframe(output)

# 将命令扔到事件循环(的线程)中执行
def run_command_in_loop(cmd, shell = True, loop=None):
    task = run_command_async(cmd, shell, loop)
    return asyncio.run_coroutine_threadsafe(task, loop)

async def run_command_async(cmd, shell = True, wait_output = True):
    '''
    异步执行命令
        最好是在python3.9上执行，否则会遇到以下问题: Cannot add child handler, the child watcher does not have a loop attached
    :param cmd: 要执行的命令
    :param shell: 是否shell方式执行
    :param wait_output: 是否等待输出，不等待则立即返回，防止调用线程被阻塞
    :return:
    '''
    #log.debug(f'Run command: %s', cmd)
    # 1 执行命令
    if shell:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            #loop=loop, # python3.9以上不需要传递loop参数，否则报错 BaseSubprocessTransport.__init__() got multiple values for argument 'loop'
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
    else:
        args = cmd.split(" ")
        proc = await asyncio.create_subprocess_exec(
            *args,
            #loop=loop,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

    # 2 等待输出
    if not wait_output:
        return None

    stdout, stderr = await proc.communicate()

    log.debug(f'Run command `%s` exited with %s', cmd, proc.returncode) # returncode为0则成功, 否则失败
    # if stdout:
    #     log.debug(f'[stdout]\n%s', stdout.decode())
    if stderr:
        #log.debug(f'[stderr]\n%s', stderr.decode())
        raise Exception(f"Fail to run command `{cmd}`: \n{stderr.decode()}")

    return stdout.decode()

# 异步执行命令，并将输出整理为df
async def run_command_return_dataframe_async(cmd):
    output = await run_command_async(cmd)
    return cmd_output2dataframe(output)

# 根据grep模式来获得进程id
# :param grep 关键字，支持多个，用|分割
def get_pid_by_grep(grep):
    # 关键字，支持多个，用|分割
    # greps = grep.split('|')
    greps = re.split(r' *\| *', grep)
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
def split_by_space(line, maxsplit=0):
    ret = re.split("\s+", line.strip(), maxsplit)
    # 如果不足maxsplit，则补足
    extend_list(ret, maxsplit + 1 - len(ret))
    return ret

# 命令行输出转表格
# :param from_nline 从第几行开始
def cmd_output2dataframe(out, from_nline = 0):
    if from_nline > 0:
        out = substr_after_lines(out, from_nline)
    lines = out.strip().split("\n")
    # 表头行
    columns = split_by_space(lines[0])
    maxsplit = len(columns) - 1 # maxsplit = 列数 - 1
    # 数据行
    data = [split_by_space(line, maxsplit) for line in lines[1:]]
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

