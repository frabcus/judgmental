"""
Converts the Bailii archive into nicer more formulaic HTML.
"""

# To do:
#  - improve recognition and handling of metadata
#  - recognise things that should be ordered lists
#  - normalise character encodings




from lxml.etree import Element,XML
import re

# the debian package "python-dateutil" is useful
from dateutil.parser import parse as dateparse

from massager import *



class CantFindElement(Exception):
    def __init__(self,searchstring):
        self.searchstring = searchstring
    def __str__(self):
        return "Can't find '%s'"%self.searchstring



class CantFindDate(Exception):
    def __str__(self):
        return "Can't find a date (probably because I'm unattractive)"



class CantFindCitation(Exception):
    def __str__(self):
        return "Can't find a citation. Sucks to be us."



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



class UndoNestedTitles(Rule):
    "At least one page has nested <title> tags. This deals with that."

    def transform(self,element):
        if element.tag != "title":
            return False
        if element.find("title") is not None:
            element.drop_tag()
            return True
        else:
            return False
        


class BtoJ(Massager):

    def preprocess(self,inf,outf):
        "Discard everything up to the first '<'."
        for l in inf:
            if "<" in l:
                outf.write(l[l.index("<"):])
                break
        for l in inf:
            outf.write(l)

    def rules(self):
        l = [EmptyParagraphsToBreaks(),
             CorrectTypos(),
             UndoNestedTitles()]
        
        return l

    def template(self):
        return html.parse(self.template_filename())
        
    def template_filename(self):
        return "template.html"
                        
    def restructure(self,page):

        t = self.template()

        def extract(a):
            x = page.find(a)
            if x is None:
                raise CantFindElement(a)
            return self.massage(x)

        def substitute(a,y):
            x = t.find(a)
            x.getparent().replace(x,y)

        def report(s):
            print "     %s"%s

        try:
            converter = extract('head/meta[@name="Converter"]').attrib["content"]
            conv_no = int("".join(c for c in converter if c.isdigit()))
        except CantFindElement:
            converter = "None supplied"
            conv_no = 0

        title = extract("//title")
        title_text = title.text
        
        court_name_h1 = extract('//td[@align="left"]/h1')
        court_name = court_name_h1.text

        def remove_nb_space(s):
            s = s or ""
            try:
                return s.replace(u"\xA0"," ")
            except UnicodeDecodeError:
                return s

        def find_date():

            # parenthesised search object
            r = re.compile("\\(([^()]*)\\)")

            # find it in parentheses in the title tag
            for raw_date in r.finditer(remove_nb_space(page.find("head/title").text)):
                s = raw_date.groups()[0]
                try:
                    return dateparse(s)
                except ValueError:
                    pass

            report("no date in title: %s"%(page.find("head/title").text))

            # find it in parentheses in a meta title tag
            metatitle = page.find('head/meta[@name="Title"]')
            if metatitle is not None:
                for raw_date in r.finditer(remove_nb_space(metatitle.attrib["content"])):
                    s = raw_date.groups()[0]
                    try:
                        return dateparse(s)
                    except ValueError:
                        pass

            raise CantFindDate()

        date = find_date()

        # preferred string representation of date
        date_str = date.strftime("%d %B %Y")

        ### should get this by other means?
        bailii_url = extract('//small/i').text

        def find_citation():

            # try looking for a "Cite as:"
            for x in page.findall('//small/br'):
                if x.tail[:8]=="Cite as:":
                    return x.tail[8:].strip()

            # does the title have the from "citation (date)"
            title_cite = re.compile("^(.*)\\(.*\\)$").match(title_text)
            if title_cite is not None:
                return title_cite.groups()[0].strip()
            
            raise CantFindCitation()

        citation = find_citation()

        opinion_as_ol = page.find("body/ol")
        opinion_as_opinion = page.find("//opinion")
        
        if opinion_as_ol is not None:

            if conv_no not in [149,151,152,153,155,157]:
                report("New <ol> converter: %d"%conv_no)
 
            party_line = opinion_as_ol.find("blockquote/i")
            if party_line is not None:
                app_resp = re.compile("Appellant:(.*)Respondent:(.*)").match(party_line.text or "")
                if app_resp is not None:
                    parties = " v. ".join(x.strip() for x in app_res.groups())
                else:
                    parties = ""
            else:
                parties = ""

            opinion_as_ol = self.massage(opinion_as_ol)
            substitute('//div[@class="opinion"]',extract('//ol'))

        elif opinion_as_opinion is not None:

            report("New <opinion> converter: %d"%conv_no)
            report(page.getpath(opinion_as_opinion))

            parties = " ".join(self.massage(x).text for x in page.findall('//td[@align="center"]'))
            opinion_as_opinion = self.massage(opinion_as_opinion)
            substitute('//div[@class="opinion"]',extract('//opinion'))

        else:
            # try the whole body, after any headmatter

            body = page.find("body")
            while body.getchildren()[0].tag != "p":
                body.getchildren()[0].drop_tree()
            parties = ""
            opinion = body.getchildren()[0]
            opinion = self.massage(opinion)
            substitute('//div[@class="opinion"]',opinion)
        
        # short name of case
        if parties!="":
            description = "%s [%s]"%(parties,date.year)
        else:
            # can we do better?
            description = citation

        substitute("//title",title)

        substitute('//div[@id="content"]/h1',court_name_h1)

        t.find('//a[@id="bc-courtname"]').text = court_name
        t.find('//span[@id="meta-citation"]').text = citation
        t.find('//div[@id="meta-date"]').text = date_str
        t.find('//div[@id="subtitle-parties"]').text = parties
        t.find('//span[@id="bc-description"]').text = description

        return t
