from __future__ import annotations

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from modern_urwid.resource.dummies import UnresolvedResource, UnresolvedTemplate


class Node:
    def __init__(
        self,
        tag: str,
        text: Union[str, None],
        attrs: dict[
            str, Union[str, int, bool, "UnresolvedResource", "UnresolvedTemplate"]
        ],
        meta_attrs: dict[
            str, Union[str, int, bool, "UnresolvedResource", "UnresolvedTemplate"]
        ],
        children: list[Node] = [],
        parent: Union[Node, None] = None,
    ):
        self.tag = tag
        self.text = text
        self.attrs = attrs
        self.meta_attrs = meta_attrs
        self.children = children if children else []
        self.parent = parent

    def get_attr(
        self, name, default=None
    ) -> Union[str, int, bool, "UnresolvedResource", "UnresolvedTemplate", None]:
        return self.attrs.get(name, default)

    def get_meta_attr(
        self, name, default=None
    ) -> Union[str, int, bool, "UnresolvedResource", "UnresolvedTemplate", None]:
        return self.meta_attrs.get(name, default)


class MetaNode(Node):
    """
    Defined by mu namespace tags
    """

    def __init__(
        self,
        tag: str,
        attrs: dict[
            str, Union[str, int, bool, "UnresolvedResource", "UnresolvedTemplate"]
        ],
        meta_attrs: dict[
            str, Union[str, int, bool, "UnresolvedResource", "UnresolvedTemplate"]
        ],
        children: list[MetaNode] = [],
        parent: Union[Node, None] = None,
    ):
        super().__init__(tag, None, attrs, meta_attrs, children, parent=parent)


class LayoutNode(Node):
    def __init__(
        self,
        tag: str,
        text: Union[str, None],
        attrs: dict[
            str, Union[str, int, bool, "UnresolvedResource", "UnresolvedTemplate"]
        ],
        meta_attrs: dict[
            str, Union[str, int, bool, "UnresolvedResource", "UnresolvedTemplate"]
        ],
        children: list[LayoutNode] = [],
        meta: list[MetaNode] = [],
        parent: Union[LayoutNode, None] = None,
    ):
        super().__init__(tag, text, attrs, meta_attrs, children, parent=parent)
        self.meta = meta if meta else []
