import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Union

import urwid

from modern_urwid.compiler import parse_xml_layout
from modern_urwid.exceptions import LayoutNotFound, LayoutNotSpecified
from modern_urwid.lifecycle.controller import Controller
from modern_urwid.resource.dummies import UnresolvedResource
from modern_urwid.resource.utils import resolve_resource, wrap_callback

if TYPE_CHECKING:
    from modern_urwid.context import CompileContext


class LifecycleManager:
    """
    Manages multiple layouts and shared resources between them.
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

    def register(self, layout_path: Union[str, Path], key: Union[str, None] = None):
        """Register a  new layout

        :param layout_path: Layout name to switch to
        :type layout_path: str | pathlib.Path
        :param key: The key to register the layout under
        :type key: str, optional
        :raises ValueError: Raises if an incorrect key value is found
        :raises TypeError: Raises if the provided controller does not extend :class:`~modern_urwid.lifecycle.controller.Controller`
        """
        if key is None:
            key = Path(layout_path).stem

        node, meta = parse_xml_layout(
            self.context.resolve_path(layout_path), self.context, key
        )

        layout_config = meta.get("layout")
        if "controller" in layout_config:
            if inspect.isclass(
                controller_cls := resolve_resource(
                    self.context.module_registry, layout_config["controller"], False
                )
            ) and issubclass(controller_cls, Controller):
                controller = controller_cls(self, self.context)
                if controller.name is None:
                    raise ValueError(f"{controller_cls.__name__}.name can not be None")
                elif controller.name != key:
                    raise ValueError(
                        f"{controller_cls.__name__}.name must be the same as the provided name: '{key}'"
                    )
            else:
                raise TypeError(
                    f"Provided resource for controller ({controller_cls.__name__}) does not extend the Controller class"
                )
        else:
            controller = Controller(self, self.context)
            controller.name = key
            if "on_load" in layout_config:
                on_load_res = layout_config["on_load"]
                if not isinstance(on_load_res, UnresolvedResource):
                    raise ValueError("on_load is not a resource reference")
                if callable(
                    resource := resolve_resource(
                        self.context.module_registry,
                        on_load_res,
                    )
                ):
                    controller.on_load = wrap_callback(resource, self.context)
            if "on_enter" in layout_config:
                on_enter_res = layout_config["on_enter"]
                if not isinstance(on_enter_res, UnresolvedResource):
                    raise ValueError("on_enter is not a resource reference")
                if callable(
                    resource := resolve_resource(
                        self.context.module_registry,
                        on_enter_res,
                    )
                ):
                    controller.on_enter = wrap_callback(resource, self.context)
            if "on_exit" in layout_config:
                on_exit_res = layout_config["on_exit"]
                if not isinstance(on_exit_res, UnresolvedResource):
                    raise ValueError("on_exit is not a resource reference")
                if callable(
                    resource := resolve_resource(
                        self.context.module_registry,
                        on_exit_res,
                    )
                ):
                    controller.on_exit = wrap_callback(resource, self.context)

        self.layouts[controller.name] = node
        self.controllers[controller.name] = controller
        for name, attr in controller.__class__.__dict__.items():
            widget_id = getattr(attr, "_widget_id", None)
            if widget_id is not None:
                widget = self.context.get_local().get_widget_by_id(widget_id)
                setattr(controller, name, widget)
        controller.on_load()

        # update all palettes
        self.loop.screen.register_palette(self.context.style_registry.get_palettes())

    def switch(self, name: str):
        """
        Switch to a different layout by name.

        Calls the new controller's :meth:`~modern_urwid.lifecycle.Controller.on_enter` method, and the
        old controller's :meth:`~modern_urwid.lifecycle.Controller.on_exit` method.

        :param name: Layout name to switch to
        :type name: str
        :raises LayoutNotFound: Raises if a layout is not found with the given name
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
        """Run the MainLoop

        :param name: If provided, switch to this layout before running
        :type name: str, optional
        """
        if name:
            self.switch(name)

        if self.current is None:
            raise LayoutNotSpecified("No layout is selected to render.")

        self.loop.run()

    def get_loop(self) -> urwid.MainLoop:
        """Get this manager's mainloop

        :return: The mainloop this manager uses
        :rtype: urwid.MainLoop
        """
        return self.loop
