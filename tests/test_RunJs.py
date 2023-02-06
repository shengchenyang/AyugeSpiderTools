import execjs

from ayugespidertools import RunJs


def test_exec_js_by_file():
    """
    测试运行 ctx 句柄中的方法
    Returns:
        None
    """
    # 测试运行 js 文件中的方法
    js_res = RunJs.exec_js("docs/js/add.js", "add", 1, 2)
    print("test_exec_js:", js_res)
    assert js_res == 3

    # 测试运行 ctx 句柄中的方法
    with open("docs/js/add.js", "r", encoding="utf-8") as f:
        js_content = f.read()
    ctx = execjs.compile(js_content)

    js_res = RunJs.exec_js(ctx, "add", 1, 2)
    print("test_exec_js_by_file:", js_res)
    assert js_res == 3
