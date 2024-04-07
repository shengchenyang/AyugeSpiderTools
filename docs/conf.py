# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from datetime import datetime

import sphinx_rtd_theme

project = "AyugeSpiderTools"
copyright = f"{datetime.now().year}, shengchenyang"
author = "shengchenyang"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
try:
    import ayugespidertools

    release = ayugespidertools.__version__
    version = ".".join(tuple(release.split(".")[:2]))
except (ImportError, AttributeError):
    release = ""
    version = ""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx_markdown_tables",
    "hoverxref.extension",
    "notfound.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "zh_CN"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_context = {
    "display_github": True,
    "github_user": "shengchenyang",
    "github_repo": "AyugeSpiderTools",
    "github_version": "master/docs/",
}

html_theme = "sphinx_rtd_theme"

html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path: list = []

source_parsers = {
    ".md": "sphinx_markdown_parser.parser.MySTParser",
}
source_suffix = [".rst", ".md"]

autodoc_mock_imports = ["ayugespidertools"]
