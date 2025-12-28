from __future__ import annotations

import importlib
import inspect
import string
from pathlib import Path
from types import LambdaType, ModuleType
from typing import Callable

import urwid
from dict_hash import md5
from lxml import etree

from modern_urwid.resource_handler import ResourceHandler
from modern_urwid.xml_parser import XMLParser

from .builder import WidgetBuilder
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


class LayoutResourceHandler(ResourceHandler):
    """
    A base class for extending a layout's functionality
    Reference properties from the base class (eg callbacks) with the "@" prefix
    Reference properties from the data dictionary with "{}" surrounding the key (eg user.name)
    """

    def __init__(
        self,
        layout: Layout,
        palettes=[],
        widgets: list[type[WidgetBuilder]] = [],
        css_variables: dict[str, str] = {},
    ):
        self.layout = layout
        self.palettes = palettes
        self.widgets = widgets
        self.css_variables = css_variables
        self.data = {}

    def get_palettes(self):
        return self.palettes

    def get_resource(self, name):
        if hasattr(self, name):
            return getattr(self, name)
        else:
            raise UnknownResource(f"Could not custom resource '@{name}'")

    def parse_string_template(self, template):
        variables = [
            field for _, field, _, _ in string.Formatter().parse(template) if field
        ]
        value = template
        for variable in variables:
            value = value.replace(f"{{{variable}}}", self._get_data_resource(variable))
        return value

    def _get_data_resource(self, attr):
        keys = attr.split(".")
        value = self.data
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

    def parse_resources_tag(self, element: etree.Element):
        for child in element:
            if child.tag == f"{XML_NS}python":
                module_path = child.get("module")
                if module_path is None:
                    raise ValueError(
                        "Could not get attribute 'module' for mu:python element"
                    )

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

    def get_widget_builder(self, tag: str) -> type[WidgetBuilder] | None:
        cls_lower = tag.lower()
        for cls in self.widgets:
            if cls_lower == cls.__name__.lower():
                return cls

    def get_css_variables(self) -> dict[str, str]:
        return self.css_variables

    def on_load(self):
        return

    def on_enter(self):
        pass

    def on_exit(self):
        pass


class Layout:
    def __init__(
        self,
        xml_path: Path,
        css_path: Path | None = None,
        resources_cls=LayoutResourceHandler,
        xml_dir=None,
        css_dir=None,
    ) -> None:
        self.resources = resources_cls(self)
        self.widget_map = {}

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

    def register_widgets(self, widgets: list[type[WidgetBuilder]]):
        self.resources.widgets.extend(widgets)

    def style_widget(self, widget: urwid.Widget, classes=[], id=None) -> urwid.AttrMap:
        return self.xml_parser.style_widget(widget, classes, id)

    def load(self):
        """Parse the XML and CSS"""
        self.css_parser = CSSParser(self.css_path, self.resources.get_css_variables())
        self.xml_parser = XMLParser(self.xml_path, self.resources, self.css_parser)
        self.resources.on_load()
        return self

    def get_root(self):
        return self.xml_parser.get_root()

    def get_palettes(self):
        if (palettes := self.resources.get_palettes()) is None:
            palettes = []
        return self.xml_parser.get_palettes() + palettes

    def get_widget_by_id(self, id) -> urwid.Widget | None:
        return self.xml_parser.get_widget_by_id(id)

    def on_enter(self):
        self.resources.on_enter()

    def on_exit(self):
        self.resources.on_exit()
