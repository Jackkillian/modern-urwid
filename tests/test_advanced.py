import importlib.resources
from pathlib import Path

import urwid

from modern_urwid import CompileContext, LifecycleManager, WidgetBuilder


def test_layout_loads():
    context = CompileContext(Path(importlib.resources.files("tests.advanced")))

    @context.widget_registry.register()
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

    loop = urwid.MainLoop(
        urwid.Text(""),
        palette=[
            ("pb_empty", "white", "black"),
            ("pb_full", "black", "light blue"),
        ],
    )
    loop.screen.set_terminal_properties(2**24)

    manager = LifecycleManager(context, loop)
    manager.register("layouts/layout.xml", "main")
    manager.register("layouts/layout2.xml")

    assert "main" in manager.layouts
    assert "main" in manager.controllers
    assert isinstance(manager.layouts["main"], urwid.AttrMap)
    assert isinstance(manager.layouts["main"].base_widget, urwid.Pile)

    manager.run("main")

    # loop.start()
    # loop.screen.clear()
    # loop.draw_screen()

    # time.sleep(10)
