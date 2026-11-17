from ayugespidertools.formatdata import DataHandle


def test_get_full_url():
    full_url = DataHandle.get_full_url(
        domain_name="https://static.geetest.com",
        deal_url="/captcha_v3/batch/v3/2021-04-27T15/word/4406ba6e71cd478aa31e0dca37601cd4.jpg",
    )
    assert (
        full_url
        == "https://static.geetest.com/captcha_v3/batch/v3/2021-04-27T15/word/4406ba6e71cd478aa31e0dca37601cd4.jpg"
    )


def test_click_point_deal():
    res = DataHandle.click_point_deal(13.32596516, 3)
    assert res == 13.326


def test_remove_tags():
    @DataHandle.remove_all_tags
    def true_test_remove_tags(html_content):
        return f"{html_content}'<p>无事发生</p>'"

    res = true_test_remove_tags("""<a href="https://www.baidu.com">跳转到百度1</a>""")
    assert res is not None


def test_normal_display():
    @DataHandle.normal_display
    def true_test_normal_display(html_content):
        return f"{html_content}"

    res = true_test_normal_display("&lt;p&gt;Hello World&lt;/p&gt;")
    assert "<p>Hello World</p>" in res


def test_simple_deal_for_extract():
    @DataHandle.simple_deal_for_extract
    def true_test_simple_deal_for_extract(html_content):
        return html_content

    res = true_test_simple_deal_for_extract("123 ")
    assert res == "123"
    _data = {"demo": "demo_data"}
    res = true_test_simple_deal_for_extract(html_content=_data)
    assert res == _data
