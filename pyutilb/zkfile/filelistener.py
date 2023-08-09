'''
文件变化的监听器接口：监听某个配置文件的增删改变化
  有2个实现类
  1 ZkChildListener 适配器模式, 将zk监听器接口转为代理调用fileListener接口, 就是将zk节点/数据变化事件转为文件增删改事件, 好实现zk配置(文件)动态刷新
  2 ZkConfigFiles zk配置文件, 就是被ZkChildListener代理调用 来实现动态刷新配置
'''
class IFileListener(object):

    def handle_file_add(self, path: str, content: str):
        '''
        处理配置文件新增
        :param path
        '''

    def handle_file_remove(self, path: str):
        '''
        处理配置文件删除
        :param path
        '''

    def handle_content_change(self, path: str, content: str):
        '''
        处理文件内容变化
        :param path
        :param content
        '''
