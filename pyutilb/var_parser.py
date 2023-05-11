#!/usr/bin/python3
# -*- coding: utf-8 -*-

from pyutilb.log import log
from pyutilb.util import *
from pyutilb.file import *

'''
从boot yaml中解析出用到的变量名，以便给自动化测试平台使用；
特性：
   1. 支持解析各类变量表达式: $xxx、${yyy}、${zzz.name}、${kkk[name]}
   2. 支持对include文件递归解析变量
   3. 支持排除 set_vars 所设置的变量

不支持:
   1. 不处理动作 proc
   2. 不处理include的文件名中带变量
   3. 不处理 set_vars 之前就有的重名变量(可能从命令行传过来的的，恰好跟 set_vars 中的变量重名, 表示不应该排除)，建议 set_vars 中还是不要设置重名变量 
'''
class VarParser(object):

    def __init__(self):
        # 步骤文件所在的目录
        self.step_dir = None
        # 收集变量
        self.vars = set() # 所有用到的变量
        self.vars_set = set() # 设置过的变量
        # 收集include
        self.includes = set()

    # 执行单个步骤文件
    # :param step_file 步骤配置文件路径
    # :param include 是否inlude动作触发
    def parse_file(self, step_file, include=False):
        # 获得步骤文件的绝对路径
        if include:  # 补上绝对路径
            if not os.path.isabs(step_file):
                step_file = self.step_dir + os.sep + step_file
        else:  # 记录目录
            step_file = os.path.abspath(step_file)
            self.step_dir = os.path.dirname(step_file)
        # 读取文本内容
        txt = read_file(step_file)
        if txt == None:
            raise Exception(f"文件{step_file}内容为空, 请检查文件是否不存在或者文件带变量表达式(暂不支持)")
        # 将 # 的注释全干掉, 防止后续干扰, TODO 考虑""中带#的情况, 后面再说
        txt = re.sub(rf'#.*\n', '\n', txt)
        # 解析用到的变量
        vars = self.parse_vars(txt)
        self.vars |= vars
        log.debug(f"解析[%s]用到的变量: %s", step_file, vars)
        # 解析设置的变量
        steps = yaml.load(txt, Loader=yaml.FullLoader)
        vars_set = self.parse_vars_set(steps)
        self.vars_set |= vars_set
        log.debug(f"解析[%s]设置的变量: %s", step_file, vars_set)
        # 解析include
        includes = self.parse_includes(txt)
        if includes != None:
            # 先去重，因为后面要递归
            includes = includes - self.includes
            self.includes |= includes
            # 递归解析
            for file in includes:
                self.parse_file(file, True)
        if not include:
            log.debug("解析出用到的变量: %s", self.vars)
            log.debug("解析出设置的变量: %s", self.vars_set)
            log.debug("解析出include文件: %s", self.includes)
            return self.vars - self.vars_set

    # 从yaml文本中解析变量表达式
    def parse_vars(self, txt):
        # 所有参数表达式的正则，不包含函数表达式
        # 正则不要包含分组, 否则只能findall到分组匹配的结果
        reg_var = f'\${reg_var_pure}' # 简单变量, 如 $xxx
        reg_complex = '\$\{[^\}]+\}' # 复杂变量, 如 ${xxx.name}
        reg_exprs = [reg_var, reg_complex]
        # 匹配
        ret = set()
        for reg in reg_exprs:
            exprs = re.findall(rf'{reg}', txt) # 无分组返回整体的list, 有1个分组返回该分组的list, 有2个以上分组返回tuple(多分组)的list
            for expr in exprs:
                var = self.parse_var(expr)
                if var != None:
                    ret.add(var)
        return ret

    # 解析单个变量
    def parse_var(self, expr):
        # 所有参数表达式的正则，不包含函数表达式
        reg_exprs = [reg_var, reg_props, reg_df_prop]
        # 匹配
        for reg in reg_exprs:
            mat = re.match(rf'{reg}', expr)
            if mat:
                # 匹配变量的位置，详见具体表达式
                if reg == reg_var:
                    ivar = 1
                else:
                    ivar = 2
                # 找到变量
                return mat.group(ivar)

        return None

    # 从yaml文本中解析设置过的变量
    def parse_vars_set(self, steps):
        ret = set()
        for step in steps:
            for action, param in step.items():
                if action == 'set_vars':
                    ret |= param.keys()
                elif action.startswith('for'):
                    log.debug("处理for")
                    ret |= self.parse_vars_set(param)
        return ret

    # 从yaml文本中解析include的文件
    def parse_includes(self, txt):
        reg = r"include\s*:([^#\n]+)"
        exprs = re.findall(reg, txt) # 无分组返回整体的list, 有1个分组返回该分组的list, 有2个以上分组返回tuple(多分组)的list
        # 不能用yield, 因为要2轮迭代, 而yield只能迭代一轮
        return set(map(lambda expr: expr.strip(' '), exprs)) # 去掉两头的空格

if __name__ == '__main__':
    '''
    变量表达式如
    xxx: $xxx
    yyy: ${yyy}
    zzz: ${zzz.name}
    kkk: ${kkk[name]}
    '''
    step_file = '/home/shi/code/python/AppiumBoot/example/step-sk.yml'
    vp = VarParser()
    vars = vp.parse_file(step_file)
    print(vars)
