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
属性file其实用的是第4层的节点名
'''
class ZkConfig(object):

    def __init__(self, files, file: str):
        self.files = files
        self.file = file

    # 获得配置数据
    @property
    def data(self):
        return self.files.get_file_props(self.file)

    # 添加配置变化监听器
    def add_config_listener(self, callback):
        self.files.add_config_listener(self.file, callback)

    # 实现dict方法
    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __contains__(self, key):
        return key in self.data

    def __len__(self):
        return len(self.data)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()
