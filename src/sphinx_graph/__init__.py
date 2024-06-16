"""Build a graph of the build process of a Sphinx project."""

__version__ = "0.1.0"

import sys
from typing import Literal

from graphviz import Digraph
from pydantic import BaseModel, Field

from . import html_like as html


class Data(BaseModel):
    """The data to build the graph from."""

    comment: str
    objects: dict[str, "Object"]
    """The objects in the graph, keyed by their fully qualified name."""
    events: dict[str, "Event"]
    transforms: dict[str, "Transform"]


class Object(BaseModel):
    """A python object."""

    description: str = ""
    type: Literal["function", "method"]
    calls: list["Call"] = Field(default_factory=list)


class Event(BaseModel):
    """A sphinx event."""

    callbacks: dict[str, "EventCallback"]


class EventCallback(BaseModel):
    """A callback for a sphinx event."""

    priority: int
    doc: str = ""
    hide: bool = False


class Transform(BaseModel):
    """A transform for a sphinx event."""

    priority: int
    hide: bool = False
    doc: str = ""
    emit: str | None = None


class Call(BaseModel):
    """A call from one object to another."""

    name: str
    """The fully qualified name of the object being called."""

    type: Literal[
        None,
        "enter",
        "exit",
        "emit",
        "apply_transforms",
    ] = None
    """The type of call."""

    context: Literal["for", "with", "if", "elif", "else", "fork", None] = None
    """The context of the call, if type is enter/exit."""

    obj_type: Literal["function", "method", None] = None
    """The type of the object being called."""
    warn_no_object: bool = True
    """Whether to warn if the object being called does not have its own node."""


def warning(message: str) -> None:
    """Print a warning message to stderr."""
    print(f"Warning: {message}", file=sys.stderr)


def build_graph(data: Data) -> Digraph:  # noqa: PLR0912,PLR0915
    """Build a graph of the build process of a Sphinx project."""

    graph = Digraph(comment=data.comment, graph_attr={"rankdir": "LR"})

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
            for port_num, call in enumerate(object_data.calls):
                if call.type == "exit":
                    indent -= 1
                    continue

                obj_type = call.obj_type
                if obj := data.objects.get(call.name):
                    obj_type = obj.type
                name = path2name(call.name, obj_type)

                indent_str = " " * indent * 4
                cell_kwargs = {}

                if call.type == "enter":
                    name = f"{call.context} {name}:"
                    indent += 1
                elif call.type == "emit":
                    name = f"emit {name}"
                    cell_kwargs["bgcolor"] = "lightblue"
                if call.type == "apply_transforms":
                    cell_kwargs["bgcolor"] = "lightyellow"

                name = indent_str + name

                table.add_row(
                    [
                        html.TableCell(
                            name,
                            align="LEFT",
                            port=str(port_num),
                            border=1,
                            **cell_kwargs,
                        )
                    ]
                )

                if call.type == "apply_transforms":
                    graph.edge(
                        path + ":" + str(port_num), "_apply_transforms", style="dashed"
                    )
                elif call.name in data.objects or call.name in data.events:
                    graph.edge(path + ":" + str(port_num), call.name)
                elif call.warn_no_object and call.type != "enter":
                    warning(f"{call.name!r} not found, called from {path!r}")

        graph.node(
            path, label=html.html(str(table)), shape="box", style="rounded", margin=".2"
        )

    for name, event_data in data.events.items():
        table = html.Table(border=0, cellspacing=0)
        table.add_row(
            [
                html.TableCell(
                    html.u(name), align="CENTER", colspan=2, bgcolor="lightblue"
                )
            ]
        )
        for callback_name, callback_data in event_data.callbacks.items():
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
                    html.TableCell(
                        str(callback_data.priority), align="CENTER", border=1
                    ),
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
            graph.edge("_apply_transforms:" + tr_name, tr_data.emit)
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
        "_apply_transforms",
        label=html.html(str(table)),
        shape="box",
        style="rounded",
        margin=".2",
    )

    return graph


def path2name(path: str, type: Literal["function", "method", None] = None) -> str:
    """Split a path into the module and object names."""
    parts = path.split(".")
    if type == "method" and len(parts) > 1:
        return f"{parts[-2]}.{parts[-1]}()"
    elif type in ("function", "method"):
        return parts[-1] + "()"
    return path
