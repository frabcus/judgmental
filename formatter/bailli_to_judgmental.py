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


class CorrectTypos(Rule):
    "Corrects some typographical errors found in the text"

    def transform(self,element):
        typos = [("Decisons","Decisions")]
        
        done_something = False
        for (old,new) in typos:
            if old in (element.text or ""):
                element.text = element.text.replace(old,new)
                done_something = True
            if old in (element.tail or ""):
                element.tail = element.tail.replace(old,new)
                done_something = True
        return done_something
        



class BtoJ(Massager):

    def rules(self):
        l = [EmptyParagraphsToBreaks(),
             CorrectTypos()]
        
        return l

    def template(self):
        return html.parse(self.template_filename())
        
    def template_filename(self):
        return "template.html"
                        
    def restructure(self,page):

        t = self.template()

        def extract(a):
            return self.massage(page.find(a))

        def substitute(a,y):
            x = t.find(a)
            x.getparent().replace(x,y)

        title = extract("//title")
        court_name_h1 = extract('//td[@align="left"]/h1')
        court_name = court_name_h1.text
        bailii_url = extract('//small/i').text
        citation = [self.massage(x) for x in page.findall('//small/br') if x.tail[:7]=="Cite as"][0].tail
        date = extract('//p[@align="RIGHT"]').text
        parties = " ".join(self.massage(x).text for x in page.findall('//td[@align="center"]'))

        substitute("//title",title)

        substitute('//div[@class="opinion"]',extract('//opinion'))

        substitute('//div[@id="content"]/h1',court_name_h1)

        t.find('//a[@class="court"]').text = court_name
        t.find('//div[@class="meta"]').text = citation
        t.find('//div[@class="date"]').text = date
        t.find('//div[@class="parties"]').text = parties

        return t
