from types import LambdaType

import urwid

from .builder import WidgetBuilder
from .layout import Layout


class LayoutManager:
    def __init__(self, loop: urwid.MainLoop | None = None):
        if loop is None:
            self.loop = urwid.MainLoop(urwid.Text(""))
        else:
            self.loop: urwid.MainLoop = loop
        self.layouts: dict[str, Layout] = {}
        self.current: str | None = None
        self.widgets: list[type[urwid.WidgetBuilder]] = []

    def register(self, name: str, layout: Layout):
        self.layouts[name] = layout
        layout.register_widgets(self.widgets)
        layout.load()
        self.loop.screen.register_palette(layout.get_palettes())

    def switch(self, name: str):
        if self.current:
            self.layouts[self.current].on_exit()

        layout = self.layouts[name]
        layout.on_enter()
        self.loop.widget = layout.get_root()
        self.current = name

    def register_palette(self, palette):
        self.loop.screen.register_palette(palette)

    def register_widget(self, cls: type[WidgetBuilder] | None = None) -> LambdaType:
        def decorator(cls: type[WidgetBuilder]):
            self.widgets.append(cls)
            return cls

        if cls:
            self.widgets.append(cls)

        return decorator

    def get_loop(self):
        return self.loop
