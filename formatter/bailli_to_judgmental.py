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

    def template(self):
        return html.parse(self.template_filename())
        
    def template_filename(self):
        return "template.html"
                        
    def restructure(self,page):

        def change(a,b):
            x = t.find(a)
            x.getparent().replace(t.find(a),page.find(b))

        t = self.template()
        r = t.getroot()

        change("//title","//title")
        change('//div[@id="content"]/h1','//td[@align="left"]/h1')
        change('//div[@class="opinion"]','//div[@class="opinion"]')

        return t
