from __future__ import annotations

import inspect
from pathlib import Path
from typing import Callable, Literal

import urwid
from dict_hash import md5
from lxml import etree

from .constants import DEFAULT_STYLE, RESOURCE_CHAR, XML_NS
from .css_parser import CSSParser
from .resource_handler import ResourceHandler
from .wrapper import FilteredWrapper


def find_urwid_class(tag: str):
    tag = tag.lower()
    for name, cls in inspect.getmembers(urwid, inspect.isclass):
        if name.lower() == tag:
            return cls
    return None


def create_text_widget(cls, el, **kw):
    if el.text and el.text.strip():
        return cls(
            el.text, **kw
        )  # can't do .strip because it'll  remove the space if doing something like 'Name: '
    else:
        return cls(**kw)


class XMLParser:
    def __init__(
        self,
        xml_path: Path,
        resources: ResourceHandler = ResourceHandler(),
        css_parser: CSSParser = CSSParser(None),
        xml_dir: Path | None = None,
    ) -> None:
        self.widget_map = {}
        self.styles = {}
        self.xml_path = xml_path
        self.css_parser = css_parser
        self.resources = resources

        self.xml_path = xml_path
        if isinstance(xml_dir, Path):
            self.xml_path = xml_dir / xml_path
        self.xml_dir = self.xml_path.parent

        # Load the xml
        xml = self.xml_path.read_text()
        root = self.parse_element(
            FilteredWrapper.from_html_root(etree.fromstring(xml)),
            DEFAULT_STYLE,
        )
        if not isinstance(root, urwid.Widget):
            raise ValueError(f"Got {root} instead of Widget for root")
        else:
            self.root = root

    def get_root(self):
        return self.root

    def get_palettes(self):
        return [(hash, *style.values()) for hash, style in self.styles.items()]

    def parse_attrs(self, kwargs: dict):
        mu = {}
        normal = {}
        for k, v in kwargs.items():
            target = normal
            if k.startswith(XML_NS):
                k = k[len(XML_NS) :]
                target = mu
            if isinstance(v, str):
                if v.isdigit():
                    target[k] = int(v)
                elif v.startswith(RESOURCE_CHAR):
                    target[k] = self.resources.get_resource(v[len(RESOURCE_CHAR) :])
                elif v == "False":
                    target[k] = False
                elif v == "True":
                    target[k] = True
                else:
                    target[k] = self.resources.parse_string_template(v)
        return mu, normal

    def parse_element(
        self,
        wrapper: FilteredWrapper,
        root_palette: dict,
        child_class: str | None = None,
    ) -> (
        urwid.Widget
        | tuple[int, urwid.Widget]
        | tuple[Literal["weight"], int, urwid.Widget]
    ):
        if child_class is not None:
            wrapper.classes |= {child_class}

        element = wrapper.etree_element
        tag = element.tag

        # Parse attributes
        mu_kwargs, kwargs = self.parse_attrs(element.attrib)
        clazz = kwargs.pop("class", None)
        id = kwargs.pop("id", None)
        child_class = mu_kwargs.get("child_class")
        height = mu_kwargs.get("height")
        weight = mu_kwargs.get("weight")

        # Parse children
        signals = {}
        children = list(wrapper.iter_children())
        for child in wrapper.iter_mu_children():
            el = child.etree_element
            if el.tag == f"{XML_NS}signal":
                signal_name = el.get("name")
                signals[signal_name] = self.parse_attrs(el.attrib)
            elif el.tag == f"{XML_NS}resources":
                self.resources.parse_resources_tag(el)
            else:
                children.append(child)

        # Apply styling
        style, pseudos = self.css_parser.get_styles(root_palette, wrapper)

        normal_hash = md5(style)
        if normal_hash not in self.styles:
            self.styles[normal_hash] = style

        focus_hash = None
        if (
            "focus" in pseudos
            and (focus_hash := md5(pseudos["focus"])) not in self.styles
        ):
            self.styles[focus_hash] = {**style.copy(), **pseudos["focus"]}

        if constructor := self.get_widget_constructor(tag):
            widget = constructor(
                element,
                [self.parse_element(child, style, child_class) for child in children],
                **kwargs,
            )
        else:
            return urwid.Filler(urwid.Text(f"Unknown tag: {tag}"))

        if id is not None:
            if id in self.widget_map:
                raise ValueError(f"Cannot duplicate IDs: {id}")
            else:
                self.widget_map[id] = widget

        for name, attrs in signals.items():
            urwid.connect_signal(
                widget, name, attrs[1].get("callback"), attrs[1].get("user_arg")
            )

        if height is not None:
            return (height, urwid.AttrMap(widget, normal_hash, focus_hash))
        elif weight is not None:
            return (
                "weight",
                weight,
                urwid.AttrMap(widget, normal_hash, focus_hash),
            )

        return urwid.AttrMap(widget, normal_hash, focus_hash)

    def style_widget(self, widget: urwid.Widget, classes=[], id=[]) -> urwid.AttrMap:
        style, pseudos = self.css_parser.get_styles_by_attr(DEFAULT_STYLE, classes, id)

        normal_hash = md5(style)
        if normal_hash not in self.styles:
            self.styles[normal_hash] = style

        focus_hash = None
        if (
            "focus" in pseudos
            and (focus_hash := md5(pseudos["focus"])) not in self.styles
        ):
            self.styles[focus_hash] = {**style.copy(), **pseudos["focus"]}

        return urwid.AttrMap(widget, normal_hash, focus_hash)

    def get_widget_constructor(
        self, tag
    ) -> (
        Callable[
            [etree.Element, list[urwid.Widget | urwid.WidgetContainerMixin]],
            urwid.Widget | urwid.WidgetContainerMixin,
        ]
        | None
    ):
        if tag == f"{XML_NS}layout":

            def fun(el, children, **kw):
                parser = XMLParser(
                    **{
                        "xml_dir": self.xml_dir,
                        "resources": self.resources,
                        "css_parser": CSSParser(
                            self.css_parser.path.parent / kw.get("css_path", "")
                        )
                        if "css_path" in kw
                        else self.css_parser,
                        **{k: v for k, v in kw.items() if k != "css_path"},
                    }
                )
                self.styles.update(parser.styles)
                return parser.get_root()

            return fun

        if cls := self.resources.get_widget_builder(tag.lower()):
            return lambda el, children, **kw: cls(el, children).build(**kw)

        if (cls := find_urwid_class(tag)) is None:
            return None

        if issubclass(
            cls,
            urwid.WidgetContainerMixin,
        ):
            return lambda el, children, **kw: cls(children, **kw)
        elif issubclass(
            cls,
            urwid.WidgetDecoration,
        ):
            return lambda el, children, **kw: cls(children[0], **kw)
        elif issubclass(cls, urwid.Widget):
            return lambda el, children, **kw: create_text_widget(cls, el, **kw)
        else:
            return None

    def get_widget_by_id(self, id) -> urwid.Widget | None:
        return self.widget_map.get(id)
