from pathlib import Path
import tomllib

from . import Data, build_graph

if __name__ == "__main__":
    data = tomllib.loads(
        Path(__file__).parent.joinpath("sphinx_graph.toml").read_text()
    )
    model = Data(**data)
    graph = build_graph(model)
    # print(graph.source)
    graph.render("sphinx_graph", format="svg", cleanup=True)
