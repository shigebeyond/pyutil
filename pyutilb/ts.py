import calendar
import datetime
import re
import time

# 今天
def today(full = False):
    zero = datetime.date.today() # 0点
    if full: # 23:59:59
        #return zero + datetime.timedelta(hours=23, minutes=59, seconds=59) # zero是date类型, 加了后还是date类型, 即0点
        return datetime.datetime.combine(zero, datetime.time.max)

    return zero

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

# 本周最后一天
def lastday_of_week(date = None):
    if date is None:
        date = today()
    return date + datetime.timedelta(6 - date.weekday())

# 本月最后一天
def lastday_of_month(date = None):
    if date is None:
        date = today()
    _, days = calendar.monthrange(date.year, date.month) # 本月的最大天数
    return datetime.date(date.year, date.month, days)

# 上月最后一天
def lastday_of_lastmonth(date = None):
    if date is None:
        date = today()
    first = datetime.date(day=1, month=today.month, year=today.year) # 本月第一天
    return first - datetime.timedelta(days=1) # 前一天=上月最后一天

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
    return datetime.datetime.now().strftime(format_string)

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

age_unit2seconds = {
    'y': 365*86400,
    'mo': 30*86400,
    'd': 86400,
    'h': 3600,
    'm': 60,
    's': 1,
}

# k8s资源年龄字符串转秒数: 年（"y"）、月（"mo"）、天（"d"）、小时（"h"）、分钟（"m"）和秒（"s"）
def age2seconds(age):
    parts = re.findall(r'\d+\w', age)
    ret = 0
    for part in parts:
        num = int(part[:-1])
        unit = part[-1]
        ret += num * age_unit2seconds[unit]
    return ret

if __name__ == '__main__':
    ''' 当前时间不能做参数默认值
    def test(start_date = now()):
        print(start_date)
    test()
    time.sleep(5)
    test() # 2个test()的时间是一样的, 但不符合程序设计意图
    '''
    print(today())
    print(today(True))
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