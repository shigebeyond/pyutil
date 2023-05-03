import asyncio
from asyncio import coroutines, get_running_loop
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from threading import Thread

from pyutilb.atomic import *
from pyutilb.log import log

thread_counter = AtomicInteger(-1)

# 获得当前运行的loop
def get_running_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError as e:
        return None

# 运行event loop的单个线程
class EventLoopThread(object):
    thread_name_pref = "EventLoopThread_"

    # 构造函数: 接收 event loop
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread_starter = AtomicStarter() # 一次性创建线程
        self.thread = None # submit()时才会递延创建与启动线程
        self.name = EventLoopThread.thread_name_pref + str(thread_counter.inc()) # 线程名

    # 运行事件循环
    def _run_loop(self):
        log.debug("%s: event loop start", self.name)
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()  # 死循环，处理event loop
        log.debug("%s: event loop end", self.name)

    # submit()时才会递延创建与启动线程
    def _start_thread(self):
        log.debug("%s: start thread", self.name)
        self.thread = Thread(name=self.name, target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()

    # 停止事件循环，也线程执行也会停止
    def shutdown(self):
        log.debug("%s: thread shutdown start", self.name)
        self.loop.call_soon_threadsafe(self.loop.stop) # loop.stop()必须在call_soon_threadsafe()中调用(会发新的任务, 从而触发epoll信息), 否则无法会卡死在 EpollSelector.selectors.select()
        log.debug("%s: thread shutdown end", self.name)

    # 添加任务(协程或回调函数), 返回future
    def exec(self, task, *args):
        # 1 递延创建与启动线程
        self.thread_starter.start_once(self._start_thread)

        # 2 将任务扔到event loop执行
        # 2.1 如果任务是函数调用
        if callable(task):
            log.debug(f"%s: execute function: %s%s", self.name, task.__qualname__, args)
            loop = self.loop
            def callback():
                # 执行函数 -- 可以做捕获异常，但只能针对普通函数，不能针对协程函数，因为协程函数执行返回的是一个协程代理对象，并非马上执行，只有在await时才执行
                ret = task(*args)
                # 如果返回值是协程, 则还要扔到队列中
                if coroutines.iscoroutine(ret):
                    asyncio.run_coroutine_threadsafe(ret, loop)
            self.loop.call_soon_threadsafe(callback)
            return

        # 2.2 如果任务是协程/future等
        #if coroutines.iscoroutine(task):
        log.debug(f"%s: execute coroutine: %s", self.name, task)
        return asyncio.run_coroutine_threadsafe(task, self.loop)


# 运行event loop的线程池
class EventLoopThreadPool(object):

    def __init__(self, n_threads):
        self.threads = list(map(lambda _: EventLoopThread(), range(0, n_threads)))
        self.idx = AtomicInteger(-1)

    # 添加协程任务, 返回future
    def exec(self, task, *args):
        return self.next_thread().exec(task, *args)

    # 包装方法的装饰器
    def run_in_pool(self, func):
        @wraps(func)
        def wrapper(*args):
            return self.exec(func, *args)

        return wrapper

    # 获得下一个线程
    def next_thread(self):
        i = self.idx.inc() % len(self.threads)
        return self.threads[i]

    # 停止线程池
    def shutdown(self):
        print("pool shutdown")
        for thread in self.threads:
            thread.shutdown()

if __name__ == '__main__':
    # 测试
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
