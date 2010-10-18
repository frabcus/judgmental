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



class BtoJ(Massager):

    def rules(self):
        l = [EmptyParagraphsToBreaks()]
        
        return l

    def template(self):
        return html.parse(self.template_filename())
        
    def template_filename(self):
        return "template.html"
                        
    def restructure(self,page):

        def change(a,b):
            x = t.find(a)
            y = page.find(b)
            self.massage(y)
            x.getparent().replace(x,y)

        t = self.template()
        r = t.getroot()

        # title
        change("//title","//title")

        # the bulk of the text
        change('//div[@class="opinion"]','//opinion')

        # the court name
        change('//div[@id="content"]/h1','//td[@align="left"]/h1')

        return t
