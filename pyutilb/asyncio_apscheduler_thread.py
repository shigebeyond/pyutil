import asyncio
import datetime
import threading
import time
from threading import Thread
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pyutilb.atomic import AtomicInteger
from pyutilb.asyncio_threadpool import EventLoopThread
from pyutilb.log import log

thread_counter = AtomicInteger(-1)

'''
运行event loop的定时器线程
  核心方法是 add_cron_job()
  其他方法是代理调用 AsyncIOScheduler，如果没有提供代理方法，请直接使用 .scheduler 来访问
'''
class SchedulerThread(EventLoopThread):

    # 构造函数: 接收 event loop
    def __init__(self):
        super().__init__()
        self.name = "SchedulerThread_" + str(thread_counter.inc()) # 修改线程名

        # 创建调度器
        self.scheduler = AsyncIOScheduler()
        self.scheduler._eventloop = self.loop # 调度器的loop = 线程的loop, 否则线程无法处理调度器的定时任务
        self.scheduler.start()

    # 添加定时作业
    def add_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None, **trigger_args):
        # 1 递延创建与启动线程
        self.thread_starter.start_once(self._start_thread)

        # 2 添加定时作业
        return self.scheduler.add_job(func, trigger, args=args, kwargs=kwargs, id=id, name=name, **trigger_args)

    # 添加定时作业
    def add_cron_job(self, cron, func, args=None, kwargs=None, id=None, name=None):
        # 解析cron表达式成trigger参数
        trigger_args = self.parse_cron_expr(cron)
        # 添加作业
        return self.add_job(func, 'cron', args=args, kwargs=kwargs, id=id, name=name, **trigger_args)

    # 调整作业的定时trigger
    def reschedule_cron_job(self, job_id, cron):
        # 解析cron表达式成trigger参数
        trigger_args = self.parse_cron_expr(cron)
        # 调整trigger
        return self.scheduler.reschedule_job(job_id, trigger='cron', **trigger_args)

    # 解析cron表达式成trigger参数
    def parse_cron_expr(self, cron):
        cron = cron.strip()
        n = cron.count(' ') + 1
        if n != 6 and n != 7:
            raise Exception(f"cron表达式要求有6~7个域, 目前有{n}个域")
        if n == 6:
            second, minute, hour, day_of_month, month, day_of_week = cron.split(' ')
            year = None
        else:
            second, minute, hour, day_of_month, month, day_of_week, year = cron.split(' ')
        # 分别对应job参数: year, month, day, week, day_of_week, hour, minute, second
        # 参考: /usr/local/lib/python3.7/dist-packages/apscheduler/triggers/cron/__init__.py
        trigger_args = {
            'second': second,
            'minute': minute,
            'hour': hour,
            'day': day_of_month,
            'month': month,
            'day_of_week': day_of_week,
            'year': year,
        }
        log.debug(f"解析cron: %s", trigger_args)
        return trigger_args

if __name__ == '__main__':
    # 测试
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

