from sphinx.application import Sphinx
from sphinx_graph import __version__, build_main

project = "sphinx-graph"
author = "Chris Sewell"
version = release = __version__

html_theme = "furo"
html_title = "sphinx-graph"


def setup(app: Sphinx):
    app.connect("config-inited", write_image)


def write_image(app: Sphinx, _) -> None:
    build_main(directory=app.srcdir)
