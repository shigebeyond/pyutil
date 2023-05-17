#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyutilb.log import log
from pyutilb.util import *

'''
抽取器基类，处理通用的抽取变量逻辑；
子类需实现 _get_val_by() 方法，几个boot框架用 ResponseWrap._get_val_by() 来实现；
'''
class BaseExtractor(object):

    # 执行单个类型的抽取
    def run_type(self, type, fields):
        for var, path in fields.items():
            # 获得字段值
            if type == 'eval':
                val = eval(path, globals(), get_vars()) # 丢失本地与全局变量, 如引用不了json模块
            else:
                val = self._get_val_by(type, path)
            # 抽取单个字段
            set_var(var, val)
            log.debug(f"Extract variable from response: %s=%s", var, val)
