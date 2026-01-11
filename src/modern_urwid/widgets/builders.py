import inspect

import urwid

from .builder import WidgetBuilder


def find_urwid_class(tag: str):
    tag = tag.lower()
    for name, cls in inspect.getmembers(urwid, inspect.isclass):
        if name.lower() == tag:
            return cls
    return None


class GenericWidgetBuilder(WidgetBuilder):
    tag = "*"

    def build(self) -> urwid.Widget:
        if (cls := find_urwid_class(self.node.tag)) is None:
            return urwid.Filler(
                urwid.Text(f"Could not find widget {self.node.tag} in urwid")
            )
        kwargs = self.resolve_attrs()
        if issubclass(
            cls,
            urwid.WidgetContainerMixin,
        ):
            return cls([], **kwargs)
        elif cls is urwid.ScrollBar:
            return cls(urwid.ListBox([]))
        elif issubclass(
            cls,
            urwid.WidgetDecoration,
        ):
            return cls(urwid.Text("null"))
        elif issubclass(cls, urwid.Widget):
            if issubclass(cls, (urwid.Text, urwid.Button)):
                if self.node.text and self.node.text.strip():
                    return cls(self.node.text, **kwargs)
                else:
                    text = kwargs.pop("markup", "")
                    if not text:
                        text = kwargs.pop("label", "")
                    if not text:
                        text = kwargs.pop("caption", "")
                    return cls(text, **kwargs)
            else:
                return cls(**kwargs)
        else:
            return urwid.Filler(
                urwid.Text(f"Could not find widget {self.node.tag} in urwid")
            )

    def attach_children(self, widget, children):
        if hasattr(widget, "contents"):
            try:
                setattr(
                    widget,
                    "contents",
                    [
                        (child, widget.options(sizing.wh_type, sizing.wh_amount))
                        for child, sizing, _ in children
                    ],
                )
            except urwid.WidgetError:
                setattr(
                    widget,
                    "contents",
                    [(child, widget.options()) for child, _, _ in children],
                )
        elif hasattr(widget, "original_widget"):
            setattr(widget, "original_widget", children[0][0])
        else:
            raise ValueError(f"Could not set children for widget {widget}")


class ListBoxBuilder(WidgetBuilder):
    tag = "listbox"

    def build(self) -> urwid.ListBox:
        kwargs = {"body": urwid.SimpleFocusListWalker([])}
        kwargs.update(self.resolve_attrs())
        return urwid.ListBox(**kwargs)

    def attach_children(self, widget, children):
        widget.body.extend([child for child, sizing, _ in children])
