from ayugespidertools.config import setup_lazy_import

_MODULES = {
    "download.file": ["FilesDownloadPipeline"],
    "es.asynced": ["AyuAsyncESPipeline"],
    "es.fantasy": ["AyuFtyESPipeline"],
    "mongo.asynced": ["AyuAsyncMongoPipeline"],
    "mongo.fantasy": ["AyuFtyMongoPipeline"],
    "mongo.twisted": ["AyuTwistedMongoPipeline"],
    "msgproducer.kafkapub": ["AyuKafkaPipeline"],
    "msgproducer.mqpub": ["AyuMQPipeline"],
    "msgproducer.mqasyncpub": ["AyuAsyncMQPipeline"],
    "mysql.asynced": ["AyuAsyncMysqlPipeline"],
    "mysql.fantasy": ["AyuFtyMysqlPipeline"],
    "mysql.stats": ["AyuStatisticsMysqlPipeline"],
    "mysql.turbo": ["AyuTurboMysqlPipeline"],
    "mysql.twisted": ["AyuTwistedMysqlPipeline"],
    "oracle.fantasy": ["AyuFtyOraclePipeline"],
    "oracle.twisted": ["AyuTwistedOraclePipeline"],
    "oss.ali": ["AyuAsyncOssPipeline"],
    "oss.batch": ["AyuAsyncOssBatchPipeline"],
    "postgres.asynced": ["AyuAsyncPostgresPipeline"],
    "postgres.fantasy": ["AyuFtyPostgresPipeline"],
    "postgres.twisted": ["AyuTwistedPostgresPipeline"],
}


setup_lazy_import(
    modules_map=_MODULES,
    base_package="ayugespidertools.scraper.pipelines",
    globals_dict=globals(),
)
