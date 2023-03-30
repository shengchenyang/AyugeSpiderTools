import base64
import json
import time
import traceback
from threading import Thread
from typing import Optional

import numpy as np
import requests
from retrying import retry
from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.settings import Settings
from scrapy.utils.project import get_project_settings
from scrapy.utils.response import response_status_message
from WorkWeixinRobot.work_weixin_robot import WWXRobot

from ayugespidertools.common.Params import Param


class PrivateProxyDownloaderMiddleware(RetryMiddleware):
    """
    基于独享代理的自定义动态代理中间件，此中间件暂不使用，后期优化
    """

    def __init__(self, wwx_robot_key: str):
        self.settings = Settings()
        super(PrivateProxyDownloaderMiddleware, self).__init__(self.settings)
        self.important_error = False
        self.WWX = WWXRobot(key=wwx_robot_key)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(wwx_robot_key=crawler.settings.get("WWXRobot_key", None))
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    @retry(stop_max_attempt_number=Param.retry_num)
    def get_proxy_ip(self, size, isdict: Optional[bool] = None):
        proxy_url = f"http://dps.kdlapi.com/api/getdps?orderid={self.simidaili_conf['orderid']}&num={size}&signature={self.simidaili_conf['signature']}&format=json"
        if self.important_error:
            raise ValueError("ip 获取方式有误，请重构私密代理中间件获取 ip 的模块！")

        try:
            r = requests.get(proxy_url).json()
        except Exception as e:
            raise ValueError("快代理请求获取 ip 无响应，请检查是否能够正常访问快代理或者 nacos 的配置是否以及失效！") from e

        if r["code"] == 0:
            try:
                iplist = r.get("data").get("proxy_list")
                now_ipnum = r.get("data").get("today_left_count")
                if iplist and now_ipnum:
                    if (now_ipnum < 100) and (now_ipnum >= 50):
                        self.WWX.send_text("私密代理三级警报：相关部门请注意，ip 数量已经少于 100 个！请及时充值！")
                    elif (now_ipnum < 50) and (now_ipnum >= 10):
                        self.WWX.send_text(
                            "私密代理二级警报：相关部门请注意，相关部门请注意, ip 数量已经少 50 个！请及时充值！"
                        )
                    elif now_ipnum < 10:
                        self.WWX.send_text(
                            "私密代理一级警报：相关部门请注意，，相关部门请注意，相关部门请注意, ip 数量已经少于 10 个！请及时充值！"
                        )

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

        elif msg := r.get("msg"):
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
        # spider.slog.debugger(f"目前的平均请求速度为：{np.average(self.v_count)}")

        if request.url.startswith("https://"):
            request.meta["proxy"] = f"https://{current_ip}"
        elif request.url.startswith("http://"):
            request.meta["proxy"] = f"http://{current_ip}"
        else:
            spider.slog.info(f"request url error: {request.url}")

        # request.meta["proxy"] = "http://{}".format(current_ip)
        request.meta["dont_retry"] = True
        # request.meta["ja3"] = True
        proxy_user_pass = f"{self.username}:{self.password}"
        encoded_user_pass = "Basic " + base64.urlsafe_b64encode(
            bytes(proxy_user_pass, "ascii")
        ).decode("utf8")
        request.headers["Proxy-Authorization"] = encoded_user_pass

    def process_response(self, request, response, spider):
        if response.status not in self.retry_http_codes:
            return response
        # 如果出现返回异常的状态码则更换ip进行请求
        current_ip_index = np.argmin(self.v_count)
        current_ip = self.proxy_list[current_ip_index]

        # 统计请求速率
        self.reqnum_count[current_ip_index] += 1
        self.v_sum()

        if request.url.startswith("https://"):
            request.meta["proxy"] = f"https://{current_ip}"
        elif request.url.startswith("http://"):
            request.meta["proxy"] = f"http://{current_ip}"
        else:
            spider.slog.error(f"request url error: {request.url}")
        # request.meta["proxy"] = "http://{}".format(current_ip)
        reason = response_status_message(response.status)
        return self._retry(request, reason, spider) or response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            current_ip = request.meta["proxy"].split("" // "")[-1]
            url = "https://dps.kdlapi.com/api/checkdpsvalid?orderid={}&signature={}&proxy={}".format(
                self.simidaili_conf["orderid"],
                self.simidaili_conf["signature"],
                current_ip,
            )
            is_exists = requests.get(url).json()
            if not is_exists["data"][current_ip]:
                if current_ip in self.proxy_list:
                    spider.slog.info("更新ip")
                    # 找到相应索引，并删除相应时间统计数组、ip列表以及请求次数统计数组相应索引上的值
                    current_ip_index = self.proxy_list.index(current_ip)
                    self.proxy_list.pop(current_ip_index)
                    self.time_count = np.delete(
                        self.time_count, current_ip_index, axis=0
                    )
                    self.reqnum_count = np.delete(
                        self.reqnum_count, current_ip_index, axis=0
                    )

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

                    spider.slog.info(f"目前 ip 池存量 ip 数量为：{len(self.proxy_list)}")
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
                spider.slog.info(f"request url error: {request.url}")
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
        resx = json.dumps({"username": "***", "password": "***"})
        self.simidaili_conf = json.loads(resx)
        self.username = self.simidaili_conf["username"]
        self.password = self.simidaili_conf["password"]

        if settings.get("SMPPSIZE"):
            if settings.get("SMPPSIZE") < 1:
                raise ValueError(
                    "您输入的 ip 池子大小不能小于 1！请重新修改 settings 中的 SMPPSIZE 的值为大于等于 1"
                )
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
        spider.slog.info(f"初始化 ip 字典，ip 数量为：{len(self.proxy_list)}")
        spider.slog.info(f"PrivateProxyDownloaderMiddleware opened: {spider.name}")

    def spider_closed(self, spider):
        self.end_time = True
        self.t.join()
        spider.slog.info(f"PrivateProxyDownloaderMiddleware closed: {spider.name}")
