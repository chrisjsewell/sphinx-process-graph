from typing import Literal, TypedDict, Unpack


def html(s: str) -> str:
    """Wrap a string in HTML tags."""
    return f"<{s}>"


def u(s: str) -> str:
    """underline."""
    return f"<U>{s}</U>"


def o(s: str) -> str:
    """underline."""
    return f"<U>{s}</U>"


def b(s: str) -> str:
    """bold."""
    return f"<B>{s}</B>"


def i(s: str) -> str:
    """italic."""
    return f"<I>{s}</I>"


def s(s: str) -> str:
    """strike-through."""
    return f"<S>{s}</S>"


def sub(s: str) -> str:
    """Sub-script."""
    return f"<SUB>{s}</SUB>"


def sup(s: str) -> str:
    """Super-script."""
    return f"<SUP>{s}</SUP>"


def br(align: Literal["CENTER", "LEFT", "RIGHT", None] = None) -> str:
    """line break."""
    if align:
        return f'<BR ALIGN="{align}" />'
    return "<BR/>"


class TableParams(TypedDict):
    """Parameters for a table."""

    align: Literal["CENTER", "LEFT", "RIGHT"]
    """Specifies horizontal placement."""
    bgcolor: str
    """Specifies the background color for a table."""
    border: int
    """specifies the width of the border around a table.

    A value of zero indicates no border.
    The default is 1. The maximum value is 255.
    """
    cellborder: int
    """specifies the width for all cells in a table.

    The maximum value is 127.
    """
    cellpadding: int
    """specifies the space, in points, between a cell's border and its content.

    The default is 2. The maximum value is 255.
    """
    cellspacing: int
    """specifies the space, in points, between cells in a table and between a cell and the table's border.

    The default is 2. The maximum value is 127.
    """
    color: str
    """specifies the border color for a table."""
    fixedsize: bool
    """Specifies whether the values given by the WIDTH and HEIGHT attributes are enforced."""
    gradientangle: int
    """Gives the angle used in a gradient fill if the BGCOLOR is a color list."""
    height: int
    """specifies the minimum height, in points, of the object.

    The maximum value is 65535.
    """
    href: str
    """Attaches a URL to the table."""
    id: str
    """Allows the user to specify a unique ID for the table."""
    port: str
    """Specifies the port for the table."""
    rows: str
    """Provides general formatting information concerning the rows.

    At present, the only legal value is *, which causes a horizontal rule to appear between every row.
    """
    sides: str
    """specifies which sides of a border in a cell or table should be drawn, if a border is drawn.

    Can contain any collection of the (case-insensitive) characters 'L', 'T', 'R', or 'B'
    """
    style: str
    """specifies the style characteristics for the table, as a comma-separated list.

    At present, the only legal attributes are ROUNDED and RADIAL.
    """
    target: str
    """Determines which window of the browser is used for the HREF if the table has one."""
    title: str
    """Sets the tooltip annotation attached to the element, if HREF is present."""
    valign: Literal["BOTTOM", "MIDDLE", "TOP"]
    """Specifies vertical placement."""
    width: int
    """specifies the minimum width, in points, of the object.

    The maximum value is 65535.
    """


class TableCellParams(TypedDict):
    """Parameters for a table."""

    align: Literal["CENTER", "LEFT", "RIGHT", "TEXT"]
    """Specifies horizontal placement."""
    balign: Literal["CENTER", "LEFT", "RIGHT"]
    """Specifies the default alignment of <BR> elements contained in the cell."""
    bgcolor: str
    """Specifies the background color."""
    border: int
    """specifies the width of the border.

    A value of zero indicates no border.
    The default is 1. The maximum value is 255.
    """
    cellpadding: int
    """specifies the space, in points, between a cell's border and its content.

    The default is 2. The maximum value is 255.
    """
    cellspacing: int
    """specifies the space, in points, between cells in a table and between a cell and the table's border.

    The default is 2. The maximum value is 127.
    """
    color: str
    """specifies the border color."""
    colspan: int
    """specifies the number of columns spanned by the cell.

    The default is 1. The maximum value is 65535.
    """
    fixedsize: bool
    """Specifies whether the values given by the WIDTH and HEIGHT attributes are enforced."""
    gradientangle: int
    """Gives the angle used in a gradient fill if the BGCOLOR is a color list."""
    height: int
    """specifies the minimum height, in points.

    The maximum value is 65535.
    """
    href: str
    """Attaches a URL."""
    id: str
    """Allows the user to specify a unique ID."""
    port: str
    """Specifies the port."""
    rowspan: int
    """specifies the number of rows spanned by the cell.

    The default is 1. The maximum value is 65535.
    """
    sides: str
    """specifies which sides of the border should be drawn, if a border is drawn."""
    style: str
    """specifies the style characteristics, as a comma-separated list.

    At present, the only legal attribute is RADIAL.
    """
    target: str
    """Determines which window of the browser is used for the HREF if the table has one."""
    title: str
    """Sets the tooltip annotation attached to the element, if HREF is present."""
    valign: Literal["BOTTOM", "MIDDLE", "TOP"]
    """Specifies vertical placement."""
    width: int
    """specifies the minimum width, in points, of the object.

    The maximum value is 65535.
    """


class TableCell:
    """A cell in a table."""

    def __init__(self, content: str, **kwargs: Unpack[TableCellParams]) -> None:
        """Create a new cell."""
        self.content = content
        self.kwargs = kwargs

    def __repr__(self) -> str:
        text = "<TD"
        for key, value in self.kwargs.items():
            if key == "fixedsize":
                str_value = "TRUE" if value else "FALSE"
            else:
                str_value = str(value)  # TODO escape "
            text += f' {key.upper()}="{str_value}"'
        text += f">\n{self.content}\n</TD>"
        return text


class Table:
    """A table of data."""

    def __init__(
        self, rows: list[list[TableCell]] | None = None, **kwargs: Unpack[TableParams]
    ) -> None:
        """Create a new table."""
        self.kwargs = kwargs
        self.rows = rows or []

    def add_row(self, cells: list[TableCell]) -> None:
        """Add a row to the table."""
        self.rows.append(cells)

    def __repr__(self) -> str:
        text = "<TABLE"
        for key, value in self.kwargs.items():
            if key == "fixedsize":
                str_value = "TRUE" if value else "FALSE"
            else:
                str_value = str(value)  # TODO escape "
            text += f' {key.upper()}="{str_value}"'
        text += ">\n"
        for row in self.rows:
            text += "<TR>\n"
            for cell in row:
                text += str(cell)
            text += "</TR>\n"
        text += "</TABLE>\n"
        return text
