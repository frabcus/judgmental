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

        t = self.template()

        def extract(a):
            y = page.find(a)
            self.massage(y)
            return y

        def substitute(a,y):
            x = t.find(a)
            x.getparent().replace(x,y)

        title = extract("//title")
        court_name = extract('//td[@align="left"]/h1')
        bailii_url = extract('//small/i').text
        citation = [x for x in page.findall('//small/br') if x.tail[:7]=="Cite as"][0].tail
        date = extract('//p[@align="RIGHT"]').text
        parties = " ".join(x.text for x in page.findall('//td[@align="center"]'))

        substitute("//title",title)

        substitute('//div[@class="opinion"]',extract('//opinion'))

        substitute('//div[@id="content"]/h1',court_name)

        t.find('//div[@class="meta"]').text = citation
        t.find('//div[@class="date"]').text = date
        t.find('//div[@class="parties"]').text = parties

        return t
