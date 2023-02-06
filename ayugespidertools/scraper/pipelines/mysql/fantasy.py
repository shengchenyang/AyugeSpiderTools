from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline

__all__ = ["AyuFtyMysqlPipeline"]


class AyuFtyMysqlPipeline(AyuMysqlPipeline):
    """
    Mysql 存储场景的 scrapy pipeline 扩展
    """

    def __init__(self, *args, **kwargs):
        super(AyuFtyMysqlPipeline, self).__init__(*args, **kwargs)
