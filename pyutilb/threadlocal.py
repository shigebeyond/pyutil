#!/usr/bin/python3
# -*- coding: utf-8 -*-

from threading import Thread, get_ident

# 仿java实现，让local支持默认值
class ThreadLocal(object):

    def __init__(self, default = None):
        '''
        构造函数
        :param default: 默认值，可能是函数
        '''
        self.locals = {}
        self.default = default

    # 设置local变量
    def set(self, value):
        ident = get_ident()
        self.locals[ident] = value

    # 获得local变量
    def get(self):
        ident = get_ident()
        if ident not in self.locals:
            self.locals[ident] = self._get_default_val()
        return self.locals[ident]

    # 构造默认值
    def _get_default_val(self):
        if callable(self.default):
            return self.default()
        return self.default


if __name__ == '__main__':
    num = ThreadLocal()
    print(num.get())
    def task(arg):
        num.set(arg)
        print(num.get())
    for i in range(10):
        t = Thread(target=task, args=(i,))
        t.start()