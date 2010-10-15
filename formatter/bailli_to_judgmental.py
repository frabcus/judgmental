from massager import *
from lxml.etree import Element,XML


class EmptyParagraphsToBreaks(Rule):
    "<p /> --> <br />"
    
    def transform(self,element):
        done_something = False
        for e in element.findall("p"):
            if e.getchildren() == [] and (e.text or "").strip() == "":
                element.replace(e, Element("br"))
                done_something = True
        return done_something



class ReplaceHomemadeTagsWithSpanOrDiv(Rule):

    def transform(self,element):

        t = element.tag

        to_span = ["judge"]
        to_div = ["opinion"]

        if t in to_span:
            element.tag = "span"
            element.attrib["class"] = t

            # This is too ad-hoc; only works right for "judge"
            for b in element.findall("b"):
                b.drop_tag() 

            return True

        elif t in to_div:
            element.tag = "div"
            element.attrib["class"] = t

            return True

        return False

    



class BtoJ(Massager):

    def rules(self):
        l = [EmptyParagraphsToBreaks(),
             ReplaceHomemadeTagsWithSpanOrDiv()]
        
        return l
        
    def post_process(self,element):

        # Add the CSS
        csstext = '<link rel="stylesheet" href="style.css" type="text/css" media="all" />'
        css = XML(csstext)
        element.find("head").insert(3,css)


