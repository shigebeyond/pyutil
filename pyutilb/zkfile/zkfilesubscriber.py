import atexit
import threading

from kazoo.client import KazooClient

from pyutilb.log import log
from pyutilb.zkfile.filelistener import IFileListener
from pyutilb.zkfile.zkchildlistener import ZkChildListener

'''
zookeeper文件订阅器

设计目标：
    只监控(当前k8s命名空间+应用)目录下的配置文件
    配合 jkcfig 在zk上生成的目录结构
    通过 ZkFileSubscriber.instances() 获得实例

zk目录结构如下:
```
jkcfig
 	default # k8s命名空间
 		app1 # 应用
 			redis.yaml # 配置文件
             log4j.properties
 		app2 # 应用
 			redis.yaml # 配置文件
             log4j.properties
```
'''
class ZkFileSubscriber(object):

    # 单例池
    insts = {}
    # 创建单例的锁
    _lock = threading.Lock()

    @classmethod
    def instances(cls, zk_hosts):
        if zk_hosts not in cls.insts:
            # 未启动，加锁启动
            with cls._lock:
                # 双重检查
                if zk_hosts not in cls.insts:
                    cls.insts[zk_hosts] = cls(zk_hosts)
        return cls.insts[zk_hosts]

    def __init__(self, zk_hosts):
        if not isinstance(zk_hosts, KazooClient):
            zk = KazooClient(hosts=zk_hosts)
            zk.start()
        self.zk = zk
        self.child_listeners = {}  # zk子节点监听器: <父目录 to zk子节点监听器>
        atexit.register(self.close) # 关闭钩子: 去掉监听+关闭zk连接

    def subscribe(self, parent_path: str, listener: IFileListener):
        '''
        监听文件变化
        :param parent_path 父目录
        :param listener 监听器
        '''
        log.info("ZkChildListener监听[%s]子节点变化", parent_path)
        # 1 获得zk子节点监听器
        self.child_listeners[parent_path] = ZkChildListener(self.zk, parent_path, listener)

        # 2 刷新文件: 通知监听器立即更新缓存的文件 -- 多余, ZkChildListener->ChildrenWatch 一创建就会自动拉子节点一次, 因此不需要我在主动拉
        # self.list_files(parent_path)

    def unsubscribe(self, parent_path: str):
        '''
        取消监听文件变化
        :param parent_path 父目录
        :param listener 监听器
        '''
        log.info("ZkChildListener取消监听[%s]子节点变化", parent_path)
        # 获得zk子节点监听器
        child_listener = self.child_listeners[parent_path]
        if child_listener is not None:
            # 关闭: 清理监听器
            child_listener.close()
            # 删除zk子节点监听器
            self.child_listeners.pop(parent_path)

    def list_files(self, parent_path: str) -> list:
        '''
        列出文件
        :param parent_path 父目录
        :return 文件
        '''
        # 获得子节点
        children = []
        if self.zk.exists(parent_path):
            children = self.zk.get_children(parent_path)

        # 处理文件变化, 从而触发 IDiscoveryListener
        self.child_listeners[parent_path].watch_children(children)
        return children

    # 去掉监听+关闭zk连接
    def close(self):
        for parent_path in list(self.child_listeners.keys()):
            self.unsubscribe(parent_path)
        self.zk.stop()
