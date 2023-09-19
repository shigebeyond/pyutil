from pyutilb.lazy import lazyproperty

# 代理spark DataFrame，主要用于代理df的数据方法(即[]操作符)，如df.collect()[0]
# 用在SparkBoot中
class SparkDfProxy(object):

    def __init__(self, df):
        self.df = df

    # 对df.collect()之后的数据加缓存，不用每次都collect()
    @lazyproperty
    def data(self):
        return self.df.collect() # 收集spark df数据

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]