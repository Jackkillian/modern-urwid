import cssselect2

from .constants import XML_NS


class FilteredWrapper(cssselect2.ElementWrapper):
    def iter_mu_children(self):
        child = None
        for i, etree_child in enumerate(self.etree_children):
            if etree_child.tag.startswith(XML_NS):
                child = type(self)(
                    etree_child,
                    parent=self,
                    index=i,
                    previous=child,
                    in_html_document=self.in_html_document,
                )
                yield child

    def iter_children(self):
        child = None
        for i, etree_child in enumerate(self.etree_children):
            if not etree_child.tag.startswith(XML_NS):
                child = type(self)(
                    etree_child,
                    parent=self,
                    index=i,
                    previous=child,
                    in_html_document=self.in_html_document,
                )
                yield child
