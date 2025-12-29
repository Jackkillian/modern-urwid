from pathlib import Path

import urwid
from lxml import etree

from .css_parser import CSSParser
from .resource_handler import ResourceHandler
from .xml_parser import XMLParser


class WidgetBuilder:
    """
    Utility class used to build custom widgets. Widgets can be made
    with Python or XML. Use the ``LayoutManager.register_widget()`` decorator to register.
    """

    def __init__(
        self,
        element: etree.Element,
        children: list[urwid.Widget | urwid.WidgetContainerMixin] = [],
    ):
        self.element = element
        self.children = children

    def build(self, **kwargs) -> urwid.Widget:
        """Build the widget. When overriding, use the ``self.manager``, ``self.element``, ``self.children`` if applicable."""
        return urwid.Widget(**kwargs)

    def render_from_xml(
        self,
        xml_path: Path,
        resource_handler=ResourceHandler(),
        css_path: Path | None = None,
    ) -> XMLParser:
        """Render a widget from XML. Note: ``XMLParser.styles`` will need to be registered in urwid palettes."""
        return XMLParser(xml_path, resource_handler, CSSParser(css_path))
