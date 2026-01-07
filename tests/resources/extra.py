import urwid

from modern_urwid import CompileContext, Controller, LayoutNode, assign_widget
from tests.resources.widgets import CustomButton


class MyController(Controller):
    @assign_widget("dynamic_listbox")
    def my_listbox(self) -> urwid.ListBox: ...

    def on_load(self):
        # my_listbox = self.context.get_widget_by_id("dynamic_listbox")
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

    # TODO: this doesnt need to be wrapped with ctx...
    def switch_controller(self, node: LayoutNode, ctx: CompileContext, w: urwid.Button):
        self.manager.switch("second")

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


class SecondController(Controller):
    # TODO: controllers use the same context, so any tags with the same id get overwritten
    @assign_widget("overwrite")
    def text(self) -> urwid.Text: ...

    def on_load(self):
        self.text.set_text("Welcome to modern-urwid")

    def switch_controller(self, node: LayoutNode, ctx: CompileContext, w: urwid.Button):
        self.manager.switch("main")
