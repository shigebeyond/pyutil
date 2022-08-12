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

# 应用log配合着
conf = __file__.replace("log.py", "logging.conf")
logging.config.fileConfig(conf)

# 创建logger
logger = logging.getLogger("boot")

# 线程池: 延迟创建
_executor = None
def executor():
    global _executor
    if _executor == None: # 延迟创建
        _executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    return _executor

# 异步日志
def debug(msg, *args, **kwargs):
    executor().submit(logger.debug, msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    executor().submit(logger.info, msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    executor().submit(logger.warning, msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    executor().submit(logger.error, msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    executor().submit(logger.critical, msg, *args, **kwargs)

if __name__ == '__main__':
    debug("hello")
    error("err", exc_info = Exception('unknow err'))
    logger.error("err", exc_info = Exception('unknow err'))