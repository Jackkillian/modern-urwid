import urwid

from modern_urwid import CompileContext, LayoutNode
from modern_urwid.compiler import create_wrapper


def on_load(ctx: CompileContext):
    my_listbox: urwid.ListBox = ctx.get_local("main").get_widget_by_id(
        "dynamic_listbox"
    )

    _, hash, focus_hash = ctx.style_registry.get(
        create_wrapper("button", classes="listbox-child")
    )
    my_listbox.body.extend(
        [
            urwid.AttrMap(urwid.Button(f"This is custom button #{i}"), hash, focus_hash)
            for i in range(10)
        ]
    )


def on_edit_change(node: LayoutNode, ctx: CompileContext, w: urwid.Edit, full_text):
    w.set_caption(f"Edit ({full_text}): ")


def quit_callback(node: LayoutNode, ctx: CompileContext, w):
    raise urwid.ExitMainLoop()
