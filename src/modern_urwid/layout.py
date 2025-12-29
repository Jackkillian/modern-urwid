from __future__ import annotations

import importlib
import string
from pathlib import Path
from types import ModuleType
from typing import Union

import urwid
from lxml import etree

from modern_urwid.resource_handler import ResourceHandler
from modern_urwid.xml_parser import XMLParser

from .builder import WidgetBuilder
from .constants import XML_NS
from .css_parser import CSSParser
from .exceptions import UnknownResource


class LayoutResourceHandler(ResourceHandler):
    """
    A base class for extending a layout's functionality.

    Reference properties from the base class (e.g. callbacks) with the ``@`` prefix.
    Reference properties from the data dictionary with brackets surrounding the key (e.g. ``"{user.name}"``).
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
        """Get custom palettes."""
        return self.palettes

    def get_resource(self, name):
        """Get a custom resource (typically referenced by ``@ResourceName`` in XML)."""
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

    def get_widget_builder(self, tag: str) -> Union[type[WidgetBuilder], None]:
        cls_lower = tag.lower()
        for cls in self.widgets:
            if cls_lower == cls.__name__.lower():
                return cls

    def get_css_variables(self) -> dict[str, str]:
        return self.css_variables

    def on_load(self):
        """Called when loading the parent layout in :meth:`~modern_urwid.layout_manager.LayoutManager.register`."""
        return

    def on_enter(self):
        """Called when the parent layout is rendered on the mainloop with :meth:`~modern_urwid.layout_manager.LayoutManager.switch`."""
        pass

    def on_exit(self):
        """Called when the parent layout is removed from the mainloop with :meth:`~modern_urwid.layout_manager.LayoutManager.switch`."""
        pass


class Layout:
    """
    Create a UI layout from XML and CSS.

    This class is responsible for parsing XML and applying
    CSS styles to the created widgets. The root widget can
    be referenced with :meth:`get_root`.
    """

    def __init__(
        self,
        xml_path: Path,
        css_path: Union[Path, None] = None,
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
        """Add custom widget builders for the XML parser. Note: do this before calling :meth:`load`."""
        self.resources.widgets.extend(widgets)

    def style_widget(self, widget: urwid.Widget, classes=[], id=None) -> urwid.AttrMap:
        """Style a widget according to any given classes or id it may have."""
        return self.xml_parser.style_widget(widget, classes, id)

    def load(self):
        """Parse the XML and CSS. Make sure to call :meth:`register_widgets` first if neccessary."""
        self.css_parser = CSSParser(self.css_path, self.resources.get_css_variables())
        self.xml_parser = XMLParser(self.xml_path, self.resources, self.css_parser)
        self.resources.on_load()
        return self

    def get_root(self) -> urwid.Widget:
        """Get the root XML widget that can be rendered."""
        return self.xml_parser.get_root()

    def get_palettes(self):
        """Get all palettes used in this layout."""
        if (palettes := self.resources.get_palettes()) is None:
            palettes = []
        return self.xml_parser.get_palettes() + palettes

    def get_widget_by_id(self, id) -> Union[urwid.Widget, None]:
        """Get a widget by its ``id`` attribute."""
        return self.xml_parser.get_widget_by_id(id)

    def on_enter(self):
        """Called when this is rendered on the mainloop with :meth:`~modern_urwid.layout_manager.LayoutManager.switch`."""
        self.resources.on_enter()

    def on_exit(self):
        """Called when this is removed from the mainloop with :meth:`~modern_urwid.layout_manager.LayoutManager.switch`."""
        self.resources.on_exit()
