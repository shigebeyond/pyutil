#!/usr/bin/python3
# -*- coding: utf-8 -*-

import fnmatch
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
        # 动作映射函数
        self.actions = {
            'sleep': self.sleep,
            'print': self.print,
            'for': self.do_for,
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
        # 当前文件
        self.step_file = None
        # 记录定义的过程, 通过 ~过程名 来定义, 通过 call:过程名 来调用
        self.procs = {}
        # 统计
        self.stat = Stat.start()

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

            self.stat.end()
            return self.stat
        except Exception as ex:
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
        log.debug(f"Load and run step file: {self.step_file}")

        # 记录yaml开始
        self.stat.enter_yaml(step_file)

        # 执行多个步骤
        self.run_steps(steps)

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
        steps = read_yaml(step_file)
        return steps

    # 执行多个步骤
    def run_steps(self, steps):
        # 逐个步骤调用多个动作
        for step in steps:
            self.stat.incr_step()  # 统计
            for action, param in step.items():
                self.stat.incr_action()  # 统计
                self.run_action(action, param)

    '''
    执行单个动作：就是调用动作名对应的函数
    :param action 动作名
    :param param 参数
    '''
    def run_action(self, action, param):
        log.debug(f"handle action: {action}={param}")
        if action[0] == '~':  # 定义过程
            action = f"proc({action[1:]})"

        has_other_arg = '(' in action # 是否有其他参数
        if has_other_arg: # 解析其他参数
            action, params = parse_func(action)
            n = params
            if len(params) == 1:
                n = params[0]
        if action not in self.actions:
            raise Exception(f'Invalid action: [{action}]')

        # 调用动作对应的函数
        func = self.actions[action]
        if has_other_arg: # 其他参数: 多加了个参数，如循环变量n
            func(param, n)
        else:
            func(param)

    # --------- 动作处理的函数 --------
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
        log.debug(f"-- Loop start: {label} -- ")
        last_i = get_var('for_i', False) # 旧的索引
        last_v = get_var('for_v', False) # 旧的元素
        try:
            for i in range(n):
                # i+1表示迭代次数比较容易理解
                log.debug(f"{i+1}th iteration")
                set_var('for_i', i+1) # 更新索引
                if n_null or items is None:
                    v = None
                else:
                    v = items[i]
                set_var('for_v', v) # 更新元素
                self.run_steps(steps)
        except BreakException as e:  # 跳出循环
            log.debug(f"-- Loop break: {label}, break condition: {e.condition} -- ")
        else:
            log.debug(f"-- Loop finish: {label} -- ")
        finally:
            set_var('for_i', last_i) # 恢复索引
            set_var('for_v', last_v) # 恢复元素

    # 执行一次子步骤，相当于 for(1)
    def once(self, steps):
        self.do_for(steps, 1)

    # 检查并继续for循环
    def moveon_if(self, expr):
        # break_if(条件取反)
        self.break_if(f"not ({expr})")

    # 跳出for循环
    def break_if(self, expr):
        val = eval(expr, globals(), get_vars())  # 丢失本地与全局变量, 如引用不了json模块
        if bool(val):
            raise BreakException(expr)

    # 加载并执行其他步骤文件
    def include(self, step_file):
        self.run_1file(step_file, True)

    # 设置变量
    def set_vars(self, vars):
        for k, v in vars.items():
            v = replace_var(v)  # 替换变量
            set_var(k, v)

    # 打印变量
    def print_vars(self, _):
        log.info(f"Variables: {get_vars()}")

    # 睡眠
    def sleep(self, seconds):
        seconds = replace_var(seconds)  # 替换变量
        time.sleep(int(seconds))

    # 打印
    def print(self, msg):
        msg = replace_var(msg)  # 替换变量
        log.debug(msg)

    # 执行命令
    def exec(self, cmd):
        output = os.popen(cmd).read()
        log.debug(f"execute commmand: {cmd} | result: {output}")

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