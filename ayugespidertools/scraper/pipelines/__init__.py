# Define your item pipelines here
#
# Don"t forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from ayugespidertools.scraper.pipelines.download.file import FilesDownloadPipeline
from ayugespidertools.scraper.pipelines.mongo.fantasy import AyuFtyMongoPipeline
from ayugespidertools.scraper.pipelines.mongo.twisted import AyuTwistedMongoPipeline
from ayugespidertools.scraper.pipelines.msgproducer.mqpub import AyuMQPipeline
from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline
from ayugespidertools.scraper.pipelines.mysql.asynced import AsyncMysqlPipeline
from ayugespidertools.scraper.pipelines.mysql.fantasy import AyuFtyMysqlPipeline
from ayugespidertools.scraper.pipelines.mysql.stats import AyuStatisticsMysqlPipeline
from ayugespidertools.scraper.pipelines.mysql.turbo import AyuTurboMysqlPipeline
from ayugespidertools.scraper.pipelines.mysql.twisted import AyuTwistedMysqlPipeline

__all__ = [
    "FilesDownloadPipeline",
    "AyuFtyMongoPipeline",
    "AyuTwistedMongoPipeline",
    "AyuMQPipeline",
    "AyuMysqlPipeline",
    "AsyncMysqlPipeline",
    "AyuFtyMysqlPipeline",
    "AyuStatisticsMysqlPipeline",
    "AyuTurboMysqlPipeline",
    "AyuTwistedMysqlPipeline",
]
