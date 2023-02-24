# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from datetime import datetime
from pathlib import Path

project = "AyugeSpiderTools"
copyright = f"{datetime.now().year}, shengchenyang"
author = "shengchenyang"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
try:
    from ayugespidertools.commands.version import AyuCommand

    release = AyuCommand.version()
    version = tuple(release.split(".")[:2])
except ImportError:
    release = ""
    version = ""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "recommonmark",
    "sphinx_markdown_tables",
    "hoverxref.extension",
    "notfound.extension",
    # "ayugespidertoolsdocs",
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
    "github_version": "main/docs/",
}

html_theme = "sphinx_rtd_theme"
import sphinx_rtd_theme

html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = []

from recommonmark.parser import CommonMarkParser

source_parsers = {
    ".md": CommonMarkParser,
}
source_suffix = [".rst", ".md"]
