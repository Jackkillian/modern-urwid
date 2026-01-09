# Usage

## Basic XML/CSS Rendering with CompileContext and LifecycleManager
The `CompileContext` class is used to manage resources for controllers, including custom widgets, and styles/palettes:
```python
context = CompileContext("/path/to/base/dir")
```

A `LifecycleManager` is used to load layouts and switch between them:
```python
manager = LifecycleManager(context)
```

Then, layouts with XML and CSS can be created from a file path:
```python
manager.register(
    "resources/layouts/layout.xml", # this will be resolved under the base path provided to CompileContext
    "main" # name of the layout/controller
)
```

XML is used to create layouts. Note that attributes are passed as keyword arguments to urwid widgets. If an attribute's value starts with `@`, it will be treated as a resource and will be resolved from any loaded modules. String templates can also be used in a similar way by wrapping a value with brackets (`{}`).
Attributes in the MU namespace will be treated specially:
- `mu:id` - The ID of the widget. Used for styling and widget binding.
- `mu:class` - Any classes to apply to the widget. Used for styling.
- `mu:height` - Specify the height (or width in a horizontal container) of a widget.
- `mu:weight` - Specify the weight of a widget in its container. Overrides `mu:height`.
- `mu:pack` - Pack the widget in its container. Overrides `mu:weight`.

XML:
```xml
<pile xmlns:mu="https://github.com/Jackkillian/modern-urwid" mu:id="root">
    <mu:resources>
        <mu:python module="tests.basic" />
        <mu:stylesheet path="styles.css" />
    </mu:resources>
    <mu:layout on_load="@basic.on_load" />
    <filler mu:height="1" mu:class="header">
        <text>Hello, world</text>
    </filler>
    <filler mu:height="1">
        <edit caption="Edit: ">
            <mu:signal name="change" callback="@basic.on_edit_change" />
        </edit>
    </filler>
    <filler mu:height="1"><button
            on_press="@basic.quit_callback"
        >Quit</button></filler>
    <scrollbar>
        <listbox mu:id="dynamic_listbox" />
    </scrollbar>
</pile>
```

CSS:
```css
#root {
    color: dark blue;
    background: light gray;
}

.header {
    color:
        dark red,
        bold,
        italics;
}

.listbox-child {
    background: dark gray;
}
```

Python modules can be used to define resources such as callbacks and various data, as well as the three layout lifecycle hooks: `on_load`, `on_enter`, and `on_exit`. The `on_load` hook and other callbacks are defined in the `tests.basic` module as referenced in the XML:
```python
import urwid
from modern_urwid import CompileContext, LayoutNode
from modern_urwid.compiler import create_wrapper

def on_load(ctx: CompileContext):
    # get the widget with id "dynamic_listbox"
    my_listbox: urwid.ListBox = ctx.get_local("main").get_widget_by_id( # "main" references the layout name
        "dynamic_listbox"
    )

    # load the urwid palette names for the widgets we will create
    _, palette, focus_palette = ctx.style_registry.get(
        create_wrapper("button", classes="listbox-child")
    )

    # add children to the listbox
    my_listbox.body.extend(
        [
            urwid.AttrMap(urwid.Button(f"This is custom button #{i}"), palette, focus_palette)
            for i in range(10)
        ]
    )

def on_edit_change(node: LayoutNode, ctx: CompileContext, w: urwid.Edit, full_text):
    w.set_caption(f"Edit ({full_text}): ")

def quit_callback(node: LayoutNode, ctx: CompileContext, w):
    raise urwid.ExitMainLoop()
```

Before the MainLoop can be run, a layout must be activated with `switch()`.
```python
manager.switch("main") # switch to the layout named "main"
manager.run() # calls urwid.MainLoop.run
```


## Rendering custom widgets
Custom widgets can be made by extending the `WidgetBuilder` class and registered with the `@context.widget_registry.register()` decorator:
```python
@context.widget_registry.register()
class CustomWidget(WidgetBuilder):
    tag = "customwidget"

    def build(self, **kwargs):
        return urwid.Filler(
            urwid.Text(f"This is a custom widget with tag <{self.node.tag}>")
        )
```

Alternately, you can use the `<mu:widget module="..." />` tag in `<mu:resources>...</mu:resources>`, which will automatically register all classes extending `WidgetBuilder` in the given module.

Custom widgets can also be created from XML with the `parse_xml_layout()` method:
```python
@context.widget_registry.register()
class AnotherCustomWidget(WidgetBuilder):
    tag = "customwidgetfromxml"

    def build(self, **kwargs):
        return parse_xml_layout(
            self.context.resolve_path("path/to/my/widget.xml"),
            self.context,
        )[0]
```

```{note}
Custom widgets must be registered **before** layouts are registered.
```
