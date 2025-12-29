from types import LambdaType

import urwid

from .builder import WidgetBuilder
from .layout import Layout


class LayoutManager:
    """
    Manages multiple layouts and shared custom widgets and palettes
    between them.
    """

    def __init__(self, loop: urwid.MainLoop | None = None):
        if loop is None:
            self.loop = urwid.MainLoop(urwid.Text(""))
        else:
            self.loop: urwid.MainLoop = loop
        self.layouts: dict[str, Layout] = {}
        self.current: str | None = None
        self.widgets: list[type[urwid.WidgetBuilder]] = []

    def register(self, name: str, layout: Layout):
        """Register a new :class:`~modern_urwid.layout.Layout`"""
        self.layouts[name] = layout
        layout.register_widgets(self.widgets)
        layout.load()
        self.loop.screen.register_palette(layout.get_palettes())

    def switch(self, name: str):
        """
        Switch to a different layout by name.

        Calls the new layout's :meth:`~modern_urwid.layout.Layout.on_enter` method, and the
        old layout's :meth:`~modern_urwid.layout.Layout.on_exit` method.
        """
        if self.current:
            self.layouts[self.current].on_exit()

        layout = self.layouts[name]
        layout.on_enter()
        self.loop.widget = layout.get_root()
        self.current = name

    def register_palette(self, palette):
        """Register a set of palette entries in the urwid :class:`~urwid.MainLoop`."""
        self.loop.screen.register_palette(palette)

    def register_widget(self, cls: type[WidgetBuilder] | None = None) -> LambdaType:
        """
        Register a custom widget builder.

        This can be used either as a **decorator** (``@manager.register_widget()``)
        or by directly passing a class (``manager.register_widget(MyCustomBuilder)``).
        """

        def decorator(cls: type[WidgetBuilder]):
            self.widgets.append(cls)
            return cls

        if cls:
            self.widgets.append(cls)

        return decorator

    def get_loop(self) -> urwid.MainLoop:
        """Get the urwid :class:`~urwid.MainLoop`"""
        return self.loop

    def run(self):
        """Run the urwid :class:`~urwid.MainLoop`"""
        self.loop.run()
