#!/usr/bin/python3
# -*- coding: utf-8 -*-

import fnmatch
from pyutilb import log
from pyutilb.util import *

# 报告者：对测试进行统计+生成报告
class Reporter(object):

    def __init__(self):
        # 开始时间
        self.start_time = None
        # 结束时间
        self.end_time = None
        # 统计yaml文件、步骤、动作
        self.yamls = 0
        self.steps = 0
        self.actions = 0
        # 记录错误
        self.err = None

    def start(self):
        self.start_time = time.time()

    def end(self, err = None):
        self.end_time = time.time()
        self.err = err
        # 生成报告
        self.generate_report()

    def incr_yaml(self):
        self.yamls += 1

    def incr_step(self):
        self.steps += 1

    def incr_action(self):
        self.actions += 1

    # 生成报告
    # TODO: 后续生成html报告
    def generate_report(self):
        cost_time = self.end_time - self.start_time
        msg = f"-- Test report --\n耗时(s): {cost_time}\n" +\
            f"执行的yaml文件数: {self.yamls}\n" +\
            f"执行的步骤数: {self.steps}\n" +\
            f"执行的动作数: {self.actions}"
        # log.debug(msg)
        write_file('./report.txt', msg)
