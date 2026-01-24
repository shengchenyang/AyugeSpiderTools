from ayugespidertools.config import setup_lazy_import

_MODULES = {
    "headers.ua": ["RandomRequestUaMiddleware"],
    "netlib.aiohttplib": ["AiohttpDownloaderMiddleware"],
    "proxy.default": ["ProxyDownloaderMiddleware"],
}


setup_lazy_import(
    modules_map=_MODULES,
    base_package="ayugespidertools.scraper.middlewares",
    globals_dict=globals(),
)
