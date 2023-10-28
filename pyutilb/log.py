import logging
import logging.config
import concurrent.futures
import time
from pyutilb.lazy import lazyproperty
from configparser import ConfigParser
import platform

# window下改写 ConfigParser.read(): fix 由于编码不一致而导致 pyutilb\logging.conf 读取失败bug
if platform.system().lower() == 'windows':
    read1 = ConfigParser.read
    def read2(self, filenames, encoding=None):
        if '\logging.conf' in filenames:
            encoding = 'utf-8'
        return read1(self, filenames, encoding)
    ConfigParser.read = read2

# 加载并应用log的默认配置，延迟调用，防止没有打日志却创建了日志文件(如k8scmd库)
def load_log_conf():
    conf_file = __file__.replace("log.py", "logging.conf")
    logging.config.fileConfig(conf_file)

# 异步日志
class AsyncLogger(object):
    # 线程池: 延迟创建
    _executor = None

    # 获得线程池
    @staticmethod
    def executor():
        if AsyncLogger._executor == None:  # 延迟创建
            AsyncLogger._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        return AsyncLogger._executor

    def __init__(self, name):
        self.name = name

    # 延迟获得被代理的logger => 延迟加载log配置 => 延迟创建日志文件
    @lazyproperty
    def logger(self):
        load_log_conf()  # 延迟加载log配置
        return logging.getLogger(self.name)

    # 设置日志等级
    def setLevel(self, level):
        if isinstance(level, str):
            level = level.upper() # 转大写
        self.logger.setLevel(level) # logger内部会转为int

    # 打日志
    def debug(self, msg, *args, **kwargs):
        if self.logger.isEnabledFor(logging.DEBUG):
            AsyncLogger.executor().submit(self.logger.debug, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if self.logger.isEnabledFor(logging.INFO):
            AsyncLogger.executor().submit(self.logger.info, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if self.logger.isEnabledFor(logging.WARNING):
            AsyncLogger.executor().submit(self.logger.warning, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if self.logger.isEnabledFor(logging.ERROR):
            AsyncLogger.executor().submit(self.logger.error, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        if self.logger.isEnabledFor(logging.CRITICAL):
            AsyncLogger.executor().submit(self.logger.critical, msg, *args, **kwargs)

# 获得异步日志
def getLogger(name=None):
    return AsyncLogger(name)

# 默认日志
log = getLogger("boot")

if __name__ == '__main__':
    # 原始配置：写 boot.log
    log.debug("hello")
    log.error("err", exc_info = Exception('unknow err'))

    time.sleep(1)

    # 修改配置: 写 xxx.log
    conf_file = __file__.replace("log.py", "logging2.conf")
    logging.config.fileConfig(conf_file)
    log.debug("hello")
    log.error("err", exc_info=Exception('unknow err'))

    # 异步线程也会受到影响: 写 xxx.log
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(log.debug, "异步执行哈哈哈哈1")
    executor.submit(log.debug, "异步执行哈哈哈哈2")
    executor.submit(log.debug, "异步执行哈哈哈哈3")

    time.sleep(3)