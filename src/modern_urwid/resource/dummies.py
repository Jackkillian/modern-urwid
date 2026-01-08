"""
Various classes representing unresolved AST attributes
"""


class UnresolvedResource:
    """Represents an unresolved resource from a module

    :param path: A module path to a resource (e.g. ``extra.on_load``)
    :type path: str
    """

    def __init__(self, path: str):
        self.path = path

    def __repr__(self) -> str:
        return f"<UnresolvedResource path={self.path}>"


class UnresolvedTemplate:
    """Represents an unresolved string template

    :param template: A string template (e.g. ``User ID: {users.data.id}``)
    :type template: str
    """

    def __init__(self, template: str):
        self.value = template

    def __repr__(self) -> str:
        return f"<UnresolvedTemplate value={self.value}>"
