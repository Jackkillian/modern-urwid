import inspect
from typing import TYPE_CHECKING, Union

import urwid

from modern_urwid.compiler import parse_xml_layout
from modern_urwid.exceptions import LayoutNotFound, LayoutNotSpecified
from modern_urwid.lifecycle.controller import Controller
from modern_urwid.resource.dummies import UnresolvedResource
from modern_urwid.resource.utils import resolve_resource, wrap_callback

if TYPE_CHECKING:
    from pathlib import Path

    from modern_urwid.context import CompileContext


class Manager:
    """
    Manages multiple layouts and shared custom widgets and palettes
    between them.
    """

    def __init__(
        self, context: "CompileContext", loop: Union[urwid.MainLoop, None] = None
    ):
        if loop is None:
            self.loop = urwid.MainLoop(urwid.Text(""))
        else:
            self.loop: urwid.MainLoop = loop
        self.controllers: dict[str, "Controller"] = {}
        self.layouts: dict[str, urwid.Widget] = {}
        self.current: Union[str, None] = None
        self.context = context

    def register(self, name: str, layout_path: Union[str, "Path"]):
        """Register a new layout"""
        node, meta = parse_xml_layout(
            self.context.resolve_path(layout_path), self.context
        )
        self.layouts[name] = node

        layout_config = meta.get("layout")
        if "controller" in layout_config:
            if inspect.isclass(
                controller_cls := resolve_resource(
                    self.context.module_registry, layout_config["controller"], False
                )
            ) and issubclass(controller_cls, Controller):
                controller = controller_cls(self.context)
            else:
                raise TypeError(
                    f"Provided resource for controller ({controller_cls}) does not extend the Controller class"
                )
        else:
            controller = Controller(self.context)
            if "on_load" in layout_config:
                if callable(
                    resource := resolve_resource(
                        self.context.module_registry,
                        UnresolvedResource(layout_config["on_load"]),
                    )
                ):
                    controller.on_load = wrap_callback(resource, self.context)
            if "on_enter" in layout_config:
                if callable(
                    resource := resolve_resource(
                        self.context.module_registry,
                        UnresolvedResource(layout_config["on_enter"]),
                    )
                ):
                    controller.on_enter = wrap_callback(resource, self.context)
            if "on_exit" in layout_config:
                if callable(
                    resource := resolve_resource(
                        self.context.module_registry,
                        UnresolvedResource(layout_config["on_exit"]),
                    )
                ):
                    controller.on_exit = wrap_callback(resource, self.context)

        self.controllers[name] = controller
        for name, attr in controller.__class__.__dict__.items():
            widget_id = getattr(attr, "_widget_id", None)
            if widget_id is not None:
                widget = self.context.get_widget_by_id(widget_id)
                setattr(controller, name, widget)
        controller.on_load()

        # update all palettes
        self.loop.screen.register_palette(self.context.style_registry.get_palettes())

    def switch(self, name: str):
        """
        Switch to a different layout by name.

        Calls the new controller's :meth:`~modern_urwid.lifecycle.Controller.on_enter` method, and the
        old controller's :meth:`~modern_urwid.lifecycle.Controller.on_exit` method.
        """

        if name not in self.layouts:
            raise LayoutNotFound(f"Layout '{name}' is not registered")

        if self.current:
            self.controllers[self.current].on_exit()

        controller = self.controllers[name]
        controller.on_enter()
        self.loop.widget = self.layouts[name]
        self.current = name

    def run(self, name: Union[str, None] = None):
        if name:
            self.switch(name)

        if self.current is None:
            raise LayoutNotSpecified("No layout is selected to render.")

        self.loop.run()

    def get_loop(self) -> urwid.MainLoop:
        return self.loop
