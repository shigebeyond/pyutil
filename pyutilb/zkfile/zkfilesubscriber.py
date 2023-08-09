from pyutilb.log import log
from pyutilb.zkfile.filelistener import IFileListener
from pyutilb.zkfile.zkchildlistener import ZkChildListener

'''
zookeeper文件订阅器

设计目标：
    只监控(当前k8s命名空间+应用)目录下的配置文件
    配合 jkcfig 在zk上生成的目录结构

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

    def __init__(self, zk):
        self.zk = zk
        self.child_listeners = {}  # zk子节点监听器: <父目录 to zk子节点监听器>

    def subscribe(self, parent_path: str, listener: IFileListener):
        '''
        监听文件变化
        :param parent_path 父目录
        :param listener 监听器
        '''
        log.info("ZkChildListener监听[{}]子节点变化", parent_path)
        # 1 获得zk子节点监听器
        self.child_listeners[parent_path] = ZkChildListener(self.zk, parent_path, listener)

        # 2 刷新文件: 通知监听器更新缓存的文件
        self.list_files(parent_path)

    def unsubscribe(self, parent_path: str):
        '''
        取消监听文件变化
        :param parent_path 父目录
        :param listener 监听器
        '''
        log.info("ZkChildListener取消监听[{}]子节点变化", parent_path)
        # 获得zk子节点监听器
        child_listener = self.child_listeners[parent_path]
        if child_listener is not None:
            # 关闭: 清理监听器
            child_listener.close()
            # 删除zk子节点监听器
            self.child_listeners.remove(parent_path)

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
        self.child_listeners[parent_path].watch_children(parent_path, children)
        return children

    def close(self):
        for parent_path in self.child_listeners.keys():
            self.unsubscribe(parent_path)
