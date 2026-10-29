from ayugespidertools.scraper.pipelines.postgres import (
    AyuPostgresLegacyPipeline,
    AyuPostgresPipeline,
)

__all__ = [
    "AyuFtyPostgresLegacyPipeline",
    "AyuFtyPostgresPipeline",
]


class AyuFtyPostgresPipeline(AyuPostgresPipeline): ...


class AyuFtyPostgresLegacyPipeline(AyuPostgresLegacyPipeline): ...
