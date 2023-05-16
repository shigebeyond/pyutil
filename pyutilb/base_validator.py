#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from pyutilb.log import log

# 校验函数映射
validate_funcs = {
    '=': lambda val, param, ex: ex == None and str(val) == str(param), # val与param可能是int/float/string，而且两者类型可能不同，如val是int，param是字符串（通过第3种方式调用校验）
    '>': lambda val, param, ex: ex == None and float(val) > float(param),
    '<': lambda val, param, ex: ex == None and float(val) < float(param),
    '>=': lambda val, param, ex: ex == None and float(val) >= float(param),
    '<=': lambda val, param, ex: ex == None and float(val) <= float(param),
    'contains': lambda val, param, ex: ex == None and param in val,
    'startswith': lambda val, param, ex: ex == None and val.startswith(param),
    'endswith': lambda val, param, ex: ex == None and val.endswith(param),
    'regex_match': lambda val, param, ex: ex == None and re.search(param, val) != None,
    'exist': lambda val, param, ex: ex == None,
    'not_exist': lambda val, param, ex: ex != None,
}
func_names = '|'.join(validate_funcs.keys())
func_reg = rf'(.+) +({func_names})( +(.+))?$'

'''
校验器基类，处理通用的校验逻辑；
子类需实现 _get_val_by() 方法，几个boot框架用 ResponseWrap._get_val_by() 来实现；
校验器有以下几种调用形式：
    1. 两层字典： path: func: param
    validate_by_jsonpath:
      '$.data.goods_id':
         '>': 0 # 校验符号或函数: 校验的值, 即 id 元素的值>0
    2. 两层列表： - [path, func, param]
    validate_by_jsonpath:
      - ['$.data.goods_id', '>', 0]
    3. 字符串的列表： - 'path func param'
    validate_by_jsonpath:
      - '$.data.goods_id > 0'
'''
class BaseValidator(object):

    # 执行单个类型的校验
    def run_type(self, type, fields):
        # 1 两层字典
        if isinstance(fields, dict):
            for path, rules in fields.items():
                self.run_field(type, path, rules) # 校验单个字段
            return

        # 2 列表
        if isinstance(fields, list):
            for field in fields:
                if isinstance(field, list): # 2.1 两层列表
                    pass
                else: # 2.2 字符串的列表
                    field = self.parse_func_expr(field)
                self.run_field(type, field[0], field[1], field[2])  # 校验单个字段
            return

        raise Exception(f'Invalid validator fields: {fields}')

    # 解析函数表达式
    def parse_func_expr(self, expr):
        mat = re.match(func_reg, expr.strip())
        if mat == None:
            raise Exception("Mismatch validate function syntax: " + expr)

        path = mat.group(1)
        func = mat.group(2)
        val = mat.group(4)
        # print({
        #     'path': path,
        #     'func': func,
        #     'val': val,
        # })
        return [path, func, val]

    # 执行单个字段的校验
    def run_field(self, type, path, rules_or_func, param=None):
        # 1 获得字段值
        val = ex = None
        try:
            val = self._get_val_by(type, path)
        except Exception as e:
            ex = e

        # 2 执行校验函数
        # 2.1 rules_or_func 为字典类型的rules -- 多个函数
        if isinstance(rules_or_func, dict):
            # 逐个函数校验
            for func, param in rules_or_func.items():
                b = self.run_func(func, val, param, ex)
                if b == False:
                    raise AssertionError(f"Response element [{path}] not meet validate condition: {val} {func} '{param}'")
            return

        # 2.2 rules_or_func 为字符串类型的函数名 -- 单个函数
        func = rules_or_func
        b = self.run_func(func, val, param, ex)
        if b == False:
            raise AssertionError(f"Response element [{path}] not meet validate condition: {val} {func} '{param}'")

    '''
    执行单个函数：就是调用函数
    :param func 函数名
    :param val 校验的值
    :param param 参数
    :param ex 查找元素异常
    '''
    def run_func(self, func, val, param, ex):
        if func not in validate_funcs:
            raise Exception(f'Invalid validate function: {func}')
        # 调用校验函数
        log.debug(f"Call validate function: %s(%s)", func, param)
        func = validate_funcs[func]
        return func(val, param, ex)

if __name__ == '__main__':
    v = BaseValidator()
    exprs = [
        '$.data.goods_id > 0',
        '//*[@id="root"]/div/main/div/article/div[1]/div/div/div/h2[1]/b > 0',
        '#root > div > main > div > article > div.Post-RichTextContainer > div > div > div > h2:nth-child(3) > b > 0',
        'main div.Post-RichTextContainer h2:nth-child(3)  b > 0',
        '$.data.goods_id contains xxx',
        '$.data.goods_id endswith xxx',
        '$.data.goods_id exist',
        '$.data.goods_id not_exist',
        "io.material.catalog:id/cat_demo_text = Hello world",
        "Timer > 2022-07-06 12:00:00",
        "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.widget.FrameLayout[2]/android.widget.LinearLayout contains 衬衫"
    ]
    for expr in exprs:
        r = v.parse_func_expr(expr)
        print(r)