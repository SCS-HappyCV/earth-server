写一个函数，获取可行的minio对象名。
具体要求如下：

1. 输入为一个字符串，表示对象名
2. 检查该对象名是否已经存在，如果不存在则直接返回
3. 如果已经存在，则在对象名后面加上一个数字，直到找到一个不存在的对象名
4.  代码中需要有详细的注释，方便他人阅读
5.  代码注释使用中文，你的对代码的解释也使用中文
6.  代码中要有log信息，方便调试
7.  使用 `loguru` 而不是 `logging`
8.  使用 `pathlib` 而不是 `os.path`
9.  尽可能用 `pathlib` 的方法进行文件操作，例如用 `Path().open()` 代替 `open()`，用 `Path().read_text()` 代替 `open().read()` 等
10. 打开文件不用指定编码，因为默认是utf-8
11. 打印异常不用`str(e)`，直接打印`e`
12. `return`写在`else`中，不要写在`try`中
13. 使用`trackback`库将异常的行号也打印出来
14. 类型提示尽可能使用Python 3.10以上的方式，例如`list`, `dict`, `tuple`等。而不是`typing.List`, `typing.Dict`, `typing.Tuple`等。
15. 当你要添加命令行参数时，使用 `Fire` 库而不是 `argparse`
16. 文件的复制和移动使用`shutil`库
17. 不要使用`async/await`这种异步编程方式
