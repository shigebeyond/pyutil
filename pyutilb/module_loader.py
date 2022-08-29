import importlib
import types

# 已加载的模块
_modules = {}

# 加载python模块中的函数
def load_module_funs(py_path):
    module = load_module(py_path)
    return filter_module_element(module, True)

# 加载python模块中的变量
def load_module_vars(py_path):
    module = load_module(py_path)
    return filter_module_element(module, False)

# 加载python模块
def load_module(py_path):
    if py_path not in _modules:
        _modules[py_path] = importlib.machinery.SourceFileLoader('module_name', py_path).load_module()
    return _modules[py_path]

# 过滤模块中的函数或变量
# :param module 模块
# :param is_fun 是否过滤函数
def filter_module_element(module, is_fun):
    if is_fun:
        filter_type = is_function
    else:
        filter_type = is_variable
    module_functions_dict = dict(filter(filter_type, vars(module).items()))
    return module_functions_dict

# 检查模块元素是否函数
def is_function(tup):
    """ Takes (name, object) tuple, returns True if it is a function.
    """
    name, item = tup
    return isinstance(item, types.FunctionType)

# 检查模块元素是否变量
def is_variable(tup):
    """ Takes (name, object) tuple, returns True if it is a variable.
    """
    name, item = tup
    if callable(item):
        # function or class
        return False

    if isinstance(item, types.ModuleType):
        # imported module
        return False

    if name.startswith("_"):
        # private property
        return False

    return True

# if __name__ == '__main__':
#     file = '/home/shi/code/python/pyutilb/tests/debugtalk.py'
#     funs = load_module_funs(file)
#     print(funs)
#     vars = load_module_vars(file)
#     print(vars)