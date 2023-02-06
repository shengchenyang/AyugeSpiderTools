import execjs

__all__ = [
    "exec_js",
]


def exec_js(js_handle, method, *args):
    """
    执行 js_full_path 的 js 文件中的 method 方法
    Args:
        js_handle: js 处理对象，可能是 js_full_path 的全路径，也可能是 js 的 ctx 句柄
        method: 需要调用的 js 方法名
        *args: 调用的目标函数所需要的参数

    Returns:
        1). js 执行后的结果
    """
    # 先判断是否有 ctx 对象，如果有的话，直接调用 ctx 的方法即可，不用重复构造 ctx 对象
    if any(
        [
            type(js_handle) != str,
            type(js_handle) == execjs._external_runtime.ExternalRuntime.Context,
        ]
    ):
        return js_handle.call(method, *args)

    # 没有 ctx 句柄则需要创建此对象
    with open(js_handle, "r", encoding="utf-8") as f:
        js_content = f.read()
    ctx = execjs.compile(js_content)
    return ctx.call(method, *args)
