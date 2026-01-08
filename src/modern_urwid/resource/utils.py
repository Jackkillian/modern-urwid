"""
Various utilities for handling resources
"""

import importlib
import importlib.util
import inspect
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Union

from modern_urwid.lifecycle.controller import Controller

if TYPE_CHECKING:
    from modern_urwid.resource.dummies import UnresolvedResource
    from modern_urwid.resource.registry import ModuleRegistry


def wrap_callback(callback: Callable, *args) -> Callable:
    """Wrap a callback with the given arguments

    :param callback: The callback to wrap
    :type callback: Callable
    :return: Lambda that will call the original callback with
        the given arguments and any additional arguments at call time
    :rtype: Callable
    """
    return lambda *_args, **_kwargs: callback(*args, *_args, **_kwargs)


def resolve_resource(
    module_registry: "ModuleRegistry",
    unresolved: "UnresolvedResource",
    resolve_controllers: bool = True,
) -> Any:
    """Resolve a resource

    :param module_registry: The module registry
    :type module_registry: :class:`~modern_urwid.resource.registry.ModuleRegistry`
    :param unresolved: The unresolved resource to evaluate
    :type unresolved: :class:`~modern_urwid.resource.dummies.UnresolvedResource`
    :param resolve_controllers: Whether or not to instance controller classes
    :type resolve_controllers: bool
    :return: A resolved resource provided by a module
    :rtype: Any
    """
    path = unresolved.path
    if path.startswith("@"):
        path = path[1:]

    attrs = path.split(".")
    module_name = attrs.pop(0)
    module = module_registry.get(module_name)
    target = module
    for attr in attrs:
        if isinstance(target, dict):
            if attr not in target:
                raise AttributeError(
                    f"{target} does not have attribute '{attr}' (reading '{unresolved.path}')"
                )
            target = target[attr]
        elif hasattr(target, attr):
            target = getattr(target, attr)
        else:
            raise AttributeError(
                f"{target} does not have attribute '{attr}' (reading '{unresolved.path}')"
            )

        if (
            resolve_controllers
            and inspect.isclass(target)
            and issubclass(target, Controller)
        ):
            target = target()
    return target


def import_module(
    module_path: Union[str, None] = None, file_path: Union[Path, None] = None
) -> Union[tuple[str, ModuleType], None]:
    """Import a Python module from a given module or file path

    :param module_path: A Python module path (e.g. ``tests.resources.extra``), defualts to ``None``
    :type module_path: str, optional
    :param file_path: A file path to the module, defaults to ``None``
    :type file_path: str, optional
    :return: A tuple containing the python module and its name, or ``None`` if it could not be resolved
    :rtype: tuple[str, ModuleType] | None
    """
    if module_path:
        name = module_path.split(".")[-1]
        return name, importlib.import_module(module_path)
    elif file_path:
        name = file_path.stem
        spec = importlib.util.spec_from_file_location(name, str(file_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from path {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return name, module
    else:
        return None
