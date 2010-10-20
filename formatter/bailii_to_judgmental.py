"""
Converts the Bailii archive into nicer more formulaic HTML.
"""

from massager import *
from lxml.etree import Element,XML

# the debian package "python-dateutil" is useful
from dateutil.parser import parse as dateparse

import re


class EmptyParagraphsToBreaks(Rule):
    "<p /> --> <br />"
    "<blockquote /> --> <br />"
    
    def transform(self,element):
        done_something = False
        for e in element.findall("p"):
            if e.getchildren() == [] and (e.text or "").strip() == "":
                element.replace(e, Element("br"))
                done_something = True
        for e in element.findall("blockquote"):
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

        converter = extract('head/meta[@name="Converter"]').attrib["content"]

        title = extract("//title")
        court_name_h1 = extract('//td[@align="left"]/h1')
        court_name = court_name_h1.text
        bailii_url = extract('//small/i').text

        citation = [self.massage(x) for x in page.findall('//small/br') if x.tail[:7]=="Cite as"][0].tail
        if citation[:7]=="Cite as":
            citation = citation[7:].strip(":").strip()

        if converter == "\\converter JU convhtm149":
            raw_date = re.compile("\\((.*)\\)").search(page.find("head/title").text).groups()[0]
        else:
            raw_date = extract('//p[@align="RIGHT"]').text        

        # structured date
        date = dateparse(raw_date)

        # preferred string representation of date
        date_str = date.strftime("%d %B %Y")
        
        parties = " ".join(self.massage(x).text for x in page.findall('//td[@align="center"]'))
        description = "%s [%s]"%(parties,date.year)

        substitute("//title",title)

        substitute('//div[@class="opinion"]',extract('//opinion'))

        substitute('//div[@id="content"]/h1',court_name_h1)

        t.find('//a[@id="bc-courtname"]').text = court_name
        t.find('//span[@id="meta-citation"]').text = citation
        t.find('//div[@id="meta-date"]').text = date_str
        t.find('//div[@id="subtitle-parties"]').text = parties
        t.find('//span[@id="bc-description"]').text = description

        return t
