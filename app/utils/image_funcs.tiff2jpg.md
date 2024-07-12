写一个函数，将输入的tiff图片转换为jpg图片。
代码具体要求如下：

1. 函数的参数有两个，一个是输入的tiff图片的路径，一个是输出的png图片的路径或者None
   - 如果输出路径是None，则你自行创建一个临时文件来存储输出的图片
   - 如果输出路径不是None，则将输出的图片保存到指定的路径
2. 返回值是输出的jpg图片的路径
3. 如果输入的图片不存在，直接抛出异常
4. 如果输出路径不存在，
5. 可以考虑使用`NamedTemporaryFile`来创建临时文件
6. 代码中需要有详细的注释，方便他人阅读
7. 代码注释使用中文，你的对代码的解释也使用中文
8. 代码中要有log信息，方便调试
9. 使用 `loguru` 而不是 `logging`
10. 使用 `pathlib` 而不是 `os.path`
11. 尽可能用 `pathlib` 的方法进行文件操作，例如用 `Path().open()` 代替 `open()`，用 `Path().read_text()` 代替 `open().read()` 等
12. 将字符串转为`Path`对象时，请尽量加上`expanduser()`方法，以便支持`~`符号
13. 打开文件不用指定编码，因为默认是utf-8
14. 如果没有必要，不要使用`try/except`捕获异常
15. 在`except`中不要引发新的异常，而是直接`raise`
16. 打印异常不用`str(e)`，直接打印`e`
17. `return`写在`else`中，不要写在`try`中
18. 如果需要引发异常，请不要将异常字符串直接写到异常的括号内，而是先定义一个异常变量`err_msg`，然后将`err_msg`写入异常括号内
19. `return`语句尽量不要写在`try`块内，而是写在`else`块内
20. 使用`trackback`库将异常的行号也打印出来
21. 类型提示尽可能使用python原生对象作为类型，例如`list`, `dict`, `tuple`等。而不是`typing`模块中的`List`, `Dict`, `Tuple`等。
22. 当你要添加命令行参数时，使用 `Fire` 库而不是 `argparse`
23. 可以使用`python-box`库加载`yaml`, `json`等配置文件
24. 文件的复制和移动使用`shutil`库
25. 需要进行多维数组的`shape`变换时，使用`einops`库的`rearrange`，`pack`等函数，而不是`transpose`,`stack`等函数
26. 不要使用`async/await`这种异步编程方式
