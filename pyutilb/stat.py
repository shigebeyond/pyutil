#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
from pyutilb.util import *

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

    def start(self):
        self.start_time = datetime.datetime.now()

    def end(self, err = None):
        self.end_time = datetime.datetime.now()
        self.err = err

    def incr_step(self):
        self.steps += 1

    def incr_action(self):
        self.actions += 1

    # 开始执行一个yaml文件
    def enter_yaml(self, yaml):
        self.yamls += 1
        i = self.add_yaml_node(yaml)  # 记录yaml文件
        self.yaml_levels.append(i)  # 记录新层的下标

    # 结束执行一个yaml文件
    def exit_yaml(self):
        self.yaml_levels.pop()  # 干掉本层

    # 往yaml树中添加yaml节点
    def add_yaml_node(self, yaml):
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
