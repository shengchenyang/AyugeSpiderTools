import warnings
from typing import TYPE_CHECKING, Tuple, Union

import requests
from retrying import retry

from ayugespidertools.common.encryption import EncryptOperation
from ayugespidertools.common.params import Param

try:
    import oss2
except ImportError:
    # pip install ayugespidertools[all]
    pass

warnings.filterwarnings("ignore")

__all__ = [
    "AliOssBase",
]

if TYPE_CHECKING:
    from ayugespidertools.common.typevars import NoneType, Str_Lstr


class AliOssBase:
    """阿里云 Oss 对象存储 python sdk 示例
    其 GitHub 官方文档地址：
        https://github.com/aliyun/aliyun-oss-python-sdk?spm=5176.8465980.tools.dpython-github.572b1450ON6Z9R
    阿里云官方 oss sdk 文档地址：
        https://www.alibabacloud.com/help/zh/object-storage-service/latest/python-quick-start
    """

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        bucket: str,
        doc: str,
    ) -> None:
        """初始化 auth，bucket 等信息
        注：阿里云账号 AccessKey 拥有所有 API 的访问权限，风险很高；
        强烈建议您创建并使用 RAM 用户进行 API 访问或日常运维，请登录 RAM 控制台创建 RAM 用户

        Args:
            access_key_id: 阿里云账号 AccessKey
            access_key_secret: 阿里云账号 AccessKey 对应的秘钥
            endpoint: 填写 Bucket 所在地域对应的 Endpoint；
                以华东1（杭州）为例，Endpoint 填写为 https://oss-cn-hangzhou.aliyuncs.com（注意二级域名等问题）
            bucket: 填写 Bucket 名称，此 oss 项目所属 bucket
            doc: 需要操作的 oss 文件夹目录
        """
        self.endpoint = endpoint
        self.doc = doc
        self.bucket = bucket
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, f"{self.endpoint}/", self.bucket)
        self.headers = {"Connection": "close"}

    def delete_oss(self, del_logo_url: str):
        """删除单个文件: 以下代码用于删除 bucket 中的 del_logo_url 所对应的文件

        Args:
            del_logo_url: 需要参数的阿里云链接全路径 url
        """
        try:
            self.bucket.delete_object(
                f"{self.doc}/{del_logo_url.replace(f'{self.endpoint}/{self.doc}/', '')}"
            )
        except oss2.exceptions.NoSuchKey as e:
            raise ValueError(
                f"delete_oss error: status={e.status}, request_id={e.request_id}"
            ) from e

    @retry(
        stop_max_attempt_number=Param.retry_num, retry_on_result=lambda x: x[0] is False
    )
    def put_oss(
        self,
        put_bytes_or_url: Union[str, bytes],
        file_name: str,
        file_format: str,
        file_name_md5: bool = False,
    ) -> Tuple[bool, str]:
        """上传单个文件的 bytes 内容

        Args:
            put_bytes_or_url: 需要上传的文件 bytes 内容或链接
            file_name: 需要上传的文件的名称
            file_format: 需要上传的文件格式，比如：jpg, png, wav 等
            file_name_md5: 文件名称是否需要 md5 处理

        Returns:
            1): 上传状态，是否成功
            2): 上传成功至 Oss 的目标 url
        """
        assert type(put_bytes_or_url) in [str, bytes], "参数：上传的文件需要是 str 或 bytes 格式"

        input_file_name = (
            EncryptOperation.md5(file_name) if file_name_md5 else file_name
        )
        if isinstance(put_bytes_or_url, str):
            put_bytes_or_url = requests.get(
                url=put_bytes_or_url, headers=self.headers, verify=False
            ).content

        try:
            self.bucket.put_object(
                f"{self.doc}/{input_file_name}.{file_format}",
                put_bytes_or_url,
            )
        except Exception:
            return False, ""
        return True, input_file_name

    def enumer_file_by_pre(
        self,
        prefix: str,
        count_by_type: Union["Str_Lstr", "NoneType", list] = None,
    ) -> list:
        """列举 prefix 文件夹下的所有的 count_by_type 类型的文件元素

        Args:
            prefix: 文件夹目录
            count_by_type: 统计的依据，计数文件夹中的此类型的元素
                参数示例如下:
                    1. amr
                    2. ["amr", "mp3", "m4a", "wav", "aac", "ogg", "flac", "wma"]

        Returns:
            1). prefix 目录下的符合规则的文件列表
        """
        assert type(count_by_type) in [
            str,
            list,
            "NoneType",
        ], "计数依据的参数类型需要是 str 或 list"

        # 如果依据为空，则统计目标目录下的所有文件
        obj_list = list(oss2.ObjectIterator(self.bucket, prefix=prefix))
        if not count_by_type:
            return [obj.key for obj in obj_list][1:]

        # 返回符合单个约束的元素集
        if isinstance(count_by_type, str):
            return [obj.key for obj in obj_list if str(obj.key).endswith(count_by_type)]

        key_list: list = []
        for count_by in count_by_type:
            res = [obj.key for obj in obj_list if str(obj.key).endswith(count_by)]
            key_list = key_list + res
        return key_list
