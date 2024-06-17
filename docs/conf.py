from pathlib import Path
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx_graph import __version__, build_main
from docutils import nodes
import tempfile

project = "sphinx-graph"
author = "Chris Sewell"
version = release = __version__

html_theme = "furo"
html_title = "sphinx-graph"


def setup(app: Sphinx):
    app.add_directive("sphinx-graph", SphinxGraphDirective)


class SphinxGraphDirective(SphinxDirective):
    def run(self):
        with tempfile.TemporaryDirectory() as tempdir:
            source = build_main(directory=Path(tempdir)).read_text()
        return [nodes.container("", nodes.raw("", source, format="html"), classes=["sphinx-graph"])]
