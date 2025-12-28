# modern-urwid
An urwid library for creating TUIs from XML and CSS

## Installation
Instal with:  
`pip install modern-urwid`

## Features
- Read XML and CSS files and parse them into urwid Widgets using the `Layout` and `LayoutResources` classes

### Example
Python:
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
  
XML:
```xml
<pile xmlns:mu="https://github.com/Jackkillian/modern-urwid" id="root">
    <filler mu:height="1"><text
            id="header_text"
            class="custom"
        >Hello, world!</text></filler>
    <filler mu:height="1">
        <edit caption="Edit: ">
            <mu:signal name="change" callback="@on_edit_change" />
            <mu:signal name="postchange" callback="@on_edit_postchange" />
        </edit>
    </filler>
    <filler mu:height="1">
        <button on_press="@quit_callback">Quit</button>
    </filler>
    <filler mu:height="1">
        <progressbar
            normal="pb_empty"
            complete="pb_full"
            current="57"
        />
    </filler>
    <filler valign="middle">
        <text>This inherits the root pile style</text>
    </filler>
    <customwidget />
    <columns mu:height="1">
        <filler mu:weight="75"><text class="col1">Col 1</text></filler>
        <filler mu:weight="25"><text class="col2">Col 2</text></filler>
    </columns>
</pile>
```
  
CSS:
```css
#root {
    color: black;
    background: dark gray;
}
edit { color: white; }
.custom {
    color: light green;
    background: dark gray;
}
button { color: yellow; }
button:focus { color: light red; }
.col1 { background: dark blue; }
.col2 {
    color: black;
    background: brown;
}
```
