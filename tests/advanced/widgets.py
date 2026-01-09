import urwid

from modern_urwid import WidgetBuilder, parse_xml_layout


class CustomWidget2(WidgetBuilder):
    tag = "customwidgetfromxml"

    def build(self, **kwargs):
        return parse_xml_layout(
            self.context.resolve_path("widgets/widget.xml"),
            self.context,
        )[0]


class CustomButton(WidgetBuilder):
    tag = "custombutton"

    def build(self, *args, **kwargs):
        return urwid.Button(kwargs.get("label", "none"))
