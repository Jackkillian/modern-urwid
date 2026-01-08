from typing import TYPE_CHECKING, Union

import urwid

from modern_urwid.style.css.wrapper import create_wrapper

if TYPE_CHECKING:
    from modern_urwid.context import CompileContext
    from modern_urwid.lifecycle.manager import Manager
    from modern_urwid.widgets.builder import WidgetBuilder


class Controller(object):
    """
    Utility class to handle lifecycle hooks
    """

    _state = {}

    def __init__(
        self,
        manager: Union["Manager", None] = None,
        context: Union["CompileContext", None] = None,
    ):
        if not hasattr(self, "name"):
            self.name = None
        self.__dict__ = self._state
        if context is not None:
            self.context = context
            self.local_data = context.get_local(self.name)
        if manager is not None:
            self.manager = manager

    def make_widget_from_builder(
        self,
        builder_cls: type["WidgetBuilder"],
        *args,
        id: Union[str, None] = None,
        classes: Union[str, None] = None,
        **kwargs,
    ) -> urwid.Widget:
        """Make an urwid widget from a given :class:`~modern_urwid.widgets.builder.WidgetBuilder`"""
        builder = builder_cls(None, self.context)
        widget = builder.build(*args, **kwargs)

        if id:
            if id in self.context.get(self.name).mapped_widgets:
                raise ValueError(f"Cannot duplicate IDs: {id}")
            self.context.get(self.name).mapped_widgets[id] = widget

        style, hash, focus_hash = self.context.style_registry.get(
            create_wrapper(str(builder_cls.tag), id, classes),
            # root_style, # TODO: load from layout??
        )

        widget = urwid.AttrMap(widget, hash, focus_hash)
        return builder.after_build(widget)

    def on_load(self):
        """Called when loading the parent layout in :meth:`~modern_urwid.lifecycle.manager.Manager.register`."""
        pass

    def on_enter(self):
        """Called when the parent layout is rendered on the mainloop with :meth:`~modern_urwid.lifecycle.manager.Manager.switch`."""
        pass

    def on_exit(self):
        """Called when the parent layout is removed from the mainloop with :meth:`~modern_urwid.lifecycle.manager.Manager.switch`."""
        pass
