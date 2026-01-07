from typing import Union

import cssselect2
import lxml.etree


def create_wrapper(
    tag: str, id: Union[str, None] = None, classes: Union[str, None] = None
):
    element = lxml.etree.Element(tag)
    if id:
        element.set("id", id)
    if classes:
        element.set("class", classes)
    return cssselect2.ElementWrapper.from_xml_root(element)
