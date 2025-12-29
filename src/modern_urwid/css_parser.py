from pathlib import Path
from re import L

import cssselect2
import tinycss2
from tinycss2.ast import (
    Declaration,
    FunctionBlock,
    HashToken,
    IdentToken,
    LiteralToken,
    Node,
    WhitespaceToken,
)


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


def get_props(tokens, variables):
    modified = [
        IdentToken(-1, -1, variables.get(token.arguments[0].value))
        if isinstance(token, FunctionBlock)
        else token
        for token in tokens
    ]
    decls: list[Declaration] = tinycss2.parse_declaration_list(
        modified, skip_comments=True, skip_whitespace=True
    )
    return {
        decl.name: "".join(
            [
                "#" + token.value if isinstance(token, HashToken) else token.value
                for token in decl.value
                if hasattr(token, "value")
            ]
        ).strip()
        for decl in decls
        if not decl.name.startswith("--")
    }


def get_tokens_value(tokens: list[Node]) -> str:
    value = ""
    for token in tokens:
        value += token.serialize()
    return value


def split_decl(tokens):
    result = []
    name = []
    value = []
    in_name = True
    for token in tokens:
        if token.type == "literal":
            if token.value == ":":
                in_name = False
            elif token.value == ";":
                in_name = True
                result.append((name.copy(), value.copy()))
                name.clear()
                value.clear()
        elif in_name and not token.type == "whitespace":
            name.append(token)
        elif not in_name:
            value.append(token)
    return result


class CSSParser:
    def __init__(self, path: Path | None, variables_override: dict[str, str] = {}):
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
        self.parse_rules(rules, variables_override)

    def parse_rules(self, rules, variables={}):
        self.pseudo_map = {}
        for rule in rules:
            if rule.type != "qualified-rule":
                continue

            for name, value in split_decl(rule.content):
                name = get_tokens_value(name)
                value = get_tokens_value(value).strip()
                if name.startswith("--"):
                    if name not in variables:
                        variables[name] = value

            element_selectors: list[list[Node]] = split_tokens_by_comma(rule.prelude)
            props = get_props(rule.content, variables)
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

                # Default to 8-bit colors if true colors are not defined
                if "color-adv" not in data:
                    style["color-adv"] = style["color"]

                if "background-adv" not in data:
                    style["background-adv"] = style["background"]

                if sel_str in self.pseudo_map:
                    pseudos = self.pseudo_map[sel_str]

        return style, pseudos

    def get_styles_by_attr(self, default, classes=[], id=None):
        style = default.copy()
        pseudos = {}
        if matches := self.match(classes, id):
            matches.sort()
            for match in matches:
                specificity, order, pseudo, payload = match
                sel_str, data = payload
                style.update(data)
                if sel_str in self.pseudo_map:
                    pseudos = self.pseudo_map[sel_str]
        return style, pseudos

    def match(self, classes=[], id: str | None = None):
        relevant_selectors = []

        if id is not None and id in self.matcher.id_selectors:
            for test, specificity, order, pseudo, payload in self.matcher.id_selectors[
                id
            ]:
                relevant_selectors.append((specificity, order, pseudo, payload))

        for class_name in classes:
            if class_name in self.matcher.class_selectors:
                for (
                    test,
                    specificity,
                    order,
                    pseudo,
                    payload,
                ) in self.matcher.class_selectors[class_name]:
                    relevant_selectors.append((specificity, order, pseudo, payload))

        relevant_selectors.sort()
        return relevant_selectors
