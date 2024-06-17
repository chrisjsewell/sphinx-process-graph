"""Build a graph of the build process of a Sphinx project."""

__version__ = "0.1.0"

from pathlib import Path
import sys
import tomllib
from typing import Literal

from graphviz import Digraph
from pydantic import BaseModel, ConfigDict, Field

from . import html_like as html


class Data(BaseModel):
    """The data to build the graph from."""

    model_config = ConfigDict(extra="forbid")

    comment: str
    objects: dict[str, "Object"]
    """The objects in the graph, keyed by their fully qualified name."""
    events: dict[str, "Event"]
    transforms: dict[str, "Transform"]
    post_transforms: dict[str, "PostTransform"]


class Object(BaseModel):
    """A python object."""

    model_config = ConfigDict(extra="forbid")

    description: str = ""
    type: Literal["function", "method"] = "method"
    calls: list["Call"] = Field(default_factory=list)
    overridable: bool = False
    """Whether the object can be overridden by a subclass."""
    overrides: list[str] = Field(default_factory=list)
    """The subclass objects that override this object."""


class Event(BaseModel):
    """A sphinx event."""

    model_config = ConfigDict(extra="forbid")

    callbacks: dict[str, "EventCallback"]


class EventCallback(BaseModel):
    """A callback for a sphinx event."""

    model_config = ConfigDict(extra="forbid")

    priority: int
    doc: str = ""
    hide: bool = False
    """Whether to hide the callback from the graph.
    (mainly used for EnvironmentCollector default events)
    """


class Transform(BaseModel):
    """A transform for a sphinx event."""

    model_config = ConfigDict(extra="forbid")

    priority: int
    hide: bool = False
    doc: str = ""
    emit: str | None = None


class PostTransform(BaseModel):
    """A transform for a sphinx event."""

    model_config = ConfigDict(extra="forbid")

    priority: int
    formats: list[str] = Field(default_factory=list)
    builders: list[str] = Field(default_factory=list)
    hide: bool = False
    doc: str = ""
    emit: str | None = None


class Call(BaseModel):
    """A call from one object to another."""

    text: str
    """The fully qualified name of the object being called."""

    type: Literal[
        "standard",
        "enter",
        "exit",
        "emit",
        "apply_transforms",
        "apply_post_transforms",
    ] = "standard"
    """The type of call."""

    is_ref: bool | None = None
    """Whether the text is a reference to the object being called.

    Defaults to true if type is "standard", false otherwise.
    """

    context: Literal["for", "with", "if", "elif", "else", "fork", None] = None
    """The context of the call, if type is enter/exit."""

    obj_type: Literal["function", "method", None] = None
    """The type of the object being called."""

    warn_no_object: bool = True
    """Whether to warn if the object being called does not have its own node."""


def warning(message: str) -> None:
    """Print a warning message to stderr."""
    print(f"Warning: {message}", file=sys.stderr)


def build_main(
    name: str = "sphinx_graph", directory: Path | None = None, format: str = "svg"
) -> Path:
    data = tomllib.loads(
        Path(__file__).parent.joinpath("sphinx_graph.toml").read_text()
    )
    model = Data(**data)
    graph = build_graph(model)
    # print(graph.source)
    directory = directory or Path.cwd()
    graph.render(name, directory, format="svg", cleanup=True)
    return directory.joinpath(f"{name}.{format}")


def build_graph(data: Data) -> Digraph:  # noqa: PLR0912,PLR0915
    """Build a graph of the build process of a Sphinx project."""

    graph = Digraph(comment=data.comment, graph_attr={"rankdir": "LR"})

    transforms_id = "_apply_transforms"
    post_transforms_id = "_apply_post_transforms"

    for path, object_data in data.objects.items():
        table = html.Table(border=0, cellspacing=0)
        table.add_row(
            [html.TableCell(html.u(path2name(path, object_data.type)), align="CENTER")]
        )

        if object_data.description:
            table.add_row(
                [
                    html.TableCell(
                        object_data.description.replace("\n", html.br("LEFT")),
                        align="LEFT",
                        cellpadding=10,
                    )
                ]
            )

        if object_data.calls:
            indent = 0
            port_num = 0
            for call in object_data.calls:
                if call.type == "exit":
                    indent -= 1
                    continue

                is_ref = (
                    call.is_ref if call.is_ref is not None else call.type == "standard"
                )

                text = call.text
                if is_ref:
                    obj_type = call.obj_type
                    if obj := data.objects.get(call.text):
                        obj_type = obj.type
                    text = path2name(call.text, obj_type)

                indent_str = " " * indent * 4
                cell_kwargs = {}

                if call.type == "enter":
                    text = f"{call.context} {text}:"
                    indent += 1
                elif call.type == "emit":
                    text = f"emit {text}"
                    cell_kwargs["bgcolor"] = "lightblue"
                if call.type == "apply_transforms":
                    cell_kwargs["bgcolor"] = "lightyellow"
                if call.type == "apply_post_transforms":
                    cell_kwargs["bgcolor"] = "lightyellow"

                text = indent_str + text

                port_num += 1
                table.add_row(
                    [
                        html.TableCell(
                            text,
                            align="LEFT",
                            port=str(port_num),
                            border=1,
                            **cell_kwargs,
                        )
                    ]
                )

                match call.type:
                    case "standard":
                        if is_ref:
                            if call.text not in data.objects:
                                if call.warn_no_object:
                                    warning(
                                        f"{call.text!r} not found, called from {path!r}"
                                    )
                            else:
                                graph.edge(path + ":" + str(port_num), call.text)
                    case "enter":
                        if is_ref:
                            if call.text not in data.objects:
                                if call.warn_no_object:
                                    warning(
                                        f"{call.text!r} not found, called from {path!r}"
                                    )
                            else:
                                graph.edge(path + ":" + str(port_num), call.text)
                    case "emit":
                        if call.text not in data.events:
                            warning(
                                f"{call.text!r} event not found, called from {path!r}"
                            )
                        else:
                            graph.edge(path + ":" + str(port_num), call.text)
                    case "apply_transforms":
                        graph.edge(
                            path + ":" + str(port_num),
                            transforms_id,
                            style="dashed",
                        )
                    case "apply_post_transforms":
                        graph.edge(
                            path + ":" + str(port_num),
                            post_transforms_id,
                            style="dashed",
                        )
                    case _:
                        warning(f"Unknown call type {call.type!r}")

        if object_data.overrides or object_data.overridable:
            table.add_row(
                [
                    html.TableCell(
                        html.i("Overridable"),
                        align="LEFT",
                        cellpadding=10,
                    )
                ]
            )
            for override in object_data.overrides:
                port_num += 1
                table.add_row(
                    [
                        html.TableCell(
                            path2name(override, object_data.type),
                            align="LEFT",
                            border=1,
                            port=str(port_num),
                        )
                    ]
                )
                if override not in data.objects:
                    warning(f"{override!r} not found, override of {path!r}")
                else:
                    graph.edge(path + ":" + str(port_num), override, style="dashed")

        graph.node(
            path, label=html.html(str(table)), shape="box", style="rounded", margin=".2"
        )

    for name, event_data in data.events.items():
        add_event_node(name, event_data, graph)

    add_transforms_node(data, graph, transforms_id)
    add_post_transforms_node(data, graph, post_transforms_id)

    return graph


def path2name(path: str, type: Literal["function", "method", None] = None) -> str:
    """Split a path into the module and object names."""
    parts = path.split(".")
    if type == "method" and len(parts) > 1:
        return f"{parts[-2]}.{parts[-1]}()"
    elif type in ("function", "method"):
        return parts[-1] + "()"
    return path


def add_event_node(name: str, data: Event, graph: Digraph):
    """Add a node for an event, with its callbacks."""
    table = html.Table(border=0, cellspacing=0)
    table.add_row(
        [html.TableCell(html.u(name), align="CENTER", colspan=2, bgcolor="lightblue")]
    )
    for callback_name, callback_data in data.callbacks.items():
        if callback_data.hide:
            continue
        table.add_row(
            [
                html.TableCell(
                    callback_name[len("sphinx.") :]
                    if callback_name.startswith("sphinx.")
                    else callback_name,
                    align="LEFT",
                    border=1,
                    cellpadding=3,
                ),
                html.TableCell(str(callback_data.priority), align="CENTER", border=1),
            ]
        )
        if callback_data.doc:
            table.add_row(
                [
                    html.TableCell(
                        callback_data.doc.replace("\n", html.br("LEFT")),
                        align="LEFT",
                        colspan=2,
                    )
                ]
            )
    graph.node(
        name, label=html.html(str(table)), shape="box", style="rounded", margin=".2"
    )


def add_transforms_node(data: Data, graph: Digraph, node_id: str):
    """Add a node for the transforms."""
    table = html.Table(border=0, cellspacing=0)
    table.add_row(
        [
            html.TableCell(
                html.u("Transforms"), align="CENTER", colspan=2, bgcolor="lightyellow"
            )
        ]
    )
    for tr_name, tr_data in data.transforms.items():
        if tr_data.hide:
            continue
        table.add_row(
            [
                html.TableCell(
                    tr_name[len("sphinx.") :]
                    if tr_name.startswith("sphinx.")
                    else tr_name,
                    align="LEFT",
                    border=1,
                    cellpadding=3,
                ),
                html.TableCell(
                    str(tr_data.priority), align="CENTER", border=1, port=tr_name
                ),
            ]
        )
        if tr_data.emit:
            graph.edge(f"{node_id}:{tr_name}", tr_data.emit)
        if tr_data.doc:
            table.add_row(
                [
                    html.TableCell(
                        tr_data.doc.replace("\n", html.br("LEFT")),
                        align="LEFT",
                        colspan=2,
                    )
                ]
            )
    graph.node(
        node_id, label=html.html(str(table)), shape="box", style="rounded", margin=".2"
    )


def add_post_transforms_node(data: Data, graph: Digraph, node_id: str):
    """Add a node for the post transforms."""
    table = html.Table(border=0, cellspacing=0)
    table.add_row(
        [
            html.TableCell(
                html.u("Post Transforms"),
                align="CENTER",
                colspan=3,
                bgcolor="lightyellow",
            )
        ]
    )
    for tr_name, tr_data in data.post_transforms.items():
        if tr_data.hide:
            continue
        table.add_row(
            [
                html.TableCell(
                    tr_name[len("sphinx.") :]
                    if tr_name.startswith("sphinx.")
                    else tr_name,
                    align="LEFT",
                    border=1,
                    cellpadding=3,
                ),
                html.TableCell(
                    ",".join(tr_data.formats + tr_data.builders),
                    align="LEFT",
                    border=1,
                    port=tr_name,
                ),
            ]
        )
        if tr_data.emit:
            graph.edge(f"{node_id}:{tr_name}", tr_data.emit)
        if tr_data.doc:
            table.add_row(
                [
                    html.TableCell(
                        tr_data.doc.replace("\n", html.br("LEFT")),
                        align="LEFT",
                        colspan=3,
                    )
                ]
            )
    graph.node(
        node_id, label=html.html(str(table)), shape="box", style="rounded", margin=".2"
    )
