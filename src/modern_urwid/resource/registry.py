"""
Handles storing Python modules
"""

from types import ModuleType

from modern_urwid.exceptions import UnknownModule


class ModuleRegistry:
    """
    Simple registry for Python modules
    """

    def __init__(self):
        self.modules: dict[str, ModuleType] = {}

    def register(self, name: str, module: ModuleType):
        """Store the given module in the registry

        :param name: The name of the module
        :type name: str
        :param module: The Python module to register
        :type module: types.ModuleType
        """
        self.modules[name] = module

    def is_registered(self, name: str):
        return name in self.modules

    def get(self, name: str) -> ModuleType:
        """Get a registered module

        :param name: The name of the module
        :type name: str
        :raises UnknownModule: Raises if a module is not found with the given name
        :return: The Python module, if registered
        :rtype: types.ModuleType
        """
        if module := self.modules.get(name):
            return module
        else:
            raise UnknownModule(name)
