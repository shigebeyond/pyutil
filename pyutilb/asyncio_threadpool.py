import asyncio
from asyncio import coroutines
import time
from concurrent.futures import ThreadPoolExecutor
from pyutilb.atomic import *
from .log import log

# 运行event loop的单个线程
class EventLoop1Thread(object):

    # 构造函数: 接收 event loop
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.executor_starter = AtomicStarter() # 一次性创建线程
        self.executor = ThreadPoolExecutor(max_workers=1) # submit()时才会递延创建与启动线程
        self.executor._thread_name_prefix = self.executor._thread_name_prefix.replace('ThreadPoolExecutor', 'EventLoopThread') # 修正线程名前缀

    @property
    def name(self):
        # return threading.current_thread().name # 不一定都是在本线程中打印本线程名
        return self.executor._thread_name_prefix + '_0'

    # 运行事件循环
    def _run_loop(self):
        log.debug(self.name + ": event loop start")
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()  # 死循环，处理event loop
        log.debug(self.name + ": event loop end")

    # submit()时才会递延创建与启动线程
    def _start_thread(self):
        log.debug(self.name + ": start thread")
        self.executor.submit(self._run_loop)

    # 停止事件循环，也会停止线程
    def shutdown(self):
        log.debug(self.name + ": thread shutdown start")
        self.loop.call_soon_threadsafe(self.loop.stop) # loop.stop()必须在call_soon_threadsafe()中调用(会发新的任务, 从而触发epoll信息), 否则无法会卡死在 EpollSelector.selectors.py.select()
        self.executor.shutdown()
        log.debug(self.name + ": thread shutdown end")

    # 添加任务(协程或回调函数), 返回future
    def exec(self, task, *args):
        # 1 递延创建与启动线程
        self.executor_starter.start_once(self._start_thread)

        # 2 将任务扔到event loop执行
        # 2.1 如果任务是函数调用
        if callable(task):
            log.debug(f"{self.name}: execute task: {task.__qualname__}{args}")
            loop = self.loop
            def callback():
                # 执行函数
                ret = task(*args)
                # 如果返回值是协程, 则还要扔到队列中
                if coroutines.iscoroutine(ret):
                    asyncio.run_coroutine_threadsafe(ret, loop)
            self.loop.call_soon_threadsafe(callback)
            return

        # 2.2 如果任务是协程/future等
        #if coroutines.iscoroutine(task):
        return asyncio.run_coroutine_threadsafe(task, self.loop)


# 运行event loop的线程池
class EventLoopThreadPool(object):

    def __init__(self, n_threads):
        self.threads = list(map(lambda _: EventLoop1Thread(), range(0, n_threads)))
        self.idx = AtomicInteger(-1)

    # 添加协程任务, 返回future
    def exec(self, task, *args):
        return self.next_thread().exec(task, *args)

    # 获得下一个线程
    def next_thread(self):
        i = self.idx.inc() % len(self.threads)
        return self.threads[i]

    # 停止线程池
    def shutdown(self):
        print("pool shutdown")
        for thread in self.threads:
            thread.shutdown()

# 测试
async def test(i):  # 测试的阻塞函数
    print(f'call test({i})')
    await asyncio.sleep(1)
    # time.sleep(1)
    name = threading.current_thread()
    print(f"current thread: {name}; i = {i}")

if __name__ == '__main__':
    pool = EventLoopThreadPool(3)
    for i in range(0, 40):
        pool.exec(test(i))
    time.sleep(4)
    print("over")
    pool.shutdown()
