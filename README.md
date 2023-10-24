[GitHub](https://github.com/shigebeyond/pyutilb) | [Gitee](https://gitee.com/shigebeyond/pyutilb)

# pyutilb - 通用工具类代码
这是我平时积累的工具类，有以下几个模块

## 1. util: 通用方法
```
from pyutilb.util import *

# 变量存在ThreadLocal中，是线程安全的
# 写变量
set_var('name', 'shi')
# 读变量
v = get_var('name')
# 替换变量： 将 $变量名 或 ${变量表达式} 替换为 变量值
v = replace_var("hello $name")
````

## 3. file: 文件读写，如 `read_yaml()` 支持读取本地或http的yaml文件
```
from pyutilb.file import *

# 写文本文件
write_file(file, content, append = False)
# 读文本文件
data = read_file(file)
# 写二进制文件
write_byte_file(file, content, append = False)
# 读二进制文件
data = read_byte_file(file)
# 读远程文件
data = read_http_file(url)
# 本地或远程的文本文件
data = read_local_or_http_file(file)
# 读文本文件
data = read_yaml(yaml_file)
# 读json文件, 支持本地或远程文件
data = read_json(json_file)
# 用pandas读csv文件
data = read_csv(csv_file)
# 用pandas读excel文件
data = read_excel(excel_file, sheet_name)
# 读本地或远端url返回的json/yaml形式的变量
data = read_vars(url)
```

## 4. log: 通用日志
```
from pyutilb.log import log

log.info('hello world')
```

## 5. cmd: 同步或异步执行命令
```
from pyutilb.cmd import *

step_files, option = parse_cmd('AppiumBoot', meta['version'])
```

## 6. strs: 字符串操作
```
from pyutilb.strs import *

str = 'hello world'
print(substr_before(str, ' '))
print(substr_after(str, ' '))

output = '''Linux 5.10.60-amd64-desktop (shi-PC) 	2023年04月23日 	_x86_64_	(6 CPU)

11时28分27秒   UID      TGID       TID    %usr %system  %guest   %wait    %CPU   CPU  Command
11时28分27秒  1000      9702         -   19.37    0.50    0.00    0.00   19.87     0  java
11时28分27秒  1000         -      9702    0.00    0.00    0.00    0.00    0.00     0  |__java
'''
print(substr_after_lines(output, 2))
```

## 7. ts: 时间转换
```
from pyutilb.ts import *

# 今天
print(today()) # 纯日期
print(today(True)) # 日期+时间
# 迭代指定范围内的日期, 范围为天数
for date in iterate_date_round(round=3):
    print(date)
# 迭代指定范围内的日期, 范围为天数, 倒序
for date in iterate_date_round(round=-3, step=-1):
    print(date)
# 迭代指定范围内的日期, 范围为首尾日期
end_date = today() + datetime.timedelta(days=3)
for date in iterate_date_between(end_date=end_date):
    print(date)
# 迭代指定范围内的日期, 范围为首尾日期, 倒序
end_date = today() + datetime.timedelta(days=-3)
for date in iterate_date_between(end_date=end_date, step=-1):
    print(date)
```

## 8. ocr_baidu/ocr_youdao: ocr图像识别

## 4. yaml_boot: 抽取几个boot框架(HttpBoot/SeleniumBoot/AppiumBoot/MiniumBoot/ExcelBoot/MonitorBoot/K8sBoot)的基类

## 5. var_parser: 解析boot框架的yaml脚本中引用的变量

## 6. threadlocal: 封装ThreadLocal
```
from pyutilb.threadlocal import ThreadLocal

num = ThreadLocal()
print(num.get())
def task(arg):
    num.set(arg)
    print(num.get())
for i in range(10):
    t = Thread(target=task, args=(i,))
    t.start()
```

## 7. atomic: 封装AtomicInteger/AtomicStarter
```
from pyutilb.atomic import *

# 线程安全的递增
ai = AtomicInteger()
print(ai.inc())
print(ai.dec())

# 一次性处理
def test():
    print('只调用一次')
ast = AtomicStarter()
ast.start_once(test)
```

## 8. asyncio_threadpool: 封装执行协程的线程池
```
import threading
import asyncio
import time
from pyutilb import EventLoopThreadPool

async def test(i):  # 测试的阻塞函数
    print(f'call test({i})')
    await asyncio.sleep(1)
    # time.sleep(1)
    name = threading.current_thread().name
    print(f"current thread: {name}; i = {i}")

pool = EventLoopThreadPool(3)
for i in range(0, 40):
    pool.exec(test(i))
    # pool.exec(test, i)
time.sleep(4)
print("over")
pool.shutdown()
```

## 8. asyncio_apscheduler_thread: 封装运行event loop的定时器线程
```
import threading
import time
from pyutilb import SchedulerThread

def create_job(msg):  # 测试的阻塞函数
    def job():
        name = threading.current_thread()
        print(f"thread [{name}] trigger job: {msg}")

    return job

t = SchedulerThread()
# 添加定时任务
#t.add_cron_job("0 */1 * * * *", create_job("每隔1分"))
t.add_cron_job("0 */1 14 * * *", create_job("2点内每隔1分"))
# t.add_cron_job("*/1 * * * * *", create_job("每隔1秒"))
t.add_cron_job("15 * * * * *", create_job("指定15秒"))
t.add_cron_job("0 51 * * * * *", create_job("指定51分"))

job1 = t.add_cron_job("*/1 * * * * *", create_job("每隔1秒, 但2秒后删除"), id="plan1")
job2 = t.add_cron_job("*/1 * * * * *", create_job("每隔1秒, 但3秒后删除"))

# 删除
time.sleep(2)
print("删除job1: " + job1.id)
t.scheduler.remove_job(job1.id)

time.sleep(1)
print("删除job2: " + job2.id)
job2.remove()

time.sleep(10000)
```

## 9. lazy: 封装延迟创建的属性
```
from pyutilb.lazy import lazyproperty

class Man(object):

    @lazyproperty
    def address(self):
        return 'xxx.yyy.zzz'
```

## 9. tail: 使用协程实现类似 linux 的tail功能，可以订阅文件内容的增加
```
from pyutilb.tail import Tail

t = Tail("/home/shi/test/a.txt")
async def print_msg(msg):
    await asyncio.sleep(0.1)
    name = threading.current_thread() # MainThread
    print(f"thread [{name}] 捕获一行：{msg}")
t.follow(print_msg)
```

## 10. zkfile: 基于zookeeper实现的远程配置文件
### 设计理念
1. 数据层面：为了更好的融入k8s架构，远端配置文件的目录结构必须遵循k8s的层次结构，必包含两层：1 命名空间 2 应用；因此zookeeper上目录结构大致如下:
```
jkcfig
  default # k8s命名空间
    app1 # 应用
      redis.yaml # 配置文件
      log4j.properties
    app2 # 应用
      redis.yaml # 配置文件
      log4j.properties
```
注：仅支持 properties/yaml/yml/json 4种后缀的配置文件

2. 数据管理层面：结合 [jkcfg](https://github.com/shigebeyond/jkcfg) 在zookeeper上做配置管理，生成对应的目录结构

2. 应用端层面：就是本文`ZkConfigFiles`的实现，用来实时加载远端配置，即是从zookeeper(远端)中获得(当前k8s命名空间+应用)目录下的配置文件

### 使用
```
import time
from pyutilb.zkfile.zkconfigfiles import ZkConfigFiles

# zookeeper服务地址
zk_host = '10.106.113.218:2181'

# 实例化ZkConfigFiles, 他会从远端(zookeeper)加载配置文件, 需要3个参数: 1 zk_hosts: zookeeper服务地址 2 namespace: k8s命名空间 3 name: 当前应用名
files = ZkConfigFiles(zk_host, 'default', 'rpcserver')  # 加载zookeeper中路径/jkcfg/default/rpcserver 下的配置文件
file = 'redis.yml'
config = files.get_zk_config(file)  # 加载zookeeper中路径为/jkcfg/default/rpcserver/redis.yml 的配置文件
config.add_config_listener(lambda data: print(f"监听到配置[{file}]变更: {data}"))
while True:
    print(config['host'])  # 读配置文件中host配置项的值
    time.sleep(3)
```

## 11. template: 渲染模板
```python
from pyutilb.template import *

tpl = '<title>${title}</title>'
print(render_text(tpl, {'title': 'hero'}))

file = '/root/test.html'
print(render_file(file, {'title': 'hero'}))
```