from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from urwid import Widget

from .resource.registry import ModuleRegistry
from .style.registry import StyleRegistry
from .widgets.registry import WidgetRegistry


class LocalData:
    """Local data applied to an individual controller"""

    def __init__(self):
        self.mapped_widgets: dict[str, "Widget"] = {}
        self.custom_data = {}

    def get_widget_by_id(self, id) -> Union["Widget", None]:
        return self.mapped_widgets.get(id)

    def set(self, key: str, value: Any):
        self.custom_data[key] = value

    def get(self, key: str, default: Any = None):
        return self.custom_data.get(key, default)


class CompileContext:
    """Compile context applied to all layouts

    :param base_dir: The root directory for all referenced files
    :type base_dir: pathlib.Path
    :param widget_registry: The widget registery used for all layouts
    :type widget_registry: WidgetRegistry, optional
    :param style_registry: The style registery used for all layouts
    :type style_registry: StyleRegistry, optional
    :param module_registry: The module registery used for all layouts
    :type module_registry: ModuleRegistry, optional
    """

    def __init__(
        self,
        base_dir: Path,
        widget_registry: WidgetRegistry = None,
        style_registry: StyleRegistry = None,
        module_registry: ModuleRegistry = None,
    ):
        self.base_dir = base_dir.resolve()
        if widget_registry is None:
            widget_registry = WidgetRegistry()
        self.widget_registry = widget_registry
        if style_registry is None:
            style_registry = StyleRegistry()
        self.style_registry = style_registry
        if module_registry is None:
            module_registry = ModuleRegistry()
        self.module_registry = module_registry
        self.local_data: dict[str, LocalData] = {}
        self.current_key: Union[str, None] = None
        self.custom_data: dict[str, Any] = {}

    def resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve a path under the base directory

        :param path: The path to resolve
        :type path: str | pathlib.Path
        :return: The resolved path
        :rtype: pathlib.Path
        """
        return (self.base_dir / Path(path)).resolve()

    def add_local(self, name: str):
        """Add a :class:`~modern_urwid.context.LocalData` entry under the given name"""
        self.local_data[name] = LocalData()
        self.current_key = name

    def get_local(self, name: Union[str, None] = None) -> LocalData:
        """
        Get the :class:`~modern_urwid.context.LocalData` entry under the given name.
        Defaults to the current_key if no name is provided.
        """
        if name is None:
            if self.current_key:
                name = self.current_key
            else:
                raise ValueError("Data key is not defined")
        return self.local_data[name]

    def set_local_key(self, name: str):
        """Set the default key to use if :meth:`get_local` is called with no arguments"""
        self.current_key = name

    def set_custom(self, key: str, value: Any):
        """Set a custom data value, accessible by any layout using this context"""
        self.custom_data[key] = value

    def get_custom(self, key: str, default: Any = None):
        """Get a custom data value"""
        return self.custom_data.get(key, default)
