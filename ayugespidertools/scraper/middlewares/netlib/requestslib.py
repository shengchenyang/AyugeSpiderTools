import requests
from scrapy.http import HtmlResponse

from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Params import Param
from ayugespidertools.common.Utils import ToolsForAyu


class RequestByRequestsMiddleware(object):
    """
    将 scrapy 的 Request 请求替换为 requests
    """

    def process_request(self, request, spider):
        try:
            # 将 scrapy 的 request headers 的值，原封不动地转移到 requests 中
            r_headers = ToolsForAyu.get_dict_form_scrapy_req_headers(
                scrapy_headers=request.headers
            )

            request_body_str = str(request.body, encoding="utf-8")
            scrapy_request_method = str(request.method).upper()
            if scrapy_request_method == "GET":
                # 普通 GET 请求
                if not request.body:
                    r_response = requests.request(
                        method=scrapy_request_method,
                        url=request.url,
                        headers=r_headers,
                        cookies=request.cookies,
                        verify=False,
                        timeout=(
                            Param.requests_req_timeout,
                            Param.requests_res_timeout,
                        ),
                    )

                # 携带 body 参数的 GET 请求
                else:
                    r_response = requests.request(
                        method=scrapy_request_method,
                        url=request.url,
                        headers=r_headers,
                        cookies=request.cookies,
                        data=request_body_str,
                        verify=False,
                        timeout=(
                            Param.requests_req_timeout,
                            Param.requests_res_timeout,
                        ),
                    )

            elif scrapy_request_method == "POST":
                # POST 请求的情况是要判断其格式，如果是 json 的格式传来，则需要 requests 的 json.dumps 格式的 data 值
                if ReuseOperation.judge_str_is_json(judge_str=request_body_str):
                    r_response = requests.request(
                        method=scrapy_request_method,
                        url=request.url,
                        headers=r_headers,
                        data=request_body_str,
                        cookies=request.cookies,
                        verify=False,
                        timeout=(
                            Param.requests_req_timeout,
                            Param.requests_res_timeout,
                        ),
                    )

                else:
                    post_data_dict = {
                        x.split("=")[0]: x.split("=")[1]
                        for x in request_body_str.split("&")
                    }
                    r_response = requests.request(
                        method=scrapy_request_method,
                        url=request.url,
                        headers=r_headers,
                        data=post_data_dict,
                        cookies=request.cookies,
                        verify=False,
                        timeout=(
                            Param.requests_req_timeout,
                            Param.requests_res_timeout,
                        ),
                    )
            else:
                raise ValueError("出现未知请求方式，请及时查看！")
            return HtmlResponse(
                url=request.url,
                status=r_response.status_code,
                body=r_response.text,
                request=request,
                encoding="utf-8",
            )

        except Exception as e:
            # 这里比较重要，还是推荐捕获所有错误；不建议只抛错 requests.exceptions.ConnectTimeout:
            return HtmlResponse(
                url=request.url,
                status=202,
                body=f"requests 请求出现错误：{e}",
                request=request,
                encoding="utf-8",
            )
