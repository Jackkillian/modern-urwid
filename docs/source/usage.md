# Usage

## Basic XML/CSS Rendering with Layout and LayoutManager
The `LayoutManager` class is used to manager layouts, custom widgets, and styles/palettes:
```python
manager = LayoutManager()
```

Layouts with XML and CSS are created with the `Layout` class:
```python
layout = Layout(
    Path("path/to/layout.xml"), # paths must be pathlib.Path
    Path("path/to/stylesheet.css"),
    CustomResources, # pass custom resources by class type (this can also be None)
)
```

XML:
```xml
<pile xmlns:mu="https://github.com/Jackkillian/modern-urwid" id="root">
    <filler mu:height="1">
        <text id="header_text" class="custom">Hello, world</text>
    </filler>
    <filler mu:height="1">
        <edit caption="Edit: ">
            <mu:signal name="change" callback="@on_edit_change" />
            <mu:signal name="postchange" callback="@on_edit_postchange" />
        </edit>
    </filler>
    <filler mu:height="1"><button
            on_press="@quit_callback"
        >Quit</button></filler>
    <solidfill mu:height="3">.</solidfill>
    <filler mu:height="2"><divider /></filler>
    <filler mu:height="1">
        <progressbar
            normal="pb_empty"
            complete="pb_full"
            current="57"
        />
    </filler>
    <filler valign="top" class="dark">
        <text>This should be dark</text>
    </filler>
    <padding mu:height="2" left="5" right="2">
        <filler>
            <text id="padded">Left is padded by 5; right is be 2</text>
        </filler>
    </padding>
    <customwidget />
    <customwidgetfromxml mu:height="1" />
    <scrollbar>
        <listbox id="dynamic" />
    </scrollbar>
</pile>
```

CSS:
```css
:root {
    --default-color: dark green;
    --my-var: light red;
}

edit {
    color: var(--default-color);
}

#root {
    color: black;
    background: var(--my-var);
}

.custom {
    color: light green;
    background: dark gray;
}

.dark {
    color: black;
    background: white;
}

button {
    color: yellow;
}

button:focus {
    color: light red;
}

scrollbar {
    color: light blue;
}

scrollbar:focus {
    color: black;
}
```

Layouts use the `LayoutResourceHandler` class to access custom widgets, palettes, CSS variables, and widget callbacks. The `LayoutResourceHandler` class can also be used to dynamically create additional widgets within the layout in the `on_load()` method, or handle the layout's `on_enter()` and `on_exit()` methods.
```python
class CustomResources(LayoutResourceHandler):
    def __init__(self, layout):
        super().__init__(
            layout,
            palettes=[
                ("pb_empty", "white", "black"),
                ("pb_full", "black", "light blue"),
            ],
            css_variables={"--my-var": "light gray"}, # override any variables in the stylesheet's ':root' declaration
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
        # get the widget with id="dynamic" from the XML
        widget = self.layout.get_widget_by_id("dynamic")
        # dynamically add 10 buttons to the listbox
        if isinstance(widget, urwid.ListBox):
            widget.body.extend(
                [
                    self.layout.style_widget( # use self.layout.style_widget() to apply the '#root' style
                        urwid.Button(f"Dynamic Button {i}"), id="root"
                    )
                    for i in range(10)
                ]
            )

    def on_enter(self):
        pass
    
    def on_exit(self):
        pass
```

Layouts can then be registered with the manager with `register()`. Before the MainLoop can be run, a layout must be activated with `switch()`.
```python
manager.register("my_layout", layout)
manager.switch("my_layout") # switch to the layout named "my_layout"
manager.run() # call urwid.MainLoop.run
```


## Rendering custom widgets
Custom widgets can be made with the `@manager.register_widget()` decorator:
```python
@manager.register_widget()
class CustomWidget(WidgetBuilder):
    def build(self, **kwargs):
        return urwid.Filler(urwid.Text("This is a custom widget!"))
```

Custom widgets can also be created from XML with the `self.render_from_xml()` method:
```python
@manager.register_widget()
class CustomWidgetFromXML(WidgetBuilder):
    def build(self, **kwargs):
        parser = self.render_from_xml(
            Path("path/to/my_custom_widget.xml",
            css_path=Path("path/to/my_custom_widget.css"),
        )

        # don't forget to register any custom palettes that
        # may be parsed from the widget's stylesheet:
        manager.register_palette(parser.get_palettes())
        return parser.get_root()
```

```{note}
Custom widgets must be registered **before** layouts are registered.
```
