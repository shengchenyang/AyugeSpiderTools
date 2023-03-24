import os
import re
import subprocess

__all__ = [
    "AboutPyppeteer",
]


class AboutPyppeteer(object):
    """
    关于 Pyppeteer 的相关管理，目前只有在 Pyppeteer 卡住的时候及时释放的功能
    TODO: 此功能还不完善，等以后慢慢再优化
    """

    @classmethod
    def get_crawl_debug(cls, content: str) -> int:
        """
        获取日志中的采集信息连续信息的输出次数
        Args:
            content: 在日志文件中读出的内容信息

        Returns:
            len(res): Pyppeteer 连续信息的输出次数
        """
        pattern = re.compile(r"""(\[scrapy\.extensions\.logstats\] INFO: Crawled)""")
        res = pattern.findall(content)
        return len(res)

    @classmethod
    def quit_process(cls, process_name: str, sudo_pwd: str):
        """
        退出程序的方法
        Args:
            process_name: 需要关闭的进程名称
            sudo_pwd: sudo 需要输入的 root 账号密码

        Returns:
            None
        """
        command = (
            "ps aux | grep %s | grep -v grep | awk '{print $2}' | xargs sudo kill -9"
            % process_name
        )
        os.system(f"echo {sudo_pwd}|sudo -S {command}")

    @classmethod
    def deal_pyppeteer_suspend(cls, fn: str, line: int):
        """
        将 fn 全路径下的日志中出现 line 次卡住的日志所对应的进程杀掉
        Args:
            fn: 日志的全路径信息
            line: 日志重复输出为 line 次时处理次情况

        Returns:
            None
        """
        read_log = subprocess.getstatusoutput(f"tail -n {line} {fn}")

        # 当运行成功时
        if not read_log[0]:
            log_res = "".join(read_log[1])

            block_times = cls.get_crawl_debug(content=log_res)
            # 当连续输出 scrapy 的统计信息 3 次时，则卡住
            if block_times >= 3:
                # logger.info("quit process success")
                cls.quit_process(
                    process_name="curr_process", sudo_pwd="自行替换 sudo root 的密码"
                )

            # 当最新四行日志中未出现 scrapy 统计，则为正常状态，并清空日志
            elif block_times == 0:
                clean_log = subprocess.getstatusoutput(f"> {fn}")
