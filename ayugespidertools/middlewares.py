from ayugespidertools.config import setup_lazy_import

_MODULES = {
    "headers.ua": ["RandomRequestUaMiddleware"],
    "netlib.aiohttplib": ["AiohttpDownloaderMiddleware"],
    "proxy.dynamic": [
        "AbuDynamicProxyDownloaderMiddleware",
        "DynamicProxyDownloaderMiddleware",
    ],
    "proxy.exclusive": ["ExclusiveProxyDownloaderMiddleware"],
}


setup_lazy_import(
    modules_map=_MODULES,
    base_package="ayugespidertools.scraper.middlewares",
    globals_dict=globals(),
)
