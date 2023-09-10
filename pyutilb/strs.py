
# 获得之前的字符串
def substr_before(str, before):
    i = str.find(before)
    if i == -1:
        return None
    return str[0:i]

# 获得之后的字符串
def substr_after(str, after):
    i = str.find(after)
    if i == -1:
        return None
    return str[i+1:]

# 获得之后的字符串
def substr_after_last(str, after):
    i = str.rfind(after)
    if i == -1:
        return None
    return str[i+1:]

# 找到第几行的位置，不包含换行符
# 就是第几个换行符的位置+1
def find_lines(str, nline):
    l = len(str)
    i = 0
    while i < l and i != -1 and nline > 0:
        i = str.find("\n", i) + 1
        # print(i)
        nline -= 1
    return i

# 获得第几行之后的字符串
def substr_after_lines(str, nline):
    i = find_lines(str, nline)
    return str[i:]

if __name__ == '__main__':
    '''
    str = 'hello world'
    print(substr_before(str, ' '))
    print(substr_after(str, ' '))
    '''
    output = '''Linux 5.10.60-amd64-desktop (shi-PC) 	2023年04月23日 	_x86_64_	(6 CPU)

11时28分27秒   UID      TGID       TID    %usr %system  %guest   %wait    %CPU   CPU  Command
11时28分27秒  1000      9702         -   19.37    0.50    0.00    0.00   19.87     0  java
11时28分27秒  1000         -      9702    0.00    0.00    0.00    0.00    0.00     0  |__java
'''
    print(substr_after_lines(output, 2))