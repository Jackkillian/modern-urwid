import importlib.resources
from pathlib import Path

from modern_urwid import CompileContext, LifecycleManager


def test_layout_loads():
    context = CompileContext(Path(importlib.resources.files("tests.basic")))
    manager = LifecycleManager(context)
    manager.register(
        "layout.xml",
        "main",
    )
    manager.run("main")
