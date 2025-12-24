import importlib.resources
import time

import urwid

from modern_urwid import Layout, LayoutResources


def test_layout_loads():
    class CustomWidget(urwid.WidgetWrap):
        def __init__(self):
            super().__init__(urwid.Filler(urwid.Text("Custom Widget")))

    class CustomResources(LayoutResources):
        def __init__(self, layout):
            super().__init__(
                layout,
                [CustomWidget],
                [("pb_empty", "white", "black"), ("pb_full", "white", "dark red")],
            )

        def quit_callback(self, w):
            raise urwid.ExitMainLoop()

        def on_edit_change(self, w: urwid.Edit, full_text):
            w.set_caption(f"Edit ({full_text}): ")

        def on_edit_postchange(self, w, text):
            widget = self.layout.get_widget_by_id("header_text")
            if isinstance(widget, urwid.Text):
                widget.set_text(text)

    layout_file = importlib.resources.files("tests") / "resources" / "layout.xml"
    styles_file = importlib.resources.files("tests") / "resources" / "styles.css"
    layout = Layout(str(layout_file), str(styles_file), CustomResources)

    assert isinstance(layout.get_root(), urwid.AttrMap)
    assert isinstance(layout.get_root().base_widget, urwid.Pile)

    loop = urwid.MainLoop(
        layout.root,
        palette=layout.palettes,
    )
    loop.run()

    # loop.start()
    # loop.screen.clear()
    # loop.draw_screen()

    # time.sleep(10)
