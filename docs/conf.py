import os
import sys
from datetime import datetime, timezone

# Resolve import path for both "src" and flat layouts
HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC if os.path.isdir(SRC) else ROOT)

project = "networkx-arxiv-generators"
author = "Yan Yablonovskiy and contributors"
copyright = f"{datetime.now(tz=timezone.utc).year}, {author}"
release = ""  # set if you want an explicit version string

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "inherited-members": True,
    "show-inheritance": True,
}
# Place type hints into the description to improve readability
typehints_fully_qualified = True
autodoc_typehints = "description"

# Link out to Python and NetworkX docs
intersphinx_mapping: dict = {
    "python": ("https://docs.python.org/3", None),
    "networkx": ("https://networkx.org/documentation/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path = ["_static"]
