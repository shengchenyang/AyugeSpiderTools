from ayugespidertools.formatdata import DataHandle
from tests import tests_dir


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


def test_normal_to_stamp():
    normal_stamp = DataHandle.normal_to_stamp("Fri, 22 Jul 2022 01:43:06 +0800")
    assert normal_stamp == 1658425386

    normal_stamp = DataHandle.normal_to_stamp("Thu Jul 22 17:59:44 2022")
    assert normal_stamp == 1658483984

    normal_stamp = DataHandle.normal_to_stamp("2022-06-21 16:40:00")
    assert normal_stamp == 1655800800

    normal_stamp = DataHandle.normal_to_stamp(
        normal_time="20220815192255", _format_t="", specific_date_conn="", hms_conn=""
    )
    assert normal_stamp == 1660562575

    res = DataHandle.timestamp_to_normal(normal_stamp)
    assert res == "2022-08-15 19:22:55"

    normal_stamp = DataHandle.normal_to_stamp("2022/06/21 16:40:00")
    assert normal_stamp == 1655800800

    normal_stamp = DataHandle.normal_to_stamp("2022/06/21", date_is_full=False)
    assert normal_stamp == 1655740800

    # 当是英文的其他格式，或者混合格式时，需要自己自定时间格式化符
    normal_stamp = DataHandle.normal_to_stamp(
        normal_time="2022/Dec/21 16:40:00", _format_t="%Y/%b/%d %H:%M:%S"
    )
    assert normal_stamp == 1671612000


def test_remove_tags():
    @DataHandle.remove_all_tags
    def true_test_remove_tags(html_content):
        return f"{html_content}'<p>无事发生</p>'"

    res = true_test_remove_tags("""<a href="https://www.baidu.com">跳转到百度1</a>""")
    print(res)
    assert res is not None


def test_extract_html_to_md():
    with open(f"{tests_dir}/docs/txt/doc_with_table.html", "r", encoding="utf-8") as f:
        html_txt = f.read()
    res = DataHandle.extract_html_to_md(html_txt=html_txt)
    print(res)
    assert res is not None
