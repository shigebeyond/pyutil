# 动态加载py文件
import importlib
import sys
import types

# 判断是不是方法
def is_function(tup):
    """ Takes (name, object) tuple, returns True if it is a function.
    """
    name, item = tup
    return isinstance(item, types.FunctionType)

# 判断是不是类
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

def load_python_module(file_path):
    """ load python module.

    Args:
        file_path: python path

    Returns:
        dict: variables and functions mapping for specified python module

            {
                "variables": {},
                "functions": {}
            }

    """
    debugtalk_module = {
        "variables": {},
        "functions": {}
    }

    sys.path.insert(0, file_path)
    module = importlib.import_module("debugtalk")
    # 修复重载bug
    importlib.reload(module)
    sys.path.pop(0)

    for name, item in vars(module).items():
        if is_function((name, item)):
            debugtalk_module["functions"][name] = item
        elif is_variable((name, item)):
            if isinstance(item, tuple):
                continue
            debugtalk_module["variables"][name] = item
        else:
            pass

    return debugtalk_module

mod = load_python_module('debugtalk.py')
f = mod['functions']['test']
f()