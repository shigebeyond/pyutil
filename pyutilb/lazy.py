from concurrent.futures.thread import ThreadPoolExecutor

# 延迟计算(创建)属性装饰器: 使用 @lazyproperty 实例来代理目标对象属性的读取
class lazyproperty:
    def __init__(self, func):
        self.func = func

    # 读目标对象属性
    def __get__(self, instance, cls):
        if instance is None:
            return self

        value = self.func(instance)
        # 缓存结果到属性中
        setattr(instance, self.func.__name__, value)
        return value

# 延迟创建的线程池集合
class LazyThreads(object):

    def __init__(self, thread_num):
        self.thread_num = thread_num # 线程数

    @lazyproperty
    def thread_pool(self):
        return ThreadPoolExecutor(max_workers=self.thread_num) # 普通线程池

    @lazyproperty
    def asyncio_thread_pool(self):
        from pyutilb import EventLoopThreadPool # fix 循环引用，直接放在方法里
        return EventLoopThreadPool(self.thread_num) # 协程线程池

    @lazyproperty
    def asyncio_apscheduler_thread(self):
        from pyutilb import SchedulerThread # fix 循环引用，直接放在方法里
        return SchedulerThread() # 定时器的线程