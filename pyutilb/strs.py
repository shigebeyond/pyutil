
# 之前的字符串
def substr_before(str, before):
    i = str.find(before)
    if i == -1:
        return None
    return str[0:i]

# 之后的字符串
def substr_after(str, after):
    i = str.find(after)
    if i == -1:
        return None
    return str[i+1:]

if __name__ == '__main__':
    str = 'hello world'
    print(substr_before(str, ' '))
    print(substr_after(str, ' '))