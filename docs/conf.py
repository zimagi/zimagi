from recommonmark.parser import CommonMarkParser
from recommonmark.transform import AutoStructify

import os
import karma_sphinx_theme


DOCS_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(DOCS_DIR)


# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
]

templates_path = []
source_parsers = {'.md': CommonMarkParser}
source_suffix = ['.rst', '.md']
master_doc = 'index'

project = 'Command Environment (CENV)'
copyright = '2019, Cloud Orchestration Group'
author = 'Adrian Webb (adrianwebb.78@gmail.com)'

VERSION_PY_PATH = os.path.join(BASE_DIR, 'app', 'settings', 'version.py')
_globs = {}
exec(open(VERSION_PY_PATH).read(), _globs)  # nosec
version = _globs['VERSION']
del _globs

release = version
language = None
exclude_patterns = ['build', '.DS_Store']
pygments_style = 'sphinx'
todo_include_todos = True


# -- Options for HTML output ----------------------------------------------

html_theme = 'theme'
html_theme_path = ['.']

html_theme_options = {
    'navigation_depth': 2,
    'includehidden': False,
    'titles_only': False
}

html_static_path = ['images']
html_logo = "images/logo.png"

html_show_sourcelink = True

# -- Options for HTMLHelp output ------------------------------------------

htmlhelp_basename = 'CENVDoc'


# -- Utilities ------------------------------------------------------------

def resolve_md_url(url):
    return url

def setup(app):
    app.add_config_value('recommonmark_config', {
        'url_resolver': resolve_md_url,
    }, True)
    app.add_transform(AutoStructify)
