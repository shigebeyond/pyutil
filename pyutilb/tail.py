# python实现tail
# 参考: https://github.com/kasun/python-tail/blob/master/tail.py
# 改进: 使用 asyncio
import asyncio
import os
import sys
import threading
import time
from apscheduler.util import iscoroutinefunction_partial
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Tail(object):
    """
    python 实现类似 linux 的tail功能，可以订阅文件内容的增加
    Python-Tail - Unix tail follow implementation in Python.
    python-tail can be used to monitor changes to a file.
    Example:
        import tail

        # Create a tail instance
        t = tail.Tail('file-to-be-followed')

        # Register a callback function to be called when a new line is found in the followed file.
        # If no callback function is registerd, new lines would be printed to standard out.
        t.register_callback(callback_function)

        # Follow the file with 5 seconds as sleep time between iterations.
        # If sleep time is not provided 1 second is used as the default time.
        t.follow(s=5)
    """

    ''' Represents a tail command. '''
    def __init__(self, path, scheduler: AsyncIOScheduler = None, from_end = True):
        ''' Initiate a Tail instance.
            Check for file validity, assigns callback function to standard out.

            Arguments:
                path - File to be followed.
                scheduler - AsyncIOScheduler.
        '''
        # 文件
        self.path = self.check_file_valid(path)
        self.file = open(self.path, "r")
        self.size = os.path.getsize(self.path)  # 记录当前文件大小, 只是为了识别文件被清空或日志分割的情况, 只需要对比 最新文件大小 > self.size
        # Go to the end of file
        if from_end:
            self.file.seek(0, 2)

        # 定时器
        self.scheduler = scheduler

        # 回调
        self.callback = sys.stdout.write

    def check_file_valid(self, path):
        """ Check whether the a given file exists, readable and is a file """
        if not os.access(path, os.F_OK):
            raise Exception("File '%s' does not exist" % (path))
        if not os.access(path, os.R_OK):
            raise Exception("File '%s' not readable" % (path))
        if os.path.isdir(path):
            raise Exception("File '%s' is a directory" % (path))
        return path

    def reload_file(self):
        """ Reload tailed file when it be empty be `echo "" > tailed file`, or segmentated by logrotate.
            从头开始读
        """
        try:
            self.file = open(self.path, "r")
            self.size = os.path.getsize(self.path)
            # Go to the head of file
            self.file.seek(0, 1)
            return True
        except:
            return False

    def follow(self, callback = None, interval=1):
        """ Do a tail follow. If a callback function is registered it is called with every new line.
        Else printed to standard out.

        Arguments:
            callback - Overrides default callback function to provided function.
            interval - Number of seconds to wait between each iteration; Defaults to 1.
        """
        if callback is not None:
            self.callback = callback

        # 1 同步阻塞sleep实现定时
        # while True:
        #     self.read_line()
        #     time.sleep(interval)

        # 2 异步协程实现定时
        # 没有定时器，则自己创建一个
        self_sheduler = self.scheduler is None
        if self_sheduler:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()

        # 添加定时任务
        self.scheduler.add_job(self.read_line, 'interval', seconds=interval, id=f'tail:{self.path}')

        # 启动定时事件循环
        if self_sheduler:
            asyncio.get_event_loop().run_forever()

    async def read_line(self):
        await self.check_file_size()
        # 读行
        line = self.file.readline()
        # 回调
        if line and line != "\n": # 忽略空+换行符
            if iscoroutinefunction_partial(self.callback):
                await self.callback(line)
            else:
                self.callback(line)

    async def check_file_size(self):
        size2 = os.path.getsize(self.path)
        # 1 正常, 文件在追加: 最新文件大小 > self.size
        if size2 >= self.size:
            self.size = size2
            return

        # 2 异常, 文件被清空或日志分割
        try_count = 0
        while try_count < 10:
            # 尝试从头开始
            if self.reload_file(): # 成功则跳出
                try_count = 0
                self.size = os.path.getsize(self.path)
                break

            # 失败则重试
            try_count += 1
            await asyncio.sleep(0.1)

        if try_count == 10:
            raise Exception("Open %s failed after try 10 times" % self.path)


if __name__ == '__main__':
    t = Tail("/home/shi/test/a.txt")
    '''
    def print_msg(msg):
        print("捕获一行：" + msg)
    t.follow(print_msg)
    '''
    async def print_msg(msg):
        await asyncio.sleep(0.1)
        name = threading.current_thread() # MainThread
        print(f"thread [{name}] 捕获一行：{msg}")
    t.follow(print_msg)

""" vim: set ts=4 sw=4 sts=4 tw=100 et: """