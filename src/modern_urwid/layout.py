from __future__ import annotations

import importlib
import inspect
import string
from pathlib import Path
from types import ModuleType

import cssselect2
import tinycss2
import urwid
from dict_hash import md5
from lxml import etree
from tinycss2.ast import Node

from .constants import DEFAULT_STYLE, RESOURCE_CHAR, XML_NS
from .css_parser import CSSParser
from .exceptions import UnknownResource
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


class LayoutResources:
    """
    A base class for extending a layout's functionality
    Reference properties from the base class (eg callbacks) with the "@" prefix
    Reference properties from the data dictionary with "{}" surrounding the key (eg user.name)
    """

    def __init__(self, layout: Layout, widgets=[], palettes=[]):
        self.layout = layout
        self.widgets = widgets
        self.palettes = palettes
        self.data = {}

    def get_widgets(self):
        return self.widgets

    def get_palettes(self):
        return self.palettes

    def load_resources_from_tag(self, element: etree.Element):
        for child in element:
            if child.tag == f"{XML_NS}python":
                module_path = child.get("module")
                alias = child.get("as")
                module = importlib.import_module(module_path)
                if alias:
                    self.data[alias] = module
                else:
                    keys = module_path.split(".")
                    target = self.data
                    for key in keys[:-1]:
                        if key not in target:
                            target[key] = {}
                            target = target[key]
                        else:
                            target = target[key]
                    target[keys[-1]] = module


class Layout:
    def __init__(
        self,
        xml_path: Path,
        css_path: Path | None = None,
        resources_cls=LayoutResources,
        xml_dir=None,
        css_dir=None,
    ) -> None:
        self.resources = resources_cls(self)
        self.custom_widgets = self.resources.get_widgets()
        self.palettes = self.resources.get_palettes()
        self.widget_map = {}
        self.styles = {}

        # Handle path stuff
        self.css_path = css_path
        if css_path is not None:
            self.css_path = css_path
            if isinstance(css_dir, Path):
                self.css_path = css_dir / css_path
            self.css_dir = self.css_path.parent
        else:
            self.css_dir = None

        self.xml_path = xml_path
        if isinstance(xml_dir, Path):
            self.xml_path = xml_dir / xml_path
        self.xml_dir = self.xml_path.parent

        # Load the xml and css
        self.css_parser = CSSParser(self.css_path)

        xml = open(self.xml_path).read()
        root = self.parse_element(
            FilteredWrapper.from_html_root(etree.fromstring(xml)),
            DEFAULT_STYLE,
        )
        if not isinstance(root, urwid.Widget):
            raise ValueError(f"Got {root} instead of Widget for root")
        else:
            self.root = root

        for hash, style in self.styles.items():
            self.palettes.append((hash, *style.values()))

    def get_root(self):
        return self.root

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
                    target[k] = self.get_resource(v[len(RESOURCE_CHAR) :])
                elif v == "False":
                    target[k] = False
                elif v == "True":
                    target[k] = True
                else:
                    target[k] = self.parse_string_template(v)
        return mu, normal

    def get_resource(self, attr):
        if hasattr(self.resources, attr):
            return getattr(self.resources, attr)
        else:
            raise UnknownResource(f"Could not custom resource '@{attr}'")

    def parse_string_template(self, template):
        variables = [
            field for _, field, _, _ in string.Formatter().parse(template) if field
        ]
        value = template
        for variable in variables:
            value = value.replace(f"{{{variable}}}", self.get_data_resource(variable))
        return value

    def get_data_resource(self, attr):
        keys = attr.split(".")
        value = self.resources.data
        for key in keys:
            if isinstance(value, dict):
                if key not in value:
                    raise ValueError(f"Could not find key '{key}' on {{{attr}}}")
                value = value.get(key)
            elif isinstance(value, ModuleType):
                if hasattr(value, key):
                    value = getattr(value, key)
                else:
                    raise ValueError(f"Could not find key '{key}' on {{{attr}}}")
        return value

    def parse_element(
        self,
        wrapper: FilteredWrapper,
        root_palette: dict,
        child_class: str | None = None,
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
                self.resources.load_resources_from_tag(el)
            else:
                children.append(child)

        # Apply styling
        style, pseudos = self.css_parser.get_styles(root_palette, wrapper)

        normal_hash = md5(style)
        if normal_hash not in self.styles:
            self.styles[normal_hash] = style

        focus_hash = None
        if "focus" in pseudos:
            focus_hash = md5(pseudos["focus"])
            if focus_hash not in self.styles:
                self.styles[focus_hash] = {**style.copy(), **pseudos["focus"]}

        constructor = self.get_widget_constructor(tag)
        if constructor is None:
            return urwid.Filler(urwid.Text(f"Unknown tag: {tag}"))
        elif children:
            widget = constructor(
                element,
                [self.parse_element(child, style, child_class) for child in children],
                **kwargs,
            )
        else:
            widget = constructor(element, **kwargs)

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

    def get_widget_constructor(self, tag):
        if tag == f"{XML_NS}layout":
            return lambda el, **kw: Layout(
                xml_dir=self.xml_dir, css_dir=self.css_dir, **kw
            ).get_root()
        cls_lower = tag.lower()
        for cls in self.custom_widgets:
            if cls_lower == cls.__name__.lower():
                return lambda el, **kw: cls(**kw)
        cls = find_urwid_class(tag)
        if cls is None:
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
            return lambda el, **kw: create_text_widget(cls, el, **kw)
        else:
            return None

    def get_widget_by_id(self, id) -> urwid.Widget | None:
        return self.widget_map.get(id)

    def on_enter(self):
        pass

    def on_exit(self):
        pass
