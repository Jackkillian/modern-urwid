import inspect
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


XML_NS = "{https://www.jackkillian.com/mu/xml}"
DEFAULT_PROPS = {
    "color": "",
    "background": "",
    "monochrome": "",
    "color-adv": "",
    "background-adv": "",
}
WIDGET_MAP = {}


def find_urwid_class(tag: str):
    tag = tag.lower()
    for name, cls in inspect.getmembers(urwid, inspect.isclass):
        if name.lower() == tag:
            return cls
    return None


def create_text_widget(cls, el, **kw):
    if el.text:
        return cls(
            el.text, **kw
        )  # can't do .strip because it'll  remove the space if doing something like 'Name: '
    else:
        return cls(**kw)


def get_widget_constructor(tag):
    if tag in WIDGET_MAP:
        return WIDGET_MAP[tag]
        if isinstance(cls, (urwid.WidgetContainerMixin, urwid.WidgetDecoration)):
            return lambda el, children, **kw: WIDGET_MAP[tag](children, **kw)
        else:
            return lambda el, **kw: WIDGET_MAP[tag](
                el.text.strip() if el.text else "", **kw
            )
    cls = find_urwid_class(tag)
    if issubclass(
        cls,
        urwid.WidgetContainerMixin,
    ):
        return lambda el, children, **kw: cls(children, **kw)
    elif issubclass(
        cls,
        urwid.WidgetDecoration,
    ):
        return lambda el, children, **kw: cls(children[0], **kw)
    elif issubclass(cls, urwid.Widget):
        return lambda el, **kw: create_text_widget(cls, el, **kw)
    else:
        # TODO: parse custom widgets or just return None if none found
        return None


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
            cssselect2.ElementWrapper.from_html_root(etree.fromstring(xml)),
            DEFAULT_PROPS,
        )

        self.palettes = []
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

    def parse_element(self, wrapper: cssselect2.ElementWrapper, root_palette: dict):
        props = root_palette.copy()
        matches = self.matcher.match(wrapper)

        pseudos = {}
        if matches:
            matches.sort()
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

        for k, v in kwargs.items():
            if isinstance(v, str) and v.isdigit():
                kwargs[k] = int(v)

        # TODO: mu:child_class applies only to an element's children
        kwargs.pop("class", "")
        kwargs.pop("id", "")
        height = kwargs.pop(f"{XML_NS}height", None)
        weight = kwargs.pop(f"{XML_NS}weight", None)

        print(f"Parsing tag {tag}")

        constructor = get_widget_constructor(tag)
        if constructor is None:
            return urwid.Filler(urwid.Text(f"Unknown tag: {tag}"))
        elif len(element.getchildren()) > 0:
            print(f"Calling constructor for {tag}")
            widget = constructor(
                element,
                [self.parse_element(child, props) for child in wrapper],
                **kwargs,
            )
        else:
            widget = constructor(element, **kwargs)

        print(f"Got widget {widget}")

        # TODO: parse values like height:
        if height is not None:
            return (height, urwid.AttrMap(widget, normal_hash, focus_hash))
        elif weight is not None:
            return (
                "weight",
                weight,
                urwid.AttrMap(widget, normal_hash, focus_hash),
            )

        return urwid.AttrMap(widget, normal_hash, focus_hash)


# TODO: allow pregregistered variables, e.g. widgets, palettes, functions, etc

if __name__ == "__main__":
    layout = Layout("test/layout.xml", "test/styles.css")
    pprint(layout.palettes)
    mainloop = urwid.MainLoop(layout.root, palette=layout.palettes)
    mainloop.run()
