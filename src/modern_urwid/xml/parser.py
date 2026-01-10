import re
from typing import TYPE_CHECKING

from modern_urwid.constants import RESOURCE_CHAR, XML_NS
from modern_urwid.resource.dummies import UnresolvedResource, UnresolvedTemplate
from modern_urwid.xml.ast import LayoutNode, MetaNode, Node

if TYPE_CHECKING:
    from lxml.etree import Element


TEMPLATE_PATTERN = r".*{.*}.*"


def parse_attrs(kwargs: dict):
    mu = {}
    normal = {}
    for k, v in kwargs.items():
        target = normal
        if k.startswith(XML_NS):
            k = k[len(XML_NS) :]
            target = mu
        if isinstance(v, str):
            if v.isdigit():
                target[k] = int(v)
            elif v.startswith(RESOURCE_CHAR):
                target[k] = UnresolvedResource(v[len(RESOURCE_CHAR) :])
            elif v == "False":
                target[k] = False
            elif v == "True":
                target[k] = True
            elif re.match(TEMPLATE_PATTERN, v):
                target[k] = UnresolvedTemplate(v)
            else:
                target[k] = v
    return mu, normal


def parse_element(element: "Element", parent=None) -> Node:
    """Get the AST representation of an XML element

    :param element: The XML element
    :type element: lxml.etree.Element
    :param parent: The AST representation of the parent of this XML element
    :type parent: Node, optional
    :return: An AST node
    :rtype: Node
    """
    children = []
    meta = []

    meta_attrs, attrs = parse_attrs(dict(element.attrib))

    if str(element.tag).startswith(XML_NS):
        node = MetaNode(
            str(element.tag).replace(XML_NS, ""), attrs, meta_attrs, parent=parent
        )
    else:
        node = LayoutNode(
            str(element.tag), element.text, attrs, meta_attrs, parent=parent
        )

    for child_el in element:
        if child_node := parse_element(child_el, node):
            if isinstance(child_node, LayoutNode):
                children.append(child_node)
            elif isinstance(child_node, MetaNode):
                meta.append(child_node)

    if isinstance(node, MetaNode):
        node.children = meta
    else:
        node.children = children
        node.meta = meta

    return node
