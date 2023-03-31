import time


# 生成当前时间的时间戳，只有一个参数即时间戳的位数，默认为10位，输入位数即生成相应位数的时间戳，比如可以生成常用的13位时间戳
def now2timestamp(digits=10):
    ts = time.time()
    digits = 10 ** (digits - 10)
    return int(round(ts * digits))


# 将时间戳规范为10位时间戳
def timestamp2timestamp10(ts):
    return int(ts * (10 ** (10 - len(str(ts)))))


# 将当前时间转换为时间字符串，默认为2017-10-01 13:37:04格式
def now2date(format_string="%Y-%m-%d %H:%M:%S"):
    ts = int(time.time())
    arr = time.localtime(ts)
    return time.strftime(format_string, arr)


# 将10位时间戳转换为时间字符串，默认为2017-10-01 13:37:04格式
def timestamp2date(ts, format_string="%Y-%m-%d %H:%M:%S"):
    arr = time.localtime(ts)
    return time.strftime(format_string, arr)


# 将时间字符串转换为10位时间戳，时间字符串默认为2017-10-01 13:37:04格式
def date2timestamp(date, format_string="%Y-%m-%d %H:%M:%S"):
    arr = time.strptime(date, format_string)
    return int(time.mktime(arr))


# 不同时间格式字符串的转换
def date_format_convert(date, format_from="%Y-%m-%d %H:%M:%S", format_to="%Y-%m-%d %H-%M-%S"):
    arr = time.strptime(date, format_from)
    return time.strftime(format_to, arr)
