from ayugespidertools.scraper.pipelines.postgres import (
    AyuPostgresLegacyPipeline,
    AyuPostgresPipeline,
)

__all__ = [
    "AyuFtyPostgresPipeline",
    "AyuPostgresLegacyPipeline",
]


class AyuFtyPostgresPipeline(AyuPostgresPipeline): ...


class AyuFtyPostgresLegacyPipeline(AyuPostgresLegacyPipeline): ...
