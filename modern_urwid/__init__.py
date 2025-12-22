from pprint import pprint

import cssselect2
import tinycss2
import urwid
from dict_hash import md5
from lxml import etree
from tinycss2.ast import Node, WhitespaceToken


def pop_pseudos_from_tokens(tokens):
    result = []
    pseudos = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "literal" and token.value == ":":
            if len(tokens) > i + 1 and tokens[i + 1].type == "ident":
                pseudos.append(tokens[i + 1].value)
                i += 2
                continue
        elif token.type == "function":
            pseudos.append(token.name)
        else:
            result.append(token)
        i += 1
    return result, pseudos


def split_tokens_by_comma(tokens):
    selectors = []
    current = []
    for token in tokens:
        if isinstance(token, WhitespaceToken):
            continue
        if token.type == "literal" and token.value == ",":
            selectors.append(current)
            current = []
        else:
            current.append(token)
    if current:
        selectors.append(current)
    return selectors


def get_props(content):
    decls = tinycss2.parse_declaration_list(
        content, skip_comments=True, skip_whitespace=True
    )
    return {
        decl.name: "".join(
            [token.value for token in decl.value if hasattr(token, "value")]
        ).strip()
        for decl in decls
    }


DEFAULT_PROPS = {
    "color": "",
    "background": "",
    "monochrome": "",
    "color-adv": "",
    "background-adv": "",
}
WIDGET_MAP = {
    "text": lambda el, **kw: urwid.Text(el.text.strip() if el.text else "", **kw),
    "button": lambda el, **kw: urwid.Button(el.text.strip() if el.text else "", **kw),
    "pile": lambda el, children, **kw: urwid.Pile(children, **kw),
    "columns": lambda el, children, **kw: urwid.Columns(children, **kw),
    "filler": lambda el, children, **kw: urwid.Filler(
        children[0] if children else urwid.Divider(), **kw
    ),
}


class Layout:
    def __init__(self, xml_path, css_path) -> None:
        xml = open(xml_path).read()
        css = open(css_path).read()

        self.styles = {}
        self.matcher = cssselect2.Matcher()

        rules: list[Node] = tinycss2.parse_stylesheet(
            css,
            skip_comments=True,
            skip_whitespace=True,
        )
        self.parse_rules(rules)

        self.root = self.parse_element(
            cssselect2.ElementWrapper.from_html_root(etree.fromstring(xml))
        )

        self.palettes = []
        # now register the palettes
        for hash, style in self.styles.items():
            self.palettes.append((hash, *style.values()))

    def parse_rules(self, rules):
        self.pseudo_map = {}

        for rule in rules:
            element_selectors: list[list[Node]] = split_tokens_by_comma(rule.prelude)
            props = get_props(rule.content)
            for selectors in element_selectors:
                compiled = cssselect2.compile_selector_list(selectors)

                selectors, pseudos = pop_pseudos_from_tokens(
                    selectors
                )  # NOTE: overwrites selectors
                sel_str = tinycss2.serialize(selectors)

                for item in compiled:
                    self.matcher.add_selector(item, (sel_str, props))

                for pseudo in pseudos:
                    if sel_str not in self.pseudo_map:
                        self.pseudo_map[sel_str] = {}
                    self.pseudo_map[sel_str][pseudo] = props

    # TODO: style inheritance...
    def parse_element(self, wrapper: cssselect2.ElementWrapper):
        props = DEFAULT_PROPS.copy()
        matches = self.matcher.match(wrapper)

        pseudos = {}
        if matches:
            # matches.sort()
            for match in matches:
                specificity, order, pseudo, payload = match
                sel_str, data = payload
                props = {**props, **data}
                if sel_str in self.pseudo_map:
                    pseudos = self.pseudo_map[sel_str]

        normal_hash = md5(props)
        if normal_hash not in self.styles:
            self.styles[normal_hash] = props

        focus_hash = None
        if "focus" in pseudos:
            hash = md5(pseudos["focus"])
            if hash not in self.styles:
                self.styles[hash] = {**DEFAULT_PROPS.copy(), **pseudos["focus"]}

        # TODO: need to parse any more pseudos?
        # for name, props in pseudos.items():
        #     hash = md5(props)
        #     if hash not in self.styles:
        #         self.styles[hash] = props
        #
        element = wrapper.etree_element
        tag = element.tag
        kwargs = {**element.attrib}
        kwargs.pop("class", "")
        kwargs.pop("id", "")
        height = kwargs.pop("height", None)
        weight = kwargs.pop("weight", None)

        if len(element.getchildren()) > 0:
            widget = WIDGET_MAP[tag](
                element, [self.parse_element(child) for child in wrapper], **kwargs
            )
        elif tag in WIDGET_MAP:
            widget = WIDGET_MAP[tag](element, **kwargs)
        else:
            widget = urwid.Text(f"Unknown tag: {tag}")

        # TODO: parse values like height:
        if isinstance(height, str) and height.isdigit():
            return (int(height), urwid.AttrMap(widget, normal_hash, focus_hash))
        elif isinstance(weight, str) and weight.isdigit():
            return (
                "weight",
                int(weight),
                urwid.AttrMap(widget, normal_hash, focus_hash),
            )

        return urwid.AttrMap(widget, normal_hash, focus_hash)


if __name__ == "__main__":
    layout = Layout("test/layout.xml", "test/styles.css")
    pprint(layout.palettes)
    mainloop = urwid.MainLoop(layout.root, palette=layout.palettes)
    mainloop.run()
