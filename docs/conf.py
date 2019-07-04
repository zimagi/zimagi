import os
import sphinx_rtd_theme


DOCS_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(DOCS_DIR)


# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx'
]

templates_path = ['templates']
source_suffix = '.rst'
master_doc = 'index'

project = 'Command Environment (CENV)'
slug = 'cenv'
copyright = '2019, Cloud Orchestration Group'
author = 'Adrian Webb (adrianwebb.78@gmail.com)'

VERSION_PY_PATH = os.path.join(BASE_DIR, 'app', 'settings', 'version.py')
_globs = {}
exec(open(VERSION_PY_PATH).read(), _globs)
version = _globs['VERSION']
release = version
del _globs

language = 'en'
exclude_patterns = ['build', '.DS_Store']
pygments_style = 'default'
todo_include_todos = True


# -- Options for HTML output ----------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

html_static_path = ['static']
html_logo = "static/COG.png"
html_favicon = "static/favicon.ico"

html_show_sourcelink = True
