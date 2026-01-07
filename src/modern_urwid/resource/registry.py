from types import ModuleType

from modern_urwid.exceptions import UnknownModule


class ModuleRegistry:
    def __init__(self):
        self.modules: dict[str, ModuleType] = {}

    def register(self, name: str, module: ModuleType):
        self.modules[name] = module

    def get(self, name: str) -> ModuleType:
        if module := self.modules.get(name):
            return module
        else:
            raise UnknownModule(name)
