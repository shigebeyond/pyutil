#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio
import fnmatch
import time

from pyutilb.cmd import run_command
from pyutilb.log import log
from pyutilb.util import *
from pyutilb.file import *
from pyutilb.stat import Stat

# 跳出循环的异常
class BreakException(Exception):
    def __init__(self, condition):
        self.condition = condition # 跳转条件

# 基于yaml的启动器
class YamlBoot(object):

    def __init__(self):
        # 步骤文件所在的目录
        self.step_dir = None
        # 步骤文件所在的目录作为当前目录，主要用在K8sBoot项目的步骤文件执行过程中调用 read_file() 时应用为当前目录
        self.step_dir_as_cwd = False
        # 当前文件
        self.step_file = None
        # 步骤文的缓存, 用于减少文件读IO, 如果你想读文件缓存, 请调用use_file_cache(True), 如LocustBoot压测时可能会频繁include步骤文件
        self.step_file_cache = None
        # 动作映射函数
        self.actions = {
            'exit': exit,
            'debug': self.set_debug,
            'sleep': self.sleep,
            'print': self.print,
            'log_level': self.log_level,
            'for': self.do_for,
            'if': self.do_if,
            'else': self.do_else,
            'once': self.once,
            'break_if': self.break_if,
            'moveon_if': self.moveon_if,
            'include': self.include,
            'set_vars': self.set_vars,
            'print_vars': self.print_vars,
            'exec': self.exec,
            'proc': self.proc,
            'call': self.call,
        }
        set_var('boot', self)
        # 记录定义的过程, 通过 ~过程名 来定义, 通过 call:过程名 来调用
        self.procs = {}
        # 统计
        self.stat = Stat.start()
        self.stat_dump = True # 是否需要输出统计结果到stat.yml，K8sBoot/SparkBoot项目不需要
        # 调试
        self.debug = False

    # 设置是否使用文件缓存, 一般用在LocustBoot, 其压测时可能会频繁include步骤文件
    def use_file_cache(self, cached):
        if cached:
            self.step_file_cache = {}
        else:
            self.step_file_cache = None

    # 添加单个动作
    def add_action(self, name: str, callback: str):
        self.actions[name] = callback

    # 添加多个动作
    def add_actions(self, actions: dict):
        self.actions = {**self.actions, **actions}

    # 执行完的后置处理, 要在统计扫尾前调用
    def on_end(self):
        pass

    '''
    执行入口
    :param step_files 步骤配置文件或目录的列表
    :param throwing 是否直接抛异常
    '''
    def run(self, step_files, throwing = True):
        try:
            # 真正的执行
            self.do_run(step_files)

            self.on_end() # 执行完的后置处理, 要在统计扫尾前调用

            if self.stat_dump:
                self.stat.end()
            return self.stat
        except Exception as ex:
            if self.stat_dump:
                self.stat.end(ex)
            if throwing:
                raise ex

    '''
    真正的执行入口
    :param step_files 步骤配置文件或目录的列表
    '''
    def do_run(self, step_files):
        for path in step_files:
            # 1 模式文件
            if '*' in path:
                dir, pattern = path.rsplit(os.sep, 1)  # 从后面分割，分割为目录+模式
                if not os.path.exists(dir):
                    raise Exception(f'Step config directory not exist: {dir}')
                self.run_1dir(dir, pattern)
                return

            # 2 不存在
            if (not is_http_file(path)) and not os.path.exists(path):
                raise Exception(f'Step config file or directory not exist: {path}')

            # 3 目录: 遍历执行子文件
            if os.path.isdir(path):
                self.run_1dir(path)
                return

            # 4 纯文件
            self.run_1file(path)

    # 执行单个步骤目录: 遍历执行子文件
    # :param path 目录
    # :param pattern 文件名模式
    def run_1dir(self, dir, pattern ='*.yml'):
        # 遍历目录: https://blog.csdn.net/allway2/article/details/124176562
        files = os.listdir(dir)
        files.sort() # 按文件名排序
        for file in files:
            if fnmatch.fnmatch(file, pattern): # 匹配文件名模式
                file = os.path.join(dir, file)
                if os.path.isfile(file):
                    self.run_1file(file)

    # 执行单个步骤文件
    # :param step_file 步骤配置文件路径
    # :param include 是否inlude动作触发
    def run_1file(self, step_file, include = False):
        # 加载步骤文件：会更新 self.step_dir 与 self.step_file
        steps = self.load_1file(step_file, include)
        log.debug(f"Load and run step file: %s", self.step_file)

        # 记录yaml开始
        self.stat.enter_yaml(step_file)

        # step_dir作为当前目录
        if self.step_dir_as_cwd:
            cur_dir = os.getcwd()
            os.chdir(self.step_dir)

        # 执行多个步骤
        self.run_steps(steps)

        # 恢复当前目录
        if self.step_dir_as_cwd:
            os.chdir(cur_dir)

        # 记录yaml结束
        self.stat.exit_yaml()

    # 加载单个步骤文件
    # 会更新 self.step_dir 与 self.step_file
    def load_1file(self, step_file, include):
        # 获得步骤文件的绝对路径
        if include:  # 补上绝对路径
            if (not is_http_file(step_file)) and not os.path.isabs(step_file):
                step_file = self.step_dir + os.sep + step_file
        else:  # 记录目录
            if is_http_file(step_file):
                i = step_file.rindex('/')
                self.step_dir = step_file[:i]
            else:
                step_file = os.path.abspath(step_file)
                self.step_dir = os.path.dirname(step_file)
        # 记录步骤文件
        self.step_file = step_file
        # 读取步骤
        return self.read_cached_step_file(step_file)

    # 有缓存的读步骤文件
    def read_cached_step_file(self, step_file):
        # 无缓存: 直接读文件
        if self.step_file_cache is None:
            return read_yaml(step_file)

        # 有缓存: 读缓存
        if step_file not in self.step_file_cache:
            self.step_file_cache[step_file] = read_yaml(step_file)
        return self.step_file_cache[step_file]

    # 执行多个步骤
    def run_steps(self, steps):
        # 逐个步骤调用多个动作
        for step in steps:
            self.stat.incr_step()  # 统计
            for action, param in step.items():
                self.check_if_else_pos(step)
                self.stat.incr_action()  # 统计
                self.run_action(action, param)

    '''
    执行单个动作：就是调用动作名对应的函数
    :param action 动作名
    :param param 参数
    :return 有返回值，以便处理协程方法
    '''
    def run_action(self, action, param):
        log.debug(f"handle action: %s=%s", action, param)
        if action[0] == '~':  # 定义过程
            action = f"proc({action[1:]})"

        # 解析其他参数
        args = []
        if '(' in action:
            action, args = parse_func(action)

        if action not in self.actions:
            raise Exception(f'Invalid action: [{action}]')

        # 调用动作对应的函数
        func = self.actions[action]
        return func(param, *args)

    # --------- 动作处理的函数 --------
    # 设置调试模式
    def set_debug(self, f):
        if f is None:
            f = True
        self.debug = f

    # 解析动作名for(n)中的n: 或数字或列表
    def parse_for_n(self, n):
        if n is None or n == '':
            return None

        # 1 数字
        if isinstance(n, int) or n.isdigit():
            return int(n)

        # 2 范围表达式，如[1,3]
        if ':' in n:
            start, end, _ = parse_range(n)
            return range(start, end + 1)

        # 3 变量表达式, 必须是int/list/df.Series类型
        expr = "${" + n + "}"
        n = replace_var(expr, False)

        # fix bug: pd.Series is None 居然返回pd.Series
        if self.is_pd_series(n):
            return n
        if n is None or not (isinstance(n, (list, tuple, set, range, int))):
            raise Exception(f'Variable in for({n}) parentheses must be int/list/tuple/set/range/pd.Series type')
        return n

    # 判断是否是pd.Series, 但不是所有boot项目都依赖pandas
    def is_pd_series(self, n):
        try:
            import pandas as pd
            return isinstance(n, pd.Series)
        except ImportError:
            return False

    # 执行一次的几率
    # 一般用在 LocustBoot 中控制多接口用例的吞吐量比例
    # :param steps 每个迭代中要执行的步骤
    # :param percent 几率百分比, 0~100的整数
    def probability(self, steps, percent = 0):
        percent = int(percent)
        if percent == 0:
            return

        # 如果随机数符合几率, 就执行子步骤; 否则不执行
        if random.randint(1, 100) <= percent:
            self.run_steps(steps)

    # for循环
    # :param steps 每个迭代中要执行的步骤
    # :param n 循环次数/循环列表变量名
    def do_for(self, steps, n = None):
        n = self.parse_for_n(n)
        label = f"for({n})"
        # 循环次数
        # fix bug: pd.Series == None 居然返回pd.Series
        n_null = (not self.is_pd_series(n)) and n is None
        if n_null:
            n = sys.maxsize # 最大int，等于无限循环次数
            label = f"for(∞)"
        # 循环的列表值
        items = None
        if isinstance(n, (list, tuple, set, range)) or self.is_pd_series(n):
            items = n
            n = len(items)
        log.debug(f"-- Loop start: %s -- ", label)
        last_i = get_var('for_i', False) # 旧的索引
        last_v = get_var('for_v', False) # 旧的元素
        try:
            for i in range(n):
                # i+1表示迭代次数比较容易理解
                log.debug(f"%sth iteration", i+1)
                set_var('for_i', i+1) # 更新索引
                if n_null or items is None:
                    v = None
                else:
                    v = items[i]
                set_var('for_v', v) # 更新元素
                self.run_steps(steps)
        except BreakException as e:  # 跳出循环
            log.debug(f"-- Loop break: %s, break condition: %s -- ", label, e.condition)
        else:
            log.debug(f"-- Loop finish: %s -- ", label)
        finally:
            set_var('for_i', last_i) # 恢复索引
            set_var('for_v', last_v) # 恢复元素

    # 执行一次子步骤，相当于 for(1)
    def once(self, steps):
        self.do_for(steps, 1)

    # if条件
    # :param steps 满足条件时要执行的步骤
    # :param expr 条件表达式
    def do_if(self, steps, expr):
        val = self.eval_condition(expr)
        if val:
            self.run_steps(steps)
        set_var('doing_else', not val)

    # else条件
    def do_else(self, steps):
        if get_var('doing_else'):
            self.run_steps(steps)
        set_var('doing_else', None)

    # 校验if/else位置：else必须处于if之后
    def check_if_else_pos(self, actions):
        if 'if' in actions and 'else' in actions:
            keys = list(actions.keys())
            last_if = -2 # 记录前一个if位置
            for i in keys:
                key = keys[i]
                if key == 'if':
                    last_if = i
                elif key == 'else':
                    if i == last_if + 1: # else必须处于if之后
                        last_if = -2
                    else:
                        raise Exception("else动作必须处于if动作之后")

    # 检查并继续for循环
    def moveon_if(self, expr):
        # break_if(条件取反)
        self.break_if(f"not ({expr})")

    # 跳出for循环
    def break_if(self, expr):
        if self.eval_condition(expr):
            raise BreakException(expr)

    # 执行条件表达式
    def eval_condition(self, expr):
        val = eval(expr, globals(), get_vars())  # 丢失本地与全局变量, 如引用不了json模块
        return bool(val)

    # 加载并执行其他步骤文件
    def include(self, step_file):
        self.run_1file(step_file, True)

    # 设置变量
    # :param to_str 是否转为字符串, 否则原样返回, 可能是int/dict之类的, 主要是使用post动作的data是dict变量; 只针对整体匹配的情况
    def set_vars(self, vars, to_str = True):
        if isinstance(to_str, str):
            to_str = to_str.lower() == 'true'
        for k, v in vars.items():
            v = replace_var(v, to_str)  # 替换变量
            set_var(k, v)

    # 打印变量
    def print_vars(self, _):
        log.info(f"Variables: %s", get_vars())

    # 睡眠
    def sleep(self, seconds):
        seconds = replace_var(seconds)  # 替换变量
        time.sleep(int(seconds))
        # await asyncio.sleep(int(seconds)) # 改为协程：整个调用栈都需要调整，当有迫切需求时才做

    # 打印
    def print(self, msg):
        msg = replace_var(msg)  # 替换变量
        log.debug(msg)

    # 设置日志等级
    def log_level(self, level):
        log.setLevel(level)

    # 执行命令
    def exec(self, cmd):
        output = run_command(cmd)
        log.debug(f"execute commmand: %s | result: %s", cmd, output)

    # 定义过程, 可包含多个子步骤
    # :param steps
    # :param name
    def proc(self, steps, name):
        if name is None or name.isspace():
            raise Exception("过程名不能为空")
        if steps is None:
            raise Exception("过程中子步骤不能为空")
        self.procs[name] = steps

    # 调用过程
    # :param config 过程名
    def call(self, name):
        if name not in self.procs:
            raise Exception("未定义函数")

        # 执行多个步骤
        steps = self.procs[name]
        self.run_steps(steps)