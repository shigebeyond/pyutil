import datetime
import time

# 今天
def today():
    return datetime.date.today()

# 现在
def now():
    return datetime.datetime.now()

# 迭代日期
def iterate_date_between(start_date = None, end_date = None, step = 1):
    if step == 0:
        raise Exception("Invalid step: 0")
    if start_date is None:
        start_date = today()
    if end_date is None:
        end_date = today()
    days = (end_date - start_date).days # 相差天数
    return iterate_date_round(start_date, int(days/step), step)

# 迭代日期
def iterate_date_round(start_date = None, round = 0, step = 1):
    if step == 0:
        raise Exception("Invalid step: 0")
    if start_date is None:
        start_date = today()
    curr_date = start_date
    for i in range(0, round):
        yield curr_date
        curr_date = curr_date + datetime.timedelta(days=step)

# 检查时间是否是今天
def is_today(time):
    return now().date() == time.date() # 今天

# 字符串转时间
def str2date(str):
    if ' ' in str:
        format = "%Y-%m-%d %H:%M"
    else:
        format = "%Y-%m-%d"
    return datetime.datetime.strptime(str, format)

# 生成当前时间的时间戳，只有一个参数即时间戳的位数，默认为10位，输入位数即生成相应位数的时间戳，比如可以生成常用的13位时间戳
def now2timestamp(digits=10):
    ts = time.time()
    digits = 10 ** (digits - 10)
    return int(round(ts * digits))

# 将时间戳规范为10位时间戳
def timestamp2timestamp10(ts):
    return int(ts * (10 ** (10 - len(str(ts)))))

# 将当前时间转换为时间字符串，默认为2017-10-01 13:37:04格式
def now2str(format_string="%Y-%m-%d %H:%M:%S"):
    ts = int(time.time())
    arr = time.localtime(ts)
    return time.strftime(format_string, arr)

# 将10位时间戳转换为时间字符串，默认为2017-10-01 13:37:04格式
def timestamp2str(ts, format_string="%Y-%m-%d %H:%M:%S"):
    arr = time.localtime(ts)
    return time.strftime(format_string, arr)

# 将时间字符串转换为10位时间戳，时间字符串默认为2017-10-01 13:37:04格式
def str2timestamp(str, format_string="%Y-%m-%d %H:%M:%S"):
    arr = time.strptime(str, format_string)
    return int(time.mktime(arr))

# 不同时间格式字符串的转换
def date_format_convert(str, format_from="%Y-%m-%d %H:%M:%S", format_to="%Y-%m-%d %H-%M-%S"):
    arr = time.strptime(str, format_from)
    return time.strftime(format_to, arr)

if __name__ == '__main__':
    ''' 当前时间不能做参数默认值
    def test(start_date = now()):
        print(start_date)
    test()
    time.sleep(5)
    test() # 2个test()的时间是一样的, 但不符合程序设计意图
    '''
    print("--- iterate_date_round(3日)")
    for date in iterate_date_round(round=3):
        print(date)
    print("--- iterate_date_round(-3日)")
    for date in iterate_date_round(round=-3, step=-1):
        print(date)
    print("--- iterate_date_between(3日)")
    end_date = today() + datetime.timedelta(days=3)
    for date in iterate_date_between(end_date=end_date):
        print(date)
    print("--- iterate_date_between(-3日)")
    end_date = today() + datetime.timedelta(days=-3)
    for date in iterate_date_between(end_date=end_date, step=-1):
        print(date)