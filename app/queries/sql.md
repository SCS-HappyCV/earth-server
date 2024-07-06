我上传了两个sql文件，其中`example.sql`是代码风格示例文件，另一个sql文件是数据库的表结构。

根据这两个文件，写出下面的sql语句：

1. delete_3d_segmentation_by_id
2. delete_2d_segmentation_by_id
3. delete_2d_detection_by_id
4. delete_2d_change_detection_by_id

具体来说有以下几个要求：

1. 所有的SQL语句都要以分号结尾
2. 必要时联表查询，查询出所有必要的字段
3. 尽可能查询出所有需要的字段
4. 使用MySQL语法
5. 使用PugSQL的命名参数
6. 不要加尾随的`RETURNING id`之类的语句
6. 尽可能的缩进和换行，使得SQL语句易读
7. `SELECT`子句中，不要出现`is_deleted`字段，在`WHERE`等其他子句中可以出现
8. 不要使用隐式重命名，使用`AS`关键字
9. 尽量不要用`JOIN`，而直接使用`,`来联表查询
10. 在名称之前加上`:name`，表示这个SQL语句的名字
11. 插入要在注释的末尾加上`:insert`
12. 获取一行要在注释的末尾加上`:one`
13. 获取多行要在注释的末尾加上`:many`
14. 获取一个值要在注释的末尾加上`:scalar`
15. 更新要在注释的末尾加上`:affected`
16. 多行插入和单行插入的语法是一样的
17. 可以使用`in`子句
18. 可以使用`update join`语法，但不要显式使用`join`子句，而是在`where`子句中使用`t1.c1 = t2.c2`的形式
