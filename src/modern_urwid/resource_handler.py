from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .builder import WidgetBuilder

from lxml import etree

from .exceptions import InvalidTemplate, UnknownResource


class ResourceHandler:
    def get_resource(self, name: str) -> Any:
        """Load a given resource, referenced by ``<tag attribute="@MyResource" />``"""
        raise UnknownResource(
            f"Could not get resource '@{name}' - get_resource() not implemented"
        )

    def parse_string_template(self, template) -> str:
        """Parse a given string template, e.g. ``"User: {user.id}"``"""
        raise InvalidTemplate(
            f"Could not parse template '{{{template}}}' - parse_string_template() not implemented"
        )

    def parse_resources_tag(self, element: etree.Element) -> None:
        """Parse the ``<mu:resources />`` tag"""
        raise ValueError(
            f"Could not parse element: {element} - load_resources_from_tag() not implemented"
        )

    def get_widget_builder(self, tag: str) -> Union[type["WidgetBuilder"], None]:
        """Get a widget builder for a custom widget tag."""
        return None

    def get_css_variables(self) -> dict[str, str]:
        """Get custom CSS variables, used to override stylesheet variables."""
        return {}
