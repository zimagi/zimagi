import os
import sphinx_rtd_theme


DOCS_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(DOCS_DIR)


# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode'
]

source_suffix = '.rst'
master_doc = 'readme'

project = 'Zimagi'
copyright = '2020, Zimagi'
author = 'Adrian Webb (adrian.webb@zimagi.com)'

version = open(os.path.join(BASE_DIR, 'app', 'VERSION')).read()
release = version

language = 'en'
exclude_patterns = ['_build', 'archive']
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
    'style_nav_header_background': '#021026',
    'collapse_navigation': False,
    'sticky_navigation': False,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

templates_path = ['_templates']
html_static_path = ['_static']
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"

html_show_sourcelink = True
html_use_index = True
html_split_index = True


# -- General configuration ------------------------------------------------

def setup(app):
    app.add_css_file('css/override.css')
