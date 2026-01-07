import urwid

import modern_urwid
from modern_urwid import CompileContext, Controller, LayoutNode
from tests.resources.widgets import CustomButton


class MyController(Controller):
    @modern_urwid.widget("dynamic_listbox")
    def my_listbox(self) -> urwid.ListBox: ...

    def on_load(self):
        # my_listbox = self.context.get_widget_by_id("dynamic_listbox")

        # TODO: dynamically make widgets from xml?
        self.my_listbox.body.extend(
            [
                self.make_widget_from_builder(
                    CustomButton,
                    classes="custom-class custom-class-bg",
                    label=f"This is custom button #{i}",
                )
                for i in range(10)
            ]
        )

    def on_edit_change(
        self, node: LayoutNode, ctx: CompileContext, w: urwid.Edit, full_text
    ):
        w.set_caption(f"Edit ({full_text}): ")

    def on_edit_postchange(self, node: LayoutNode, ctx: CompileContext, w, text):
        widget = ctx.get_widget_by_id("header_text")
        if isinstance(widget, urwid.Text):
            widget.set_text(text)

    def quit_callback(self, node: LayoutNode, ctx: CompileContext, w):
        raise urwid.ExitMainLoop()
