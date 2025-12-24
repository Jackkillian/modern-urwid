# modern-urwid
A small library providing various QOL urwid utilities.
  
Current features:
- Read XML and CSS files and parse them into urwid Widgets using the `Layout` and `LayoutResources` classes

Example:
```python
import urwid
import modern_urwid

class CustomWidget(urwid.WidgetWrap):
    def __init__(self):
        super().__init__(urwid.Filler(urwid.Text("Custom Widget")))

class CustomResources(modern_urwid.LayoutResources):
    def __init__(self, layout):
        super().__init__(
            layout,
            [CustomWidget],
            [("pb_empty", "white", "black"), ("pb_full", "white", "dark red")],
        )

    def quit_callback(self, w):
        raise urwid.ExitMainLoop()

    def on_edit_change(self, w, full_text):
        w.set_caption(f"Edit ({full_text}): ")

    def on_edit_postchange(self, w, text):
        self.layout.get_widget_by_id("header_text").set_text(text)

layout = modern_urwid.Layout("resources/layout.xml", "resources/styles.css", CustomResources)

urwid.MainLoop(
    layout.root,
    palette=layout.palettes,
).run()
```
