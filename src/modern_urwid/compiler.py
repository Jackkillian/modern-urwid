import inspect
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Union

import urwid
from lxml import etree
from typing_extensions import TypedDict

from .constants import DEFAULT_STYLE
from .resource.dummies import UnresolvedResource
from .resource.utils import import_module, resolve_resource, wrap_callback
from .style.css.parser import parse_stylesheet
from .style.css.wrapper import create_wrapper
from .widgets.builder import WidgetBuilder
from .widgets.size_options import SizeOptions
from .xml.ast import LayoutNode, MetaNode
from .xml.parser import parse_element

if TYPE_CHECKING:
    from modern_urwid.context import CompileContext


if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required, TypedDict
else:
    from typing import NotRequired, Required, TypedDict


class SignalData(TypedDict):
    name: Required[str]
    callback: Required[UnresolvedResource]


class LayoutData(TypedDict):
    on_load: NotRequired[Union[UnresolvedResource, None]]
    on_enter: NotRequired[Union[UnresolvedResource, None]]
    on_exit: NotRequired[Union[UnresolvedResource, None]]
    controller: NotRequired[Union[UnresolvedResource, None]]


class StylesheetData(TypedDict):
    path: Required[str]
    var: NotRequired[list[dict[str, str]]]


class ResourceData(TypedDict):
    python: NotRequired[list[dict[str, str]]]
    widget: NotRequired[list[dict[str, str]]]
    stylesheet: NotRequired[list[StylesheetData]]


class Metadata(TypedDict):
    resources: Required[ResourceData]
    signals: Required[list[SignalData]]
    layout: Required[LayoutData]


def compile_meta_nodes(
    nodes: list["MetaNode"],
) -> Metadata:
    resources = {}
    signals = []
    layout = {}

    for node in nodes:
        if node.tag == "resources":
            for resource in node.children:
                if resource.tag not in resources:
                    resources[resource.tag] = []
                if resource.children:
                    data: dict = resource.attrs
                    for child in resource.children:
                        if child.tag not in data:
                            data[child.tag] = []
                        data[child.tag].append(child.attrs)
                    resources[resource.tag].append(data)
                else:
                    resources[resource.tag].append(resource.attrs)
        elif node.tag == "signal":
            signals.append(node.attrs)
        elif node.tag == "layout":
            layout.update(node.attrs)
        else:
            raise ValueError(f"Unallowed tag 'mu:{node.tag}' in meta")

    return {"resources": resources, "signals": signals, "layout": layout}


def compile_node(
    node: "LayoutNode",
    ctx: "CompileContext",
    root_style: dict[str, str] = DEFAULT_STYLE,
    child_class: Union[str, None] = None,
) -> tuple[urwid.Widget, SizeOptions, Metadata]:
    """
    Take the AST and CSS rules and create a widget
    """

    # build base widget
    builder = ctx.widget_registry.get(node.tag)(node, ctx)
    widget = builder.build()

    # parse meta
    meta = compile_meta_nodes(node.meta)
    for tag in meta.get("resources").get("python", []):
        if file_path := tag.get("path"):
            file_path = ctx.resolve_path(file_path)
        else:
            file_path = None
        if (result := import_module(tag.get("module"), file_path)) is None:
            raise ValueError(
                "Could not get attribute 'module' or 'path' for mu:python tag"
            )

        name, module = result
        if alias := tag.get("as"):
            name = alias
        ctx.module_registry.register(name, module)

    for tag in meta.get("resources").get("widget", []):
        if file_path := tag.get("path"):
            file_path = ctx.resolve_path(file_path)
        else:
            file_path = None
        if (result := import_module(tag.get("module"), file_path)) is None:
            raise ValueError(
                "Could not get attribute 'module' or 'path' for mu:widget tag"
            )

        for name, obj in inspect.getmembers(result[1]):
            if (
                inspect.isclass(obj)
                and issubclass(obj, WidgetBuilder)
                and obj is not WidgetBuilder
            ):
                ctx.widget_registry.register(obj)

    for stylesheet in meta.get("resources").get("stylesheet", []):
        path = stylesheet.get("path")
        if path is None:
            raise ValueError("Could not get attribute 'path' for mu:stylesheet element")

        vars = {}
        for var in stylesheet.get("var", []):
            vars[var.get("name")] = var.get("value")

        selectors, pseudo_map = parse_stylesheet(
            ctx.resolve_path(path),
            vars,
        )
        ctx.style_registry.add_selectors(selectors)
        ctx.style_registry.pseudo_map.update(pseudo_map)

    for signal in meta.get("signals"):
        if not (name := signal.get("name")):
            raise ValueError("Name attribute not present on <mu:signal> tag")

        if not (resource := signal.get("callback")):
            raise ValueError("Callback attribute not present on <mu:signal> tag")

        if callable(callback := resolve_resource(ctx.module_registry, resource)):
            urwid.connect_signal(widget, name, wrap_callback(callback, node, ctx))
        else:
            TypeError(f"Resource at {resource} is not callable.")

    # style
    if not isinstance(id := node.meta_attrs.get("id"), str):
        id = None
    else:
        if id in ctx.mapped_widgets:
            raise ValueError(f"Cannot duplicate IDs: {id}")
        ctx.mapped_widgets[id] = widget

    if not isinstance(clazz := node.meta_attrs.get("class"), str):
        clazz = child_class
    elif child_class:
        clazz = f"{child_class} {clazz}"

    style, hash, focus_hash = ctx.style_registry.get(
        create_wrapper(node.tag, id, clazz),
        root_style,
    )

    # sizing
    if "height" in node.meta_attrs:
        wh_type = "given"
        wh_amount = node.get_meta_attr("height")
    elif "weight" in node.meta_attrs:
        wh_type = "weight"
        wh_amount = node.get_meta_attr("weight")
    elif "pack" in node.meta_attrs:
        wh_type = "pack"
        wh_amount = None
    else:
        wh_type = "weight"
        wh_amount = 1

    if not isinstance(wh_amount, (int, float)) and wh_amount is not None:
        # TODO: support floats
        raise TypeError(f"WH amount '{wh_amount}' is not an int on node {node}")
    sizing = SizeOptions(wh_type, wh_amount)

    # children
    child_class = str(node.get_meta_attr("child_class"))
    if child_class:
        child_class = f"{clazz} {child_class}"
    else:
        child_class = clazz
    children = [compile_node(child, ctx, style, child_class) for child in node.children]
    if children:
        builder.attach_children(widget, children)

    # apply style map
    widget = urwid.AttrMap(widget, hash, focus_hash)

    return builder.after_build(widget), sizing, meta


def parse_xml_layout(
    file_path: Union[Path, str], context: "CompileContext"
) -> tuple[urwid.Widget, Metadata]:
    root = etree.parse(file_path).getroot()
    node = parse_element(root)
    if not isinstance(node, LayoutNode):
        raise ValueError("Root tag must an urwid widget")
    widget, _, meta = compile_node(node, context)
    return widget, meta
