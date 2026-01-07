from pathlib import Path

import cssselect2
import tinycss2
from tinycss2.ast import (
    Declaration,
    FunctionBlock,
    HashToken,
    IdentToken,
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


def parse_stylesheet(
    path: Path, variables: dict[str, str] = {}
) -> tuple[list[tuple], dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find stylesheet: {path.absolute()} does not exist"
        )
    elif not path.is_file():
        raise IsADirectoryError(
            f"Could not find stylesheet: {path.absolute()} is a directory"
        )

    rules: list[Node] = tinycss2.parse_stylesheet(
        path.read_text(),
        skip_comments=True,
        skip_whitespace=True,
    )
    result_selectors = []
    pseudo_map = {}
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

            if not sel_str:
                continue

            for item in compiled:
                result_selectors.append((item, (sel_str, props)))

            for pseudo in pseudos:
                if sel_str not in pseudo_map:
                    pseudo_map[sel_str] = {}
                pseudo_map[sel_str][pseudo] = props

    return result_selectors, pseudo_map
