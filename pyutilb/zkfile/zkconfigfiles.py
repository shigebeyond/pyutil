import configparser
import json
import time
from io import StringIO
import yaml
from dotenv import dotenv_values
from kazoo.client import KazooClient
from pyutilb.zkfile.filelistener import IFileListener
from pyutilb.zkfile.zkconfig import ZkConfig
from pyutilb.zkfile.zkfilesubscriber import ZkFileSubscriber

'''
zookeeper上的配置文件数据, 支持从远端(zookeeper)加载配置

设计目标：
    从zk中获得(当前k8s命名空间+应用)目录下的配置文件
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
属性file_props中的key其实用的是第4层的节点名
'''
class ZkConfigFiles(IFileListener):

    def __init__(self, zk_hosts, namespace, name):
        self.app_path = f"/jkcfg/{namespace}/{name}"  # 应用路径
        self.file_props = {}  # 所有配置文件的数据: <文件路径 to 配置数据>
        self.config_listeners = {} # 配置变化监听器: <配置文件名 to 配置变化监听器>
        # 监听应用下配置文件变化
        self.zk_sub = ZkFileSubscriber.instances(zk_hosts)
        self.zk_sub.subscribe(self.app_path, self)

    @property
    def files(self):
        '''
        获得所有配置文件
        '''
        return self.file_props.keys()

    # -------------- 实现 IFileListener zk文件变化的监听器 --------------
    def handle_file_add(self, path: str, content: str):
        '''
        处理配置文件新增
        :param url
        '''
        self.handle_content_change(path, content)

    def handle_file_remove(self, path: str):
        '''
        处理配置文件删除
        :param url
        '''
        path = self._get_filename(path)
        self.file_props.pop(path)
        self.trigger_config_listeners(path, None)

    def handle_content_change(self, path: str, content: str):
        '''
        处理文件内容变化
        :param path
        :param content
        '''
        path = self._get_filename(path)
        type = path.rsplit('.')[1]  # 扩展名即为类型
        data = self._build_properties(content, type)
        self.file_props[path] = data
        self.trigger_config_listeners(path, data)

    def _get_filename(self, path: str) -> str:
        '''
        从路径中获得文件名(干掉app_path)
        如 /jkcfg/default/rpcserver/redis.yml 转为 redis.yml
        '''
        # return path.replace(self.app_path, "") # wrong: /redis.yml
        return path[len(self.app_path) + 1:]  # right: redis.yml

    def _build_properties(self, content: str, type: str) -> dict:
        '''
        构建配置项
        :param content　配置文件内容
        :param type properties | yaml | json
        :return
        '''
        if not content.strip():
            return {}

        # 解析内容
        if type == "properties":
            return dotenv_values(stream=StringIO(content))  # 加载 properties 文件
        if type == "yaml" or type == "yml":
            return yaml.load(content, Loader=yaml.FullLoader)  # 加载 yaml 文件
        if type == "json":
            return json.loads(content)  # 加载 json 文件

        raise Exception("未知配置文件类型: " + type)

    def get_file_props(self, file: str) -> dict:
        '''
        获得配置文件的配置数据
        '''
        if file in self.file_props:
            return self.file_props[file]
        raise Exception(f"找到不zk配置文件[{file}], 其在zk路径为 {self.app_path}/{file}")

    def get_zk_config(self, file: str) -> ZkConfig:
        '''
        获得ZkConfig实例
        '''
        return ZkConfig(self, file)

    # -------------- 配置变化监听器 --------------
    # 添加配置变化监听器
    def get_config_listeners(self, file: str) -> list:
        if file not in self.config_listeners:
            self.config_listeners[file] = []
        return self.config_listeners[file]

    # 触发配置变化监听器
    def trigger_config_listeners(self, file: str, data: dict):
        for l in self.get_config_listeners(file):
            l(data)

    # 添加配置变化监听器
    def add_config_listener(self, file: str, callback):
        self.get_config_listeners(file).append(callback)

    # 删除配置变化监听器
    def remove_config_listener(self, file: str, callback):
        if file in self.config_listeners:
            self.config_listeners[file].remove(callback)

if __name__ == '__main__':
    # zookeeper服务地址
    zk_host = '10.106.113.218:2181'

    # 实例化ZkConfigFiles, 他会从远端(zookeeper)加载配置文件, 需要3个参数: 1 zk_hosts: zookeeper服务地址 2 namespace: k8s命名空间 3 name: 当前应用名
    files = ZkConfigFiles(zk_host, 'default', 'rpcserver')  # 加载zookeeper中路径/jkcfg/default/rpcserver 下的配置文件
    file = 'redis.yml'
    config = files.get_zk_config(file)  # 加载zookeeper中路径为/jkcfg/default/rpcserver/redis.yml 的配置文件
    config.add_config_listener(lambda data: print(f"监听到配置[{file}]变更: {data}"))
    while True:
        print(config['host'])  # 读配置文件中host配置项的值
        time.sleep(3)
