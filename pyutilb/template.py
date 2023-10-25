from mako.template import Template

def render_mako(vars = None, **args):
    '''
    渲染模板
    :param vars: 模板参数
    :param args: mako Template构造函数参数
    :return:
    '''
    if vars is None:
        vars = {}
    # 定义模板
    mytemplate = Template(**args)
    # 渲染模板
    return mytemplate.render(**vars)

def render_text(txt, vars = None):
    '''
    渲染模板字符串
    :param txt: 模板字符串
    :param vars: 模板参数
    :return:
    '''
    return render_mako(vars, text = txt)

def render_file(file, vars = None):
    '''
    渲染模板文件
    :param file: 模板文件
    :param vars: 模板参数
    :return:
    '''
    return render_mako(vars, filename = file)

if __name__ == '__main__':
    tpl = '<title>${title}</title>'
    print(render_text(tpl, {'title': 'hero'}))