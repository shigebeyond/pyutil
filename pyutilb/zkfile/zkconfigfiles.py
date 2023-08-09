import configparser
import json
import yaml
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

    def __int__(self, namespace, name, zk):
        self.app_path = f"/jkcfg/${namespace}/${name}"  # 应用路径
        self.file_props = {}  # 所有配置文件的数据: <文件路径 to 配置数据>
        self.zk = zk
        # 监听应用下配置文件变化
        self.zk_sub = ZkFileSubscriber(zk)
        self.zk_sub.subscribe(self.app_path, self)

    @property
    def files(self):
        '''
        获得所有配置文件
        '''
        return self.file_props.keys

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
        self.file_props.remove(path)

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

    def _get_filename(self, path: str) -> str:
        '''
        从路径中获得文件名(干掉app_path)
        如 /jkcfg/default/rpcserver/redis.yml 转为 redis.yml
        '''
        # return path.replace(self.app_path, "") # wrong: /redis.yml
        return path[self.app_path.length+1 : ]  # right: redis.yml

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
            return configparser.ConfigParser().read_string(content)  # 加载 properties 文件
        if type == "yaml":
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
