#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
from pyutilb.util import *
from pyutilb.file import *

# 对测试进行统计
class Stat(object):

    def __init__(self):
        # 开始时间
        self.start_time = None
        # 结束时间
        self.end_time = None
        # 记录yaml文件
        self.yaml_tree = []
        self.yaml_levels = []  # 当前yaml节点的路径, 包含每一层的下标
        # 统计yaml文件、步骤、动作
        self.yamls = 0
        self.steps = 0
        self.actions = 0
        # 记录错误
        self.err = None
        # 结束后的变量
        self.vars = None

    @classmethod
    def start(cls):
        item = cls()
        item.start_time = datetime.datetime.now()
        return item

    def end(self, err = None):
        self.end_time = datetime.datetime.now()
        # 异常转str
        if isinstance(err, Exception):
            err = str(err)
        self.err = err
        # 记录变量, 要去掉不关心的变量
        self.vars = get_vars()
        if 'boot' in self.vars:
            del self.vars['boot']
        if 'response' in self.vars:
            del self.vars['response']
        # 将统计结果输出到 result.yml
        data = self.to_dict()
        ret = yaml.dump(data)
        write_file('stat.yml', ret)
        return self

    # 转字典
    def to_dict(self):
        data = self.__dict__
        if 'yaml_levels' in data:
            del data['yaml_levels']
        return data

    # 步骤数+1
    def incr_step(self):
        self.steps += 1
        return self

    # 动作数+1
    def incr_action(self):
        self.actions += 1
        return self

    # 开始执行一个yaml文件
    def enter_yaml(self, yaml):
        self.yamls += 1
        i = self._add_yaml_node(yaml)  # 记录yaml文件
        self.yaml_levels.append(i)  # 记录新层的下标
        return self

    # 结束执行一个yaml文件
    def exit_yaml(self):
        self.yaml_levels.pop()  # 干掉本层
        return self

    # 往yaml树中添加yaml节点
    def _add_yaml_node(self, yaml):
        # 找到当前层的子节点
        children = self.yaml_tree
        for idx in self.yaml_levels:
            children = children[idx]['children']
        # 添加
        children.append({'yaml': yaml, 'children': []})
        return len(children) - 1

    # 当前层yaml的路径
    def current_level_yamls(self):
        yamls = []
        children = self.yaml_tree
        for idx in self.yaml_levels:
            yamls.append(children[idx]['yaml'])
        return yamls

    # 最后一层yaml的路径
    def last_level_yamls(self):
        yamls = []
        children = self.yaml_tree
        while children:
            yamls.append(children[-1]['yaml'])
            children = children[-1]['children']
        return yamls