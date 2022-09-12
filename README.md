# AyugeSpiderTools 工具说明

> 本文章用于说明在爬虫开发中遇到的各种通用方法，将其打包成 Pypi 包以方便安装和使用，此工具会长久维护。

## 前言
在 `Python` 开发时会遇到一些经常使用的模块，为了更方便地使用这些模块，我们需要将其打包并发布到 `Pypi` 上。

此库的源码并非最新版（比如 scrapy 框架的扩展方法等），稍等会同步最新。其使用方法请在 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 项目中查看。

## 1. 前提条件

> `python 3.8+` 可以直接输入以下命令：

```shell
pip install ayugespidertools -i https://pypi.org/simple
```

> `python 3.8` 以下的版本，请自行安装以下依赖：

```ini
opencv-python = "^4.6.0"
numpy = "^1.23.1"
PyExecJS = "^1.5.1"
environs = "^9.5.0"
requests = "^2.28.1"
loguru = "^0.6.0"
Pillow = "^9.2.0"
PyMySQL = "^1.0.2"
```

## 2. 功能介绍

### 2.1. 数据格式化

> 目前此场景下的功能较少，后面会慢慢丰富其功能

#### 2.1.1. get_full_url

根据域名 `domain_name` 拼接 `deal_url` 来获得完整链接，示例如下：

```python
full_url = FormatData.get_full_url(domain_name="https://static.geetest.com", deal_url="/captcha_v3/batch/v3/2021-04-27T15/word/4406ba6e71cd478aa31e0dca37601cd4.jpg")
```

输出为：

```
https://static.geetest.com/captcha_v3/batch/v3/2021-04-27T15/word/4406ba6e71cd478aa31e0dca37601cd4.jpg
```

#### 2.1.2. click_point_deal

将小数 `decimal` 保留小数点后 `decimal_places` 位，结果四舍五入，示例如下：

```
res = FormatData.click_point_deal(13.32596516, 3)
```

输出为：

```
13.326
```

### 2.2. 图片相关操作

#### 2.2.1. 滑块验证码缺口距离识别

通过背景图片和缺口图片识别出滑块距离，示例如下：

```python
# 参数为图片全路径的情况
gap_distance = Picture.identify_gap("doc/image/2.jpg", "doc/image/1.png")
print("滑块验证码的缺口距离1为：", gap_distance)
assert gap_distance in list(range(205, 218))

# 参数为图片 bytes 的情况
with open("doc/image/1.png", "rb") as f:
target_bytes = f.read()
with open("doc/image/2.jpg", "rb") as f:
template_bytes = f.read()
gap_distance = Picture.identify_gap(template_bytes, target_bytes, "doc/image/33.png")
print("滑块验证码的缺口距离2为：", gap_distance)
```

#### 2.2.2. 滑块验证轨迹生成

根据滑块缺口的距离生成轨迹数组，目前也不是通用版。

```python
tracks = VerificationCode.get_normal_track(space=120)
```

### 2.3. Mysql 相关

`sql` 语句简单场景生成，目前是残废版，只适用于简单场景。

更多复杂的场景请查看 [directsql](https://pypi.org/project/directsql/#history), [python-sql](https://pypi.org/project/python-sql/#history) 和 [pypika](https://pypi.org/project/PyPika/#description) 的第三方库实现，以后会升级本库的方法。

```python
# mysql 连接
mysql_client = MysqlClient.MysqlOrm(NormalConfig.LOCAL_PYMYSQL_CONFIG)

# test_select_data
sql_pre, sql_after = SqlFormat.select_generate(db_table="newporj", key=["id", "title"], rule={"id|<=": 5}, order_by="id")
status, res = mysql_client.search_data(sql_pre, sql_after, type="one")

# test_insert_data
insert_sql, insert_value = SqlFormat.insert_generate(db_table="user", data={"name": "zhangsan", "age": 18})
mysql_client.insert_data(insert_sql, insert_value)

# test_update_data
update_sql, update_value = SqlFormat.update_generate(db_table="user", data={"score": 4}, rule={"name": "zhangsan"})
mysql_client.update_data(update_sql, update_value)
```

### 2.4. 自动化相关

目前是残废阶段，以后放上一些自动化相关操作

### 2.5. 执行 js 相关

鸡肋封装，以后会优化和添加多个功能

```python
# 测试运行 js 文件中的方法
js_res = RunJs.exec_js("doc/js/add.js", "add", 1, 2)
print("test_exec_js:", js_res)
assert js_res

# 测试运行 ctx 句柄中的方法
with open('doc/js/add.js', 'r', encoding='utf-8') as f:
    js_content = f.read()
ctx = execjs.compile(js_content)

js_res = RunJs.exec_js(ctx, "add", 1, 2)
print("test_exec_js_by_file:", js_res)
assert js_res
```

## 3. 总结

项目目前是初始阶段，以后会慢慢丰富 `python` 开发中的遇到的通用方法。

## TodoList

- [x] 添加常用的图片验证码中的图片处理方法
  - [x] 滑块缺口距离的识别方法
  - [x] 根据滑块距离生成轨迹数组的方法，以后会优化此方法
  - [x] 识别点选验证码位置及点击顺序，识别结果不太好，待优化
  - [ ] ... ...
- [ ] `scrapy` 的扩展功能开发（会优先更新此功能）
  - [ ] `scarpy` 结合 `crawlab` 的统计功能
  - [ ] `scrapy` 的 `middleware`, `pipeline` 等扩展（只需爬虫人员关注反爬及解析规则即可）。
    - [ ] 代理中间件
    - [ ] 请求头中间件
    - [ ] 使用 `selenum`，`pyppeteer` 来发送请求
    - [ ] `pipeline` 扩展会自动创建用户场景需要的表及字段格式
    - [ ] ... ...
- [x] 常用的数据处理相关
  - [x] `sql` 语句拼接，只是简单场景，后续优化
  - [x] `mongoDB` 语句拼接
  - [ ] 数据格式化处理，比如：去除网页标签，去除无效空格等
  - [ ] ... ...



