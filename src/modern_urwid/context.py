from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from urwid import Widget

from .resource.registry import ModuleRegistry
from .style.registry import StyleRegistry
from .widgets.registry import WidgetRegistry


class CompileContext:
    def __init__(
        self,
        base_dir: Path,
        widget_registry: WidgetRegistry = WidgetRegistry(),
        style_registry: StyleRegistry = StyleRegistry(),
        module_registry: ModuleRegistry = ModuleRegistry(),
    ):
        self.base_dir = base_dir.resolve()
        self.widget_registry = widget_registry
        self.style_registry = style_registry
        self.module_registry = module_registry
        self.mapped_widgets: dict[str, "Widget"] = {}
        self.custom_data = {}

    def resolve_path(self, path: Union[str, Path]) -> Path:
        return (self.base_dir / Path(path)).resolve()

    def get_widget_by_id(self, id) -> Union["Widget", None]:
        return self.mapped_widgets.get(id)

    def set(self, key: str, value: Any):
        self.custom_data[key] = value

    def get(self, key: str, default: Any = None):
        return self.custom_data.get(key, default)
