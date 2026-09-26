from __future__ import annotations

from typing import Any

from ayugespidertools.exceptions import NotConfigured

try:
    import alibabacloud_oss_v2 as oss
except ImportError:
    raise NotConfigured(
        "missing alibabacloud-oss-v2 library, please install it. "
        "install command: pip install ayugespidertools[all]"
    )

__all__ = [
    "AliOssBase",
]


class AliOssBase:
    """alibabacloud Oss python sdk demo
    GitHub docs：
        https://github.com/aliyun/alibabacloud-oss-python-sdk-v2
    alibabacloud Oss sdk docs：
        https://www.alibabacloud.com/help/zh/oss/developer-reference
    """

    def __init__(
        self,
        access_key: str,
        access_secret: str,
        endpoint: str,
        region: str,
        bucket: str,
        doc: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """create OSS client

        Args:
            access_key: your access key id
            access_secret: your access key secret
            endpoint: The endpoint corresponding to the location of the bucket
            region: The region corresponding to the location of the endpoint, see the link:
                https://www.alibabacloud.com/help/zh/oss/user-guide/regions-and-endpoints
            bucket: bucket name
            doc: The OSS folder directory to be operated on，such as: file/img
        """
        self.endpoint = endpoint.rstrip("/")
        self.doc = doc
        self.bk = bucket
        credentials_provider = oss.credentials.StaticCredentialsProvider(
            access_key, access_secret
        )
        config = oss.config.load_default()
        config.credentials_provider = credentials_provider
        config.endpoint = (
            self.endpoint
            if self.endpoint.startswith(("http://", "https://"))
            else f"https://{self.endpoint}"
        )
        if not region:
            config.region = (
                self.endpoint.removeprefix("https://")
                .removeprefix("http://")
                .removeprefix("oss-")
                .removesuffix(".aliyuncs.com")
            )
        else:
            config.region = region
        self.client = oss.Client(config)

    def put_oss(self, put_bytes: bytes, file: str) -> None:
        """Upload a single file

        Args:
            put_bytes: The file to be uploaded (bytes content)
            file: upload file name
        """
        assert isinstance(put_bytes, bytes), "put_bytes needs to be in bytes format"

        oss_file_path = f"{self.doc}/{file}" if self.doc else file
        self.client.put_object(
            oss.PutObjectRequest(
                bucket=self.bk,
                key=oss_file_path,
                body=put_bytes,
            )
        )

    def get_full_link(self, file: str) -> str:
        """Get the full link to the file

        Args:
            file: current file

        Returns:
            1). full link to the current file
        """
        ep = self.endpoint.replace("https://", "", 1).replace("http://", "", 1)
        oss_file_path = f"{self.doc}/{file}" if self.doc else file
        return f"https://{self.bk}.{ep}/{oss_file_path}"
