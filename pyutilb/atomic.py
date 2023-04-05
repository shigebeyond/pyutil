import threading

# int值的原子性增减
class AtomicInteger(object):

    def __init__(self, value: int = 0):
        self.value = int(value)
        self._lock = threading.Lock()

    # 自增, 返回增加后的数值
    def inc(self, d:int = 1):
        with self._lock:
            self.value += d
            return self.value

    # 自减, 返回减少后的数值
    def dec(self, d: int = 1):
        return self.inc(-d)

# 一次性的启动
class AtomicStarter(object):

    def __init__(self):
        self.started = False
        self._lock = threading.Lock()

    def start_once(self, callback):
        # 已启动过
        if self.started:
            return

        # 未启动，加锁启动
        with self._lock:
            # 双重检查
            if self.started:
                return
            self.started = True
            callback()
