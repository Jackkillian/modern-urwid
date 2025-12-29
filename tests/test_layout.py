import importlib.resources
from pathlib import Path

import urwid

from modern_urwid import Layout, LayoutManager, LayoutResourceHandler, WidgetBuilder


def test_layout_loads():
    class CustomResources2(LayoutResourceHandler):
        pass

    class CustomResources(LayoutResourceHandler):
        def __init__(self, layout):
            self.Layout2Resources = CustomResources2(layout)
            super().__init__(
                layout,
                palettes=[
                    ("pb_empty", "white", "black"),
                    ("pb_full", "black", "light blue"),
                ],
                css_variables={"--my-var": "light gray"},
            )

        def quit_callback(self, w):
            raise urwid.ExitMainLoop()

        def on_edit_change(self, w: urwid.Edit, full_text):
            w.set_caption(f"Edit ({full_text}): ")

        def on_edit_postchange(self, w, text):
            widget = self.layout.get_widget_by_id("header_text")
            if isinstance(widget, urwid.Text):
                widget.set_text(text)

        def on_load(self):
            widget = self.layout.get_widget_by_id("dynamic")
            if isinstance(widget, urwid.ListBox):
                widget.body.extend(
                    [
                        self.layout.style_widget(
                            urwid.Button(f"Dynamic Button {i}"), id="root"
                        )
                        for i in range(10)
                    ]
                )

    manager = LayoutManager()

    @manager.register_widget()
    class CustomWidget(WidgetBuilder):
        def build(self, **kwargs):
            return urwid.Filler(urwid.Text("This is a custom widget!"))

    @manager.register_widget()
    class CustomWidgetFromXML(WidgetBuilder):
        def build(self, **kwargs):
            parser = self.render_from_xml(
                Path(importlib.resources.files("tests") / "resources" / "widget.xml"),
                css_path=Path(
                    importlib.resources.files("tests") / "resources" / "widget.css"
                ),
            )
            manager.register_palette(parser.get_palettes())
            return parser.get_root()

    manager.register(
        "layout",
        layout := Layout(
            Path(importlib.resources.files("tests") / "resources" / "layout.xml"),
            Path(importlib.resources.files("tests") / "resources" / "styles.css"),
            CustomResources,
        ),
    )

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
