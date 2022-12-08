# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import json
import time
import base64
import random
import requests
import traceback
import numpy as np
from retrying import retry
from scrapy import signals
from typing import Optional
from threading import Thread
from scrapy.http import HtmlResponse
from scrapy.settings import Settings
from .config import NormalConfig, logger
from .common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Params import Param
from ayugespidertools.common.Utils import ToolsForAyu
from scrapy.utils.project import get_project_settings
from WorkWeixinRobot.work_weixin_robot import WWXRobot
from scrapy.utils.response import response_status_message
from scrapy.downloadermiddlewares.retry import RetryMiddleware


__all__ = [
    "RandomRequestUaMiddleware",
    "DynamicProxyDownloaderMiddleware",
    "ExclusiveProxyDownloaderMiddleware",
    "AbuDynamicProxyDownloaderMiddleware",
    "RequestByRequestsMiddleware",
]


class RandomRequestUaMiddleware(object):
    """
    随机请求头中间件
    """
    def get_random_ua_by_weight(self) -> str:
        """根据权重来获取随机请求头 ua 信息"""
        # 带权重的 ua 列表，将比较常用的 ua 标识的权重设置高一点。这里是根据 fake_useragent 库中的打印信息来规划权重的。
        ua_arr = [
            {"explorer_type": "opera", "weight": 16},
            {"explorer_type": "safari", "weight": 32},
            {"explorer_type": "internetexplorer", "weight": 41},
            {"explorer_type": "firefox", "weight": 124},
            {"explorer_type": "chrome", "weight": 772},
        ]
        curr_ua_type = ReuseOperation.random_weight(weight_data=ua_arr)
        curr_ua_list = Param.fake_useragent_dict[curr_ua_type["explorer_type"]]
        curr_ua = random.choice(curr_ua_list)
        return curr_ua

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        logger.info(f"随机请求头中间件 RandomRequestUaMiddleware 已开启，生效脚本为: %s" % spider.name)
        # spider.logger.info("RandomRequestUaMiddleware opened: %s" % spider.name)

    def process_request(self, request, spider):
        curr_ua = self.get_random_ua_by_weight()
        if curr_ua:
            request.headers.setdefault(b"User-Agent", curr_ua)
            spider.logger.info("RandomRequestUaMiddleware 当前使用的 ua 为: %s" % curr_ua)


class DynamicProxyDownloaderMiddleware(object):
    """
    动态隧道代理中间件
    """
    def __init__(self, settings):
        """
        从 scrapy 配置中取出动态隧道代理的信息
        """
        dynamic_proxy_config = settings.get("DYNAMIC_PROXY_CONFIG", None)
        # 查看动态隧道代理配置是否符合要求
        is_match = ReuseOperation.if_dict_meet_min_limit(
            dict_config=dynamic_proxy_config,
            key_list=["PROXY_URL", "USERNAME", "PASSWORD"]
        )
        assert is_match, f"没有配置动态隧道代理，配置示例为：{Param.dynamic_proxy_config_example}"

        self.proxy_url = dynamic_proxy_config["PROXY_URL"]
        self.username = dynamic_proxy_config["USERNAME"]
        self.password = dynamic_proxy_config["PASSWORD"]

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.settings)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # TODO: 根据权重来随机获取一个账号 DYNAMIC_PROXY_CONFIG
        # account = ReuseOperation.random_weight(self.account_arr)
        if request.url.startswith("https://"):
            request.meta['proxy'] = f"https://{self.username}:{self.password}@{self.proxy_url}/"
        elif request.url.startswith("http://"):
            request.meta['proxy'] = f"http://{self.username}:{self.password}@{self.proxy_url}/"
        else:
            spider.logger.info(f"request url: {request.url} error when use proxy middlewares!")

        # 避免因连接复用导致隧道不能切换 IP
        request.headers["Connection"] = "close"
        # 采用 gzip 压缩加速访问
        request.headers["Accept-Encoding"] = "gzip"

    def spider_opened(self, spider):
        logger.info(f"动态隧道代理中间件: DynamicProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}")


class ExclusiveProxyDownloaderMiddleware(object):
    """
    独享代理中间件
    """

    def __init__(self, exclusive_proxy_config):
        """
        初始化独享代理设置
        Args:
            exclusive_proxy_config: 使用的独享代理的配置信息
        """
        self.proxy = None
        # 查看独享代理配置是否符合要求
        is_match = ReuseOperation.if_dict_meet_min_limit(
            dict_config=exclusive_proxy_config,
            key_list=["PROXY_URL", "USERNAME", "PASSWORD", "PROXY_INDEX"]
        )
        assert is_match, f"没有配置独享代理，配置示例为：{Param.exclusive_proxy_config_example}"

        self.proxy_url = exclusive_proxy_config["PROXY_URL"]
        self.username = exclusive_proxy_config["USERNAME"]
        self.password = exclusive_proxy_config["PASSWORD"]
        self.proxy_index = exclusive_proxy_config["PROXY_INDEX"]

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(
            exclusive_proxy_config=crawler.settings.get("EXCLUSIVE_PROXY_CONFIG", None)
        )
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def get_proxy_ip(self):
        """获取独享代理接口的索引为 proxy_index 的代理信息"""
        try:
            r = requests.get(self.proxy_url)
            proxy_list = r.json().get("data").get("proxy_list")
            proxy_list.sort()
            if self.proxy_index < len(proxy_list):
                self.proxy = proxy_list[self.proxy_index]
            else:
                raise Exception("独享代理索引超出范围，请确认独享代理服务情况。")

        except Exception:
            raise Exception("获取独享代理是失败，请及时查看。")

    def process_request(self, request, spider):
        if request.url.startswith("https://"):
            request.meta["proxy"] = "https://{}".format(self.proxy)
        elif request.url.startswith("http://"):
            request.meta["proxy"] = "http://{}".format(self.proxy)
        else:
            spider.logger.info(f"request url error: {request.url}")

        proxy_user_pass = self.username + ":" + self.password
        encoded_user_pass = "Basic " + base64.urlsafe_b64encode(bytes(proxy_user_pass, "ascii")).decode("utf8")
        request.headers["Proxy-Authorization"] = encoded_user_pass

    def spider_opened(self, spider):
        self.get_proxy_ip()
        logger.info(f"独享代理中间件: ExclusiveProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}，当前独享代理为: {self.proxy}")


class SiMiProxyDownloaderMiddleware(RetryMiddleware):
    """
    基于独享代理的自定义动态代理中间件
    """

    def __init__(self):
        self.settings = Settings()
        super(SiMiProxyDownloaderMiddleware, self).__init__(self.settings)
        self.important_error = False
        self.WWX = WWXRobot(key=NormalConfig.WWXRobot_key)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    @retry(stop_max_attempt_number=Param.retry_num)
    def get_proxy_ip(self, size, isdict: Optional[bool] = None):
        proxy_url = "http://dps.kdlapi.com/api/getdps?orderid={}&num={}&signature={}&format=json".format(
            self.simidaili_config["orderid"], size, self.simidaili_config["signature"]
        )
        if not self.important_error:
            try:
                r = requests.get(proxy_url).json()
            except Exception:
                raise ValueError("快代理请求获取 ip 无响应，请检查是否能够正常访问快代理或者 nacos 的配置是否以及失效！")
        else:
            raise ValueError("ip 获取方式有误，请重构私密代理中间件获取 ip 的模块！")

        if r["code"] == 0:
            try:
                iplist = r.get("data").get("proxy_list")
                now_ipnum = r.get("data").get("today_left_count")
                if iplist and now_ipnum:
                    if (now_ipnum < 100) and (now_ipnum >= 50):
                        self.WWX.send_text("私密代理三级警报：相关部门请注意，ip 数量已经少于 100 个！请及时充值！")
                    elif (now_ipnum < 50) and (now_ipnum >= 10):
                        self.WWX.send_text("私密代理二级警报：相关部门请注意，相关部门请注意, ip 数量已经少 50 个！请及时充值！")
                    elif now_ipnum < 10:
                        self.WWX.send_text("私密代理一级警报：相关部门请注意，，相关部门请注意，相关部门请注意, ip 数量已经少于 10 个！请及时充值！")

                    if isdict:
                        self.proxy_list = iplist
                    else:
                        return iplist
                else:
                    raise ValueError("ip 获取方式有误，请重构私密代理中间件获取 ip 的模块！")
            except:
                self.important_error = True
                traceback.print_exc()
                raise ValueError("ip 获取方式有误，请重构私密代理中间件获取ip的模块！")

        else:
            msg = r.get("msg")
            if msg:
                self.WWX.send_text(f"私密代理特级警报：私密代理出现错误，错误原因是: {msg}")
                raise ValueError(f"获取私密ip失败，原因是：{msg}")
            else:
                self.important_error = True
                raise ValueError("ip 获取方式有误，请重构私密代理中间件获取 ip 的模块！")

    def process_request(self, request, spider):
        # 初始化请求，随机选定一个 ip 进行访问
        current_ip_index = np.argmin(self.v_count)
        current_ip = self.proxy_list[current_ip_index]

        # 统计请求速率
        self.reqnum_count[current_ip_index] += 1.0
        self.v_sum()
        # logger.debugger(f"目前的平均请求速度为：{np.average(self.v_count)}")

        if request.url.startswith("https://"):
            request.meta["proxy"] = "https://{}".format(current_ip)
        elif request.url.startswith("http://"):
            request.meta["proxy"] = "http://{}".format(current_ip)
        else:
            spider.logger.info(f"request url error: {request.url}")

        # request.meta["proxy"] = "http://{}".format(current_ip)
        request.meta["dont_retry"] = True
        # request.meta["ja3"] = True
        proxy_user_pass = self.username + ":" + self.password
        encoded_user_pass = "Basic " + base64.urlsafe_b64encode(bytes(proxy_user_pass, "ascii")).decode("utf8")
        request.headers["Proxy-Authorization"] = encoded_user_pass

    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            # 如果出现返回异常的状态码则更换ip进行请求
            current_ip_index = np.argmin(self.v_count)
            current_ip = self.proxy_list[current_ip_index]

            # 统计请求速率
            self.reqnum_count[current_ip_index] += 1
            self.v_sum()

            if request.url.startswith("https://"):
                request.meta["proxy"] = "https://{}".format(current_ip)
            elif request.url.startswith("http://"):
                request.meta["proxy"] = "http://{}".format(current_ip)
            else:
                spider.logger.info(f"request url error: {request.url}")
            # request.meta["proxy"] = "http://{}".format(current_ip)
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            current_ip = request.meta["proxy"].split(""//"")[-1]
            url = "https://dps.kdlapi.com/api/checkdpsvalid?orderid={}&signature={}&proxy={}".format(
                self.simidaili_config["orderid"], self.simidaili_config["signature"],
                current_ip)
            is_exists = requests.get(url).json()
            if not is_exists["data"][current_ip]:
                if current_ip in self.proxy_list:
                    spider.logger.info("更新ip")
                    # 找到相应索引，并删除相应时间统计数组、ip列表以及请求次数统计数组相应索引上的值
                    current_ip_index = self.proxy_list.index(current_ip)
                    self.proxy_list.pop(current_ip_index)
                    self.time_count = np.delete(self.time_count, current_ip_index, axis=0)
                    self.reqnum_count = np.delete(self.reqnum_count, current_ip_index, axis=0)

                    # 如果平均速度大于每个 ip 4 次每秒，或者 ip 池子小于 1 时，则增加两个 ip，否则不予增加。
                    if (np.average(self.v_count) >= 4.5) and (len(self.proxy_list) < 7):
                        for new_ip in self.get_proxy_ip(2):
                            self.proxy_list.append(new_ip)
                            self.time_count = np.append(self.time_count, 0.5)
                            self.reqnum_count = np.append(self.reqnum_count, 0)
                            current_ip = new_ip
                            self.reqnum_count[-1] += 1
                    elif len(self.proxy_list) < self.proxypool_size:
                        new_ip = self.get_proxy_ip(1)[0]
                        self.proxy_list.append(new_ip)
                        self.time_count = np.append(self.time_count, 0.5)
                        self.reqnum_count = np.append(self.reqnum_count, 0)
                        current_ip = new_ip
                        self.reqnum_count[-1] += 1
                    else:
                        current_ip_index = np.argmin(self.v_count)
                        current_ip = self.proxy_list[current_ip_index]
                        self.reqnum_count[current_ip_index] += 1

                    spider.logger.info(f"目前 ip 池存量 ip 数量为：{len(self.proxy_list)}")
                    self.v_sum()
                else:
                    current_ip_index = np.argmin(self.v_count)
                    current_ip = self.proxy_list[current_ip_index]
                    self.reqnum_count[current_ip_index] += 1
                    self.v_sum()

            if request.url.startswith("https://"):
                request.meta["proxy"] = "https://{}".format(current_ip)
            elif request.url.startswith("http://"):
                request.meta["proxy"] = "http://{}".format(current_ip)
            else:
                spider.logger.info(f"request url error: {request.url}")
            # request.meta["proxy"] = "http://{}".format(current_ip)
            return self._retry(request, exception, spider)

    def v_sum(self):
        self.v_count = self.reqnum_count / self.time_count

    def clock(self, spider):
        while not self.end_time:
            time.sleep(0.2)
            self.time_count = np.add(self.time_count, 0.2)

    def spider_opened(self, spider):
        settings = get_project_settings()
        # TODO: 根据 nacos/consul 获取代理配置信息
        # resx = get_nacos_config(env="prod", data_id="KUAI_PROXY_PRIVATE")
        resx = json.dumps({"username": "***", "password": "***"})
        self.simidaili_config = json.loads(resx)
        self.username = self.simidaili_config["username"]
        self.password = self.simidaili_config["password"]

        if settings.get("SMPPSIZE"):
            if settings.get("SMPPSIZE") < 1:
                raise ValueError("您输入的 ip 池子大小不能小于 1！请重新修改 settings 中的 SMPPSIZE 的值为大于等于 1")
            elif settings.get("SMPPSIZE") > 7:
                raise ValueError("你礼貌吗，ip 池最大数量不可以超过 7 个！请重新设置！")

            self.proxypool_size = settings.get("SMPPSIZE")
        else:
            self.proxypool_size = 1
        self.end_time = False
        self.time_count = np.zeros((self.proxypool_size,)) + 0.5
        self.reqnum_count = np.zeros((self.proxypool_size,))
        self.v_sum()
        self.t = Thread(target=self.clock, args=(spider,), daemon=True)
        self.t.start()
        self.get_proxy_ip(self.proxypool_size, True)
        spider.logger.info(f"初始化 ip 字典，ip 数量为：{len(self.proxy_list)}")
        spider.logger.info("SiMiProxyDownloaderMiddleware opened: %s" % spider.name)

    def spider_closed(self, spider):
        self.end_time = True
        self.t.join()
        spider.logger.info("SiMiProxyDownloaderMiddleware closed: %s" % spider.name)


class AbuDynamicProxyDownloaderMiddleware(object):
    """
    阿布云动态代理 - 隧道验证方式（其实和快代理的写法一致）
    """

    def __init__(self, settings):
        """
        从 scrapy 配置中取出动态隧道代理的信息
        Args:
            settings: scrapy 配置信息
        """
        dynamic_proxy_config = settings.get("DYNAMIC_PROXY_CONFIG", None)
        # 查看动态隧道代理配置是否符合要求
        is_match = ReuseOperation.if_dict_meet_min_limit(
            dict_config=dynamic_proxy_config,
            key_list=["PROXY_URL", "USERNAME", "PASSWORD"]
        )
        assert is_match, f"没有配置动态隧道代理，配置示例为：{Param.dynamic_proxy_config_example}"

        self.proxy_url = dynamic_proxy_config["PROXY_URL"]
        self.username = dynamic_proxy_config["USERNAME"]
        self.password = dynamic_proxy_config["PASSWORD"]

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.settings)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        logger.info(f"阿布云动态隧道代理中间件: AbuDynamicProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}")

    def process_request(self, request, spider):
        if request.url.startswith("https://"):
            request.meta["proxy"] = "https://{}".format(self.proxy_url)
        elif request.url.startswith("http://"):
            request.meta["proxy"] = "http://{}".format(self.proxy_url)
        else:
            spider.logger.info(f"request url error: {request.url}")

        proxy_user_pass = self.username + ":" + self.password
        encoded_user_pass = "Basic " + base64.urlsafe_b64encode(bytes(proxy_user_pass, "ascii")).decode("utf8")
        request.headers["Proxy-Authorization"] = encoded_user_pass


class RequestByRequestsMiddleware(object):
    """
    将 scrapy 的 Request 请求替换为 requests
    """

    def process_request(self, request, spider):
        try:
            # 将 scrapy 的 request headers 的值，原封不动地转移到 requests 中
            r_headers = ToolsForAyu.get_dict_form_scrapy_req_headers(scrapy_headers=request.headers)

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
                        timeout=(Param.requests_req_timeout, Param.requests_res_timeout)
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
                        timeout=(Param.requests_req_timeout, Param.requests_res_timeout)
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
                        timeout=(Param.requests_req_timeout, Param.requests_res_timeout)
                    )

                else:
                    post_data_dict = {x.split("=")[0]: x.split("=")[1] for x in request_body_str.split("&")}
                    r_response = requests.request(
                        method=scrapy_request_method,
                        url=request.url,
                        headers=r_headers,
                        data=post_data_dict,
                        cookies=request.cookies,
                        verify=False,
                        timeout=(Param.requests_req_timeout, Param.requests_res_timeout)
                    )
            else:
                raise Exception("出现未知请求方式，请及时查看！")
            return HtmlResponse(url=request.url, status=r_response.status_code, body=r_response.text, request=request, encoding="utf-8")

        except Exception as e:
            """这里比较重要，还是推荐捕获所有错误；不建议只抛错 requests.exceptions.ConnectTimeout:"""
            return HtmlResponse(url=request.url, status=202, body=f"requests 请求出现错误：{e}", request=request, encoding="utf-8")
