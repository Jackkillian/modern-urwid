from typing import TYPE_CHECKING, Union

from cssselect2 import Matcher
from dict_hash import md5

from modern_urwid.constants import DEFAULT_STYLE

if TYPE_CHECKING:
    from cssselect2.tree import ElementWrapper


class StyleRegistry:
    def __init__(self, selectors: list[tuple] = [], pseudos: dict = {}):
        self.matcher = Matcher()
        if selectors:
            self.add_selectors(selectors)
        self.pseudo_map = pseudos.copy()
        self.palettes = {}

    def get(
        self, element: "ElementWrapper", default: dict[str, str] = DEFAULT_STYLE
    ) -> tuple[dict[str, str], str, Union[str, None]]:
        style = default.copy()
        pseudos = {}
        if matches := self.matcher.match(element):
            matches.sort()
            for match in matches:
                specificity, order, pseudo, payload = match
                sel_str, data = payload
                style.update(data)

                # Default to 8-bit colors if true colors are not defined
                if "color-adv" not in data:
                    style["color-adv"] = style["color"]

                if "background-adv" not in data:
                    style["background-adv"] = style["background"]

                if sel_str in self.pseudo_map:
                    pseudos = self.pseudo_map[sel_str]

        normal_hash = md5(style)
        if normal_hash not in self.palettes:
            self.palettes[normal_hash] = style

        focus_hash = normal_hash
        if (
            "focus" in pseudos
            and (focus_hash := md5(pseudos["focus"])) not in self.palettes
        ):
            self.palettes[focus_hash] = {**style.copy(), **pseudos["focus"]}

        return style, normal_hash, focus_hash

    def add_selectors(self, selectors: list[tuple]):
        for selector in selectors:
            self.matcher.add_selector(*selector)

    def get_palettes(self) -> list[tuple]:
        return [(hash, *style.values()) for hash, style in self.palettes.items()]
