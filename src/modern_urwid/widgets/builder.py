import string
from typing import TYPE_CHECKING, Union

from modern_urwid.resource.dummies import UnresolvedResource, UnresolvedTemplate
from modern_urwid.resource.utils import resolve_resource

if TYPE_CHECKING:
    from urwid import AttrMap, Widget

    from modern_urwid.compiler import Metadata
    from modern_urwid.context import CompileContext
    from modern_urwid.xml.ast import LayoutNode

    from .size_options import SizeOptions


class WidgetBuilder:
    """
    Used to create urwid widgets from the AST nodes.
    Subclasses should define the following methods:
    - ``build``
    - ``attach_children`` (if the widget has children)
    - ``after_build`` (if extra modification is needed)

    The following attributes can be used if applicable:
    - ``node``: :class:`~modern_urwid.xml.ast.LayoutNode`
    - ``context``: :class:`~modern_urwid.context.CompileContext`
    """

    tag: Union[str, None] = None

    def __init__(self, node: Union["LayoutNode", None], context: "CompileContext"):
        self.node = node
        self.context = context

    def build(self, *args, **kwargs) -> "Widget":
        """Build and return the widget."""
        raise NotImplementedError

    def attach_children(
        self,
        widget: "Widget",
        children: list[tuple["Widget", "SizeOptions", "Metadata"]],
    ):
        raise NotImplementedError

    def after_build(self, widget: "AttrMap") -> "Widget":
        """
        Optional hook to wrap or modify the widget after creation.
        Useful for containers, decorators, or instrumentation.
        """
        return widget

    def resolve_resource(self, unresolved: UnresolvedResource):
        """Resolve a module attribute."""
        return resolve_resource(self.context.module_registry, unresolved)

    def resolve_template(self, unresolved: UnresolvedTemplate):
        """Resolve a string template."""
        value = unresolved.value
        variables = [
            field for _, field, _, _ in string.Formatter().parse(value) if field
        ]
        for variable in variables:
            value = value.replace(
                f"{{{variable}}}",
                str(self.resolve_resource(UnresolvedResource(variable))),
            )
        return value
