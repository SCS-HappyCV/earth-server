修改`save_pointcloud`，不仅要将`las`文件放到minio，还要利用`PotreePublisher`将点云文件转换为`potree`格式，最后将`potree`文件上传到minio中。
我将给你提供`PotreePublisher`和表模式，以及我已经写过的service。
具体要求如下：

1. 原las文件保存的代码我已经写好，你只需要在此基础上进行修改
2. 你需要根据`PotreePublisher`的文档，将las文件转换为`potree`文件
3. 将生成的`potree`的`html`文件上传到minio中
4. 代码中需要有详细的注释，方便他人阅读
5. 代码注释使用中文，你的对代码的解释也使用中文
6. 代码中要有log信息，方便调试
7. 使用 `loguru` 而不是 `logging`
8.  使用 `pathlib` 而不是 `os.path`
9.  尽可能用 `pathlib` 的方法进行文件操作，例如用 `Path().open()` 代替 `open()`，用 `Path().read_text()` 代替 `open().read()` 等
10. 将字符串转为`Path`对象时，请尽量加上`expanduser()`方法，以便支持`~`符号
11. 打开文件不用指定编码，因为默认是utf-8
12. 如果没有必要，不要使用`try/except`捕获异常
13. 在`except`中不要引发新的异常，而是直接`raise`
14. 打印异常不用`str(e)`，直接打印`e`
15. `return`写在`else`中，不要写在`try`中
16. 如果需要引发异常，请不要将异常字符串直接写到异常的括号内，而是先定义一个异常变量`err_msg`，然后将`err_msg`写入异常括号内
17. `return`语句尽量不要写在`try`块内，而是写在`else`块内
18. 使用`trackback`库将异常的行号也打印出来
19. 类型提示尽可能使用python原生对象作为类型，例如`list`, `dict`, `tuple`等。而不是`typing`模块中的`List`, `Dict`, `Tuple`等。
20. 当你要添加命令行参数时，使用 `Fire` 库而不是 `argparse`
21. 文件的复制和移动使用`shutil`库
22. 需要进行多维数组的`shape`变换时，使用`einops`库的`rearrange`，`pack`等函数，而不是`transpose`,`stack`等函数
23. 不要使用`async/await`这种异步编程方式
