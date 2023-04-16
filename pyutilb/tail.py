# python实现tail
# 参考: https://www.cnblogs.com/bufferfly/p/4878688.html
# 改进: 使用 asyncio
import os
import sys
import time

class Tail(object):
    """
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
    def __init__(self, path):
        ''' Initiate a Tail instance.
            Check for file validity, assigns callback function to standard out.

            Arguments:
                path - File to be followed. '''
        self.check_filevalid(path)
        self.path = path
        self.callback = sys.stdout.write
        self.try_count = 0

        self.file = open(self.path, "r")
        self.size = os.path.getsize(self.path) # 记录当前文件大小, 只是为了识别文件被清空或日志分割的情况, 只需要对比 最新文件大小 > self.size

        # Go to the end of file
        self.file.seek(0, 2)

    def check_filevalid(self, file):
        """ Check whether the a given file exists, readable and is a file """
        if not os.access(file, os.F_OK):
            raise Exception("File '%s' does not exist" % (file))
        if not os.access(file, os.R_OK):
            raise Exception("File '%s' not readable" % (file))
        if os.path.isdir(file):
            raise Exception("File '%s' is a directory" % (file))

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

    def follows(self, interval=0.01):
        """ Do a tail follow. If a callback function is registered it is called with every new line.
        Else printed to standard out.

        Arguments:
            interval - Number of seconds to wait between each iteration; Defaults to 1.
        """

        while True:
            self.follow_once()
            time.sleep(interval)

    def follow_once(self):
        self.check_file_size()
        # 当前位置
        curr_position = self.file.tell()
        # 读行
        lines = self.file.readline()
        # if not lines:
        #     self.file.seek(curr_position)
        # 回调
        for line in lines:
            self.callback(line)

    def check_file_size(self):
        size2 = os.path.getsize(self.path)
        # 1 正常, 文件在追加: 最新文件大小 > self.size
        if size2 >= self.size:
            self.size = size2
            return

        # 2 异常, 文件被清空或日志分割
        while self.try_count < 10:
            if not self.reload_file():  # 从头开始
                self.try_count += 1
            else:
                self.try_count = 0
                self.size = os.path.getsize(self.path)
                break
            time.sleep(0.1)

        if self.try_count == 10:
            raise Exception("Open %s failed after try 10 times" % self.path)


    def register_callback(self, func):
        """ Overrides default callback function to provided function. """
        self.callback = func

if __name__ == '__main__':
    t = Tail("/home/shi/test/a.txt")
    def print_msg(msg):
        print(msg)

    t.register_callback(print_msg)

    t.follows()

""" vim: set ts=4 sw=4 sts=4 tw=100 et: """