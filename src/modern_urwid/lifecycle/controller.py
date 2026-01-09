from typing import TYPE_CHECKING, Union, Any

import urwid

from modern_urwid.style.css_parser import create_wrapper

if TYPE_CHECKING:
    from modern_urwid.context import CompileContext
    from modern_urwid.lifecycle.manager import LifecycleManager
    from modern_urwid.widgets.builder import WidgetBuilder


class SingletonMeta(type):
    _instances: dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        else:
            cls._instances[cls]._setup(*args, **kwargs)
        return cls._instances[cls]


class Controller(metaclass=SingletonMeta):
    """
    Utility class to handle lifecycle hooks and extra UI logic
    """

    def __init__(
            self,
            manager: Union["LifecycleManager", None] = None,
            context: Union["CompileContext", None] = None,
        ):
            if not hasattr(self, "name"):
                self.name = None
            self._setup(manager, context)

    def _setup(self,
        manager: Union["LifecycleManager", None] = None,
        context: Union["CompileContext", None] = None,
    ):
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
        """Called when loading the parent layout in :meth:`~modern_urwid.lifecycle.manager.LifecycleManager.register`."""
        pass

    def on_enter(self):
        """Called when the parent layout is rendered on the mainloop with :meth:`~modern_urwid.lifecycle.manager.LifecycleManager.switch`."""
        pass

    def on_exit(self):
        """Called when the parent layout is removed from the mainloop with :meth:`~modern_urwid.lifecycle.manager.LifecycleManager.switch`."""
        pass
