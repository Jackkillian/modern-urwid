from __future__ import annotations

import inspect
from pathlib import Path

import cssselect2
import tinycss2
import urwid
from dict_hash import md5
from lxml import etree
from tinycss2.ast import Node

from .constants import DEFAULT_PROPS, RESOURCE_CHAR, XML_NS
from .exceptions import UnknownResource
from .parser import get_props, pop_pseudos_from_tokens, split_tokens_by_comma
from .wrapper import FilteredWrapper


def find_urwid_class(tag: str):
    tag = tag.lower()
    for name, cls in inspect.getmembers(urwid, inspect.isclass):
        if name.lower() == tag:
            return cls
    return None


def create_text_widget(cls, el, **kw):
    if el.text and el.text.strip():
        return cls(
            el.text, **kw
        )  # can't do .strip because it'll  remove the space if doing something like 'Name: '
    else:
        return cls(**kw)


class LayoutResources:
    """
    A base class for extending a layout's functionality
    """

    def __init__(self, layout: Layout, widgets=[], palettes=[]):
        self.layout = layout
        self.widgets = widgets
        self.palettes = palettes

    def get_widgets(self):
        return self.widgets

    def get_palettes(self):
        return self.palettes


class Layout:
    def __init__(
        self,
        xml_path: str | Path,
        css_path: str | Path,
        resources_cls=LayoutResources,
    ) -> None:
        self.resources = resources_cls(self)
        self.custom_widgets = self.resources.get_widgets()
        self.palettes = self.resources.get_palettes()
        self.widget_map = {}
        self.styles = {}
        self.matcher = cssselect2.Matcher()

        xml = open(xml_path).read()
        css = open(css_path).read()
        rules: list[Node] = tinycss2.parse_stylesheet(
            css,
            skip_comments=True,
            skip_whitespace=True,
        )
        self.parse_rules(rules)

        root = self.parse_element(
            FilteredWrapper.from_html_root(etree.fromstring(xml)),
            DEFAULT_PROPS,
        )
        if not isinstance(root, urwid.Widget):
            raise ValueError(f"Got {root} instead of Widget for root")
        else:
            self.root = root

        for hash, style in self.styles.items():
            self.palettes.append((hash, *style.values()))

    def get_root(self):
        return self.root

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

    def parse_attrs(self, kwargs: dict):
        result = {}
        for k, v in kwargs.items():
            if isinstance(v, str):
                if v.isdigit():
                    result[k] = int(v)
                elif v.startswith(RESOURCE_CHAR):
                    result[k] = self.get_resource(v[len(RESOURCE_CHAR) :])
                elif v == "False":
                    result[k] = False
                elif v == "True":
                    result[k] = True
                else:
                    result[k] = v
        return result

    def get_resource(self, attr):
        if hasattr(self.resources, attr):
            return getattr(self.resources, attr)
        else:
            raise UnknownResource(f"Could not custom resource '@{attr}'")

    def parse_element(
        self,
        wrapper: FilteredWrapper,
        root_palette: dict,
        child_class: str | None = None,
    ):
        if child_class is not None:
            wrapper.classes |= {child_class}

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
            focus_hash = md5(pseudos["focus"])
            if focus_hash not in self.styles:
                self.styles[focus_hash] = {**props.copy(), **pseudos["focus"]}

        # TODO: need to parse any more pseudos?
        # for name, props in pseudos.items():
        #     hash = md5(props)
        #     if hash not in self.styles:
        #         self.styles[hash] = props
        #
        element = wrapper.etree_element
        tag = element.tag
        kwargs = self.parse_attrs(element.attrib)

        clazz = kwargs.pop("class", None)
        id = kwargs.pop("id", None)
        child_class = kwargs.pop(f"{XML_NS}child_class", None)
        height = kwargs.pop(f"{XML_NS}height", None)
        weight = kwargs.pop(f"{XML_NS}weight", None)

        signals = {}
        children = []
        for child in element.getchildren():
            if child.tag == f"{XML_NS}signal":
                signal_name = child.get("name")
                signals[signal_name] = self.parse_attrs(child.attrib)
            else:
                children.append(child)

        constructor = self.get_widget_constructor(tag)
        if constructor is None:
            return urwid.Filler(urwid.Text(f"Unknown tag: {tag}"))
        elif children:
            widget = constructor(
                element,
                [self.parse_element(child, props, child_class) for child in wrapper],
                **kwargs,
            )
        else:
            widget = constructor(element, **kwargs)

        if id is not None:
            if id in self.widget_map:
                raise ValueError(f"Cannot duplicate IDs: {id}")
            else:
                self.widget_map[id] = widget

        for name, attrs in signals.items():
            urwid.connect_signal(
                widget, name, attrs.get("callback"), attrs.get("user_arg")
            )

        if height is not None:
            return (height, urwid.AttrMap(widget, normal_hash, focus_hash))
        elif weight is not None:
            return (
                "weight",
                weight,
                urwid.AttrMap(widget, normal_hash, focus_hash),
            )

        return urwid.AttrMap(widget, normal_hash, focus_hash)

    def get_widget_constructor(self, tag):
        cls_lower = tag.lower()
        for cls in self.custom_widgets:
            if cls_lower == cls.__name__.lower():
                return lambda el, **kw: cls(**kw)
        cls = find_urwid_class(tag)
        if cls is None:
            return None
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
            return None

    def get_widget_by_id(self, id) -> urwid.Widget | None:
        return self.widget_map.get(id)
