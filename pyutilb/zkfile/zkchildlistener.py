from kazoo.recipe.watchers import ChildrenWatch, DataWatch
from pyutilb.log import log
from pyutilb.zkfile.filelistener import IFileListener

'''
zk中子节点变化监听器
  适配器模式, 将zk监听器接口转为代理调用fileListener接口, 就是将zk节点/数据变化事件转为文件增删改事件, 好实现zk配置(文件)动态刷新
'''
class ZkChildListener(IFileListener):

    def __init__(self, zk, parent_path: str, file_listener: IFileListener):
        self.zk = zk
        self.parent_path = parent_path  # 父路径
        self.file_listener = file_listener  # 文件变化的监听器
        self.data_watchers = {}  # zk节点数据监听器: <文件子路径 to zk数据监听器>
        self.files = []  # 子文件

        # 添加zk子节点监听
        self.watching = True
        self.child_watcher = ChildrenWatch(client=zk, path=parent_path, func=self.watch_children)

    # ------------------- 监听子节点变化 ---------------------
    def watch_children(self, new_childs: list):
        '''
        监听zk中子节点(文件)变化
        对比旧的文件, 从而识别文件的增删, 从而触发 IFileListener 的增删方法
        :param parent_path
        :param current_childs
        '''
        if not self.watching:
            log.info("watch_children()取消订阅zk[%s]子节点变化, 子节点为:%s", self.parent_path, new_childs)
            return False

        files = set(self.files)
        new_files = set(new_childs)
        # 处理配置文件变化, 从而触发 IDiscoveryListener
        log.info("watch_children()处理zk[%s]子节点变化事件, 子节点为:%s", self.parent_path, new_childs)
        # 1 新加文件
        add_files = new_files - files
        for file in add_files:
            path = self.parent_path + '/' + file
            content = self.zk.get(path)  # 节点值
            content = content[0].decode('utf-8')
            self.handle_file_add(path, content)

        # 2 删除文件
        remove_files = files - new_files
        for file in remove_files:
            path = self.parent_path + '/' + file
            self.handle_file_remove(path)

        self.files = new_childs
        return True

    # ------------------- 监听子节点数据变化 ---------------------
    def add_data_listener(self, path: str):
        '''
        对文件子节点添加数据监听器
        :param path
        '''
        log.info("ZkChildListener监听[%s]数据变化", path)

        # 订阅节点数据变化: 如果不订阅，则返回false
        def watch_data(data, stat, event):
            # 首次 and 有订阅该路径，控制是否继续订阅
            # 首次是在实例化DataWatch时，但self.data_watchers[path]还未赋值，因此用
            watching = event is None or path in self.data_watchers
            if watching:
                content = data.decode('utf-8')
                # 处理更新文件内容
                self.file_listener.handle_content_change(path, content)
                log.info("watch_data()处理zk节点[%s]数据变化事件，版本为:%s，数据为:%s", path, stat.version, content)
            else:
                log.info("watch_data()取消订阅zk节点[%s]数据变化", path)
            return watching

        watcher = DataWatch(client=self.zk, path=path, func=watch_data)
        self.data_watchers[path] = watcher

    def remove_data_listener(self, path: str):
        '''
        对文件子节点删除数据监听器
        :param path
        '''
        log.info("ZkChildListener取消监听[%s]数据变化", path)
        watcher = self.data_watchers.pop(path)
        #watcher.cancel() # 无效

    def close(self):
        '''
        关闭: 清理监听器
        '''
        # 取消zk子节点监听
        # self.child_watcher.cancel() # 无效
        self.watching = False

        # 清理数据监听器
        for key in list(self.data_watchers.keys()):
            self.remove_data_listener(key)

    # ------------------- 代理调用 file_listener, 多加了增删数据监听器 ---------------------
    def handle_file_add(self, path: str, content: str):
        '''
        处理配置文件新增
        :param path
        :param all_path
        '''
        self.file_listener.handle_file_add(path, content)
        # 监听子节点的数据变化
        self.add_data_listener(path)

    def handle_file_remove(self, path: str):
        '''
        处理配置文件删除
        :param path
        :param all_path
        '''
        self.file_listener.handle_file_remove(path)
        # 取消监听子节点的数据变化
        self.remove_data_listener(path)

    def handle_content_change(self, path: str, content: str):
        '''
        处理文件内容变化
        :param path
        :param content
        '''
        self.file_listener.handle_content_change(path, content)
