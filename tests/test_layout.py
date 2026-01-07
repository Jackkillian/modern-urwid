import importlib.resources
from pathlib import Path

import urwid

import modern_urwid
from modern_urwid import CompileContext, WidgetBuilder, WidgetRegistry


def test_layout_loads():
    widget_registry = WidgetRegistry()

    @widget_registry.register()
    class CustomWidget(WidgetBuilder):
        tag = "customwidget"

        def build(self, **kwargs):
            return urwid.Filler(
                urwid.Text(f"This is a custom widget with tag <{self.node.tag}>")
            )

    # selectors, pseudo_map = parse_stylesheet(
    #     Path(importlib.resources.files("tests") / "resources" / "styles.css"),
    #     {"--my-var": "light gray"},
    # )
    # style_registry = StyleRegistry(selectors, pseudo_map)
    context = CompileContext(Path(importlib.resources.files("tests")), widget_registry)

    loop = urwid.MainLoop(
        urwid.Text(""),
        palette=[
            ("pb_empty", "white", "black"),
            ("pb_full", "black", "light blue"),
        ],
    )
    loop.screen.set_terminal_properties(2**24)

    manager = modern_urwid.Manager(context, loop)
    manager.register("main", "resources/layouts/layout.xml")
    manager.run("main")

    # loop.run()
    # loop.screen.clear()
    # loop.draw_screen()
    return

    assert isinstance(layout.get_root(), urwid.AttrMap)
    assert isinstance(layout.get_root().base_widget, urwid.Pile)

    screen: urwid.display.raw.Screen = manager.get_loop().screen
    screen.set_terminal_properties(2**24)

    manager.switch("layout")
    manager.run()

    # loop.start()
    # loop.screen.clear()
    # loop.draw_screen()

    # time.sleep(10)
