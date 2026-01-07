import inspect

import urwid

from modern_urwid.resource.dummies import UnresolvedResource, UnresolvedTemplate
from modern_urwid.resource.utils import wrap_callback

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

        kwargs = self.node.attrs.copy()
        kwargs.pop("class", None)
        kwargs.pop("id", None)

        for k, v in kwargs.items():
            if isinstance(v, UnresolvedResource):
                resource = self.resolve_resource(v)
                if callable(resource):
                    resource = wrap_callback(resource, self.node, self.context)
                kwargs[k] = resource
            elif isinstance(v, UnresolvedTemplate):
                kwargs[k] = self.resolve_template(v)

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
