请重构该文件的代码，实现将多颜色的jpg图片转换为svg图片。

1. 请使用类的方式实现。
2. 代码中需要有详细的注释，方便他人阅读
3. 代码注释使用中文，你的对代码的解释也使用中文
4. 代码中要有log信息，方便调试
5. 使用 `loguru` 而不是 `logging`
6. 使用 `pathlib` 而不是 `os.path`
7. 尽可能用 `pathlib` 的方法进行文件操作，例如用 `Path().open()` 代替 `open()`，用 `Path().read_text()` 代替 `open().read()` 等
8. 将字符串转为`Path`对象时，请尽量加上`expanduser()`方法，以便支持`~`符号
9. 打开文件不用指定编码，因为默认是utf-8
10. 如果没有必要，不要使用`try/except`捕获异常
11. 在`except`中不要引发新的异常，而是直接`raise`
12. 打印异常不用`str(e)`，直接打印`e`
13. `return`写在`else`中，不要写在`try`中
14. 如果需要引发异常，请不要将异常字符串直接写到异常的括号内，而是先定义一个异常变量`err_msg`，然后将`err_msg`写入异常括号内
15. `return`语句尽量不要写在`try`块内，而是写在`else`块内
16. 使用`trackback`库将异常的行号也打印出来
17. 类型提示尽可能使用python原生对象作为类型，例如`list`, `dict`, `tuple`等。而不是`typing`模块中的`List`, `Dict`, `Tuple`等。
18. 当你要添加命令行参数时，使用 `Fire` 库而不是 `argparse`
19. 可以使用`python-box`库加载`yaml`, `json`等配置文件
20. 文件的复制和移动使用`shutil`库
21. 需要进行多维数组的`shape`变换时，使用`einops`库的`rearrange`，`pack`等函数，而不是`transpose`,`stack`等函数
22. 不要使用`async/await`这种异步编程方式
