[GitHub](https://github.com/shigebeyond/pyutilb) | [Gitee](https://gitee.com/shigebeyond/pyutilb)

# pyutilb - python通用工具类代码

1. util: 通用方法
3. file: 文件读写，如 `read_yaml()` 支持读取本地或http的yaml文件
4. log: 通用日志
5. cmd: 同步或异步执行命令
6. str: 字符串操作
7. ts: 时间转换
8. ocr_baidu/ocr_youdao: ocr图像识别 
4. yaml_boot: 抽取几个boot框架(HttpBoot/SeleniumBoot/AppiumBoot/MiniumBoot/ExcelBoot)的基类
5. var_parser: 解析boot框架的yaml脚本中引用的变量 
6. threadlocal: 封装ThreadLocal
7. atomic: 封装AtomicInteger/AtomicStarter
8. asyncio_threadpool: 封装执行协程的线程池
8. asyncio_apscheduler_thread: 封装运行event loop的定时器线程
9. lazy: 封装延迟创建的对象
9. tail: 使用协程实现类似 linux 的tail功能，可以订阅文件内容的增加