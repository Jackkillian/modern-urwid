class UnresolvedResource:
    def __init__(self, path: str):
        self.path = path

    def __repr__(self) -> str:
        return f"<UnresolvedResource path={self.path}>"


class UnresolvedTemplate:
    def __init__(self, template: str):
        self.value = template

    def __repr__(self) -> str:
        return f"<UnresolvedTemplate path={self.value}>"
