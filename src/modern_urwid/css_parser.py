from pathlib import Path

import cssselect2
import tinycss2
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


class CSSParser:
    def __init__(self, path: Path | None):
        self.matcher = cssselect2.Matcher()

        if path is None:
            return

        if not path.exists():
            raise FileNotFoundError(f"Could not find stylesheet: {path} does not exist")
        elif not path.is_file():
            raise IsADirectoryError(f"Could not find stylesheet: {path} is a directory")

        self.path = path
        self.dir = path.parent

        css = path.read_text()
        rules: list[Node] = tinycss2.parse_stylesheet(
            css,
            skip_comments=True,
            skip_whitespace=True,
        )
        self.parse_rules(rules)

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

    def get_styles(self, default: dict[str, str], element: cssselect2.ElementWrapper):
        style = default.copy()
        pseudos = {}
        if matches := self.matcher.match(element):
            matches.sort()
            for match in matches:
                specificity, order, pseudo, payload = match
                sel_str, data = payload
                style.update(data)
                if sel_str in self.pseudo_map:
                    pseudos = self.pseudo_map[sel_str]
        return style, pseudos
