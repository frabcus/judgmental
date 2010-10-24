"""
Converts the Bailii archive into nicer more formulaic HTML.
"""

# To do:
#  - improve recognition and handling of metadata
#  - recognise things that should be ordered lists
#  - normalise character encodings
#  - are there any other massive unclosed tag setups other than <li><a> ?




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



class GotIt(Exception):
    "This is a labour-saving device"
    def __init__(self,value):
        self.value = value



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
        if done_something:
            return element
        else:
            return None



class CorrectTypos(Rule):
    "Corrects some typographical errors found in the text"

    def transform(self,element):
        typos = [("Decisons","Decisions"),
                 ("Novenber","November")
                 ]
        
        done_something = False
        for (old,new) in typos:
            if old in (element.text or ""):
                element.text = element.text.replace(old,new)
                done_something = True
            if old in (element.tail or ""):
                element.tail = element.tail.replace(old,new)
                done_something = True
        if done_something:
            return element
        else:
            return None



class UndoNestedTitles(Rule):
    "At least one page has nested <title> tags. This deals with that."

    def transform(self,element):
        if element.tag != "title":
            return None
        t = element.find("title")
        if t is not None:
            element.drop_tag()
            return t
        else:
            return None



class MendUnclosedTags(Rule):
    "One page has some horrendous lists of <li><a>, all unclosed."

    def transform(self,element):
        done_something = False
        while True:
            culprit = element.find("li/a/li")
            if culprit is not None:
                done_something = True
                n = element.index(culprit.getparent().getparent())
                culprit.drop_tree()
                element.insert(n+1,culprit)
            elif done_something:
                return element
            else:
                return None
        


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
             UndoNestedTitles(),
             MendUnclosedTags()]
        
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
            conv_no = int("".join(c for c in converter if c.isdigit()) or "0")
        except CantFindElement:
            converter = "None supplied"
            conv_no = 0

        title = extract("//title")
        title_text = title.text or ""
        
        court_name_h1 = extract('//td[@align="left"]/h1')
        court_name = court_name_h1.text

        def remove_nb_space(s):
            try:
                return s.replace(u"\xA0"," ")
            except UnicodeDecodeError:
                return s

        def find_date():

            def attempt(s):
                try:
                    raise GotIt(dateparse(s))
                except (ValueError, TypeError):
                    pass

            # parenthesised search object
            r = re.compile("\\(([^()]*)($|\\))")

            try:
                # find it in parentheses in the title tag
                for raw_date in r.finditer(remove_nb_space(title_text)):
                    attempt(raw_date.groups()[0])

                # find it in parentheses in a meta title tag
                metatitle = page.find('head/meta[@name="Title"]')
                if metatitle is not None:
                    for raw_date in r.finditer(remove_nb_space(metatitle.attrib["content"])):
                        attempt(raw_date.groups()[0])

                # try finding it at the end of the title tag in a more desperate fashion
                raw_date = re.compile("([0-9]* [A-Za-z]* [0-9]*)[^0-9]*$").search(title_text)
                if raw_date:
                    attempt(raw_date.groups()[0])

                # try finding it in subtags of the title tag
                for t in title.iterdescendants():
                    for raw_date in r.finditer(remove_nb_space(t.text or "")):
                        attempt(raw_date.groups()[0])
                    for raw_date in r.finditer(remove_nb_space(t.tail or "")):
                        attempt(raw_date.groups()[0])

                # try finding it in the first paragraph of the opinion
                # if this works there's some metadata there
                for t in page.findall("//font"):
                    for raw_date in r.finditer(remove_nb_space(t.text)):
                        attempt(raw_date.groups()[0])

            except GotIt, g:
                return g.value
                
            raise CantFindDate()

        date = find_date()

        # preferred string representation of date
        # date.strftime("%d %B %Y") doesn't work for years < 1900
        months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
        date_str = "%d %s %d"%(date.day, months[date.month-1], date.year)

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
        opinion_as_opinion = page.find("body/doc/opinion")
        
        if opinion_as_ol is not None:

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
