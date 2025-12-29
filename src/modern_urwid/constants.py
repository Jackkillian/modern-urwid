"""
This module contains all of the constants used in ``modern_urwid``.

Module variables:

- ``XML_NS`` - XML namespace for modern-urwid
- ``RESOURCE_CHAR`` - The character used to reference resources from ResourceHandler
- ``DEFAULT_STYLE`` - The default style for widgets
"""

XML_NS: str = "{https://github.com/Jackkillian/modern-urwid}"
RESOURCE_CHAR: str = "@"
DEFAULT_STYLE: dict[str, str] = {
    "color": "",
    "background": "",
    "monochrome": "",
    "color-adv": "",
    "background-adv": "",
}
