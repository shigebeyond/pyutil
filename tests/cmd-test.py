from optparse import OptionParser #optparse里面最主要的类就是OptionParser了

optParser = OptionParser() #创建一个对象
optParser.add_option('-f','--file',action = 'store',type = "string" ,dest = 'filename')
optParser.add_option("-v","--vison", action="store_false", dest="verbose",
                     default='hello',help="make lots of noise [default]")

#上面的就是最主要的操作，差不多是定义参数的信息 -v是参数简写 --vsion是全写 两种名字都是同一个东西

fakeArgs = ['-f','file.txt','-v','how are you', 'arg1', 'arg2']
#这个fakeArgs是模拟sys.argv

option , args = optParser.parse_args()

#上面这里没有传入任何参数是为了更好的演示

op , ar = optParser.parse_args(fakeArgs)
#这里传入了fakeArgs，其操作和上面的是一样的
#这里的op会返回一个类似字典的自定义类型option中的dest变量，而值则是我们自己传进去的

print("option : ",option)
print("args : ",args)
print("op : ",op)
print("ar : ",ar)