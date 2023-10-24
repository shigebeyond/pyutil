from mako.template import Template
from pyutilb.util import get_vars, set_vars

def render(vars = None, **args):
    '''
    渲染模板
    :param vars: 变量，如果不指定则取 set_vars()设置的变量
    :param args: mako Template构造函数参数
    :return:
    '''
    # 获得变量
    if vars is None:
        vars = get_vars()
    # 定义模板
    mytemplate = Template(**args)
    # 渲染模板
    return mytemplate.render(**vars)

def render_text(txt, vars = None):
    '''
    渲染模板字符串
    :param txt: 模板字符串
    :param vars: 变量，如果不指定则取 set_vars()设置的变量
    :return:
    '''
    return render(vars, text = txt)

def render_file(file, vars = None):
    '''
    渲染模板文件
    :param file: 模板文件
    :param vars: 变量，如果不指定则取 set_vars()设置的变量
    :return:
    '''
    return render(vars, filename = file)

if __name__ == '__main__':
    tpl = '<title>${title}</title>'
    print(render_text(tpl, {'title': 'hero'}))

    set_vars({'title': 'hero'})
    print(render_text(tpl))