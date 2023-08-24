# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "vocabuilder"
copyright = "2023, Håkon Hægland"
author = "Håkon Hægland"
release = "0.1"

# -- General configuration ---------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath("../src"))
extensions = ["sphinx.ext.autodoc", "sphinx.ext.coverage"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_context = {
    "display_github": True,
    "github_user": "hakonhagland",
    "github_repo": "vocabuilder",
    "github_version": "master",
    "conf_py_path": "/docs/",
}
