from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from modern_urwid.widgets.builder import WidgetBuilder

from modern_urwid.widgets.builders import GenericWidgetBuilder, ListBoxBuilder

DEFAULT_BUILDERS = [ListBoxBuilder]


class WidgetRegistry:
    def __init__(self, builders: list[type["WidgetBuilder"]] = []):
        self.builders: dict[str, type["WidgetBuilder"]] = {}
        for builder in DEFAULT_BUILDERS + builders:
            self.register(builder)

    def register(self, builder_cls: Union[type["WidgetBuilder"], None] = None):
        """
        Register a custom widget builder.

        This can be used either as a decorator:
            ``@widget_registry.register()``
        Or by directly passing a class:
            ``widget_registry.register(MyCustomBuilder)``
        """

        def decorator(cls: type["WidgetBuilder"]):
            if not cls.tag:
                raise ValueError("WidgetBuilder must define a tag")
            self.builders[cls.tag] = cls
            return cls

        if builder_cls is not None:
            decorator(builder_cls)

        return decorator

    def get(self, tag: str) -> type["WidgetBuilder"]:
        if builder := self.builders.get(tag):
            return builder
        else:
            return GenericWidgetBuilder
