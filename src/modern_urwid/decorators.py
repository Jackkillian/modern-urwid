from typing import Callable, TypeVar

T = TypeVar("T")


def assign_widget(id: str) -> Callable[[Callable[..., T]], T]:
    """
    Bind a widget.

    This is a decorator to automatically assign a class variable to a widget.
    The function will be overwritten with the widget instance.
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        fn._widget_id = id  # type: ignore[attr-defined]
        return fn

    return decorator  # type: ignore[reportReturnType]
