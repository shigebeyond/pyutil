import logging
import logging.config
import concurrent.futures
from configparser import ConfigParser
import platform

# window下改写 ConfigParser.read(): fix 由于编码不一致而导致 pyutilb\logging.conf 读取失败bug
if platform.system().lower() == 'windows':
    read1 = ConfigParser.read
    def read2(self, filenames, encoding=None):
        if 'pyutilb\logging.conf' in filenames:
            encoding = 'utf-8'
        return read1(self, filenames, encoding)
    ConfigParser.read = read2

# 应用log配置
conf_file = __file__.replace("log.py", "logging.conf")
logging.config.fileConfig(conf_file)

# 线程池: 延迟创建
_executor = None
def executor():
    global _executor
    if _executor == None: # 延迟创建
        _executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    return _executor

# 异步日志
class AsyncLogger(object):

    def __init__(self, name):
        # 获得被代理的logger
        logger = logging.getLogger(name)
        self.logger = logger

    def debug(self, msg, *args, **kwargs):
        executor().submit(self.logger.debug, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        executor().submit(self.logger.info, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        executor().submit(self.logger.warning, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        executor().submit(self.logger.error, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        executor().submit(self.logger.critical, msg, *args, **kwargs)

# 获得异步日志
def getLogger(name=None):
    return AsyncLogger(name)

# 默认日志
log = getLogger("boot")

if __name__ == '__main__':
    log.debug("hello")
    log.error("err", exc_info = Exception('unknow err'))