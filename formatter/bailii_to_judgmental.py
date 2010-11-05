"""
Converts a document from the Bailii archive into nicer more formulaic HTML.
"""

# To do:
#  - improve recognition of metadata, especially parties and judges
#  - recognise paragraphs (possibly separately for each opinion shape)
#  - stash metadata for indexer
#  - recognise things that should be ordered lists
#  - are there any other massive unclosed tag configurations other than <li><a> ?



from lxml import html, etree
import re
import os

# a slightly modified version of UnicodeDammit from BeautifulSoup
from dammit import UnicodeDammit

# the debian package "python-dateutil" provides this
from dateutil.parser import parse as dateparse

from massager import *
from judgment import *



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
                element.replace(e, etree.Element("br"))
                done_something = True
        for e in element.findall("blockquote"):
            if e.getchildren() == [] and (e.text or "").strip() == "":
                element.replace(e, etree.Element("br"))
                done_something = True
        if done_something:
            return element
        else:
            return None



class SymbolClean(Rule):
    "Makes special symbols more consistent, for example by replacing curved quotes with plain ones"

    def transform(self, element):
        symbolmap = [(u"\x97", u"\u2014"), # bad em-dash to good em-dash
                     (u"\xa0", " "), # nb space to normal space
                     (u"\u2019", "'"), # curved apostrophe to normal apostrophe
                     (u"\u201c", '"'), # left curved quotes to normal quotes
                     (u"\u201d", '"') # right curved quotes to normal quotes
                     ]
        
        done_something = False
        for (old, new) in symbolmap:
            if old in (element.text or ""):
                element.text = element.text.replace(old, new)
                done_something = True
            if old in (element.tail or ""):
                element.tail = element.tail.replace(old, new)
                done_something = True
        if done_something:
            return element
        else:
            return None



class CorrectTypos(Rule):
    "Corrects some typographical errors found in the text"

    def transform(self,element):
        typos = [("Decisons","Decisions"),
                 ("Novenber","November"),
                 ("Feburary","February"),
                 ("Jully","July"),
                 (u"31\xA0September","30 September")
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

    def preprocess(self,inf):
        "Sort out encoding problems, discard everything up to the first '<' (eg. the BOM) and do CRLF -> LF"
        data = inf.read()
        u = UnicodeDammit(data, smartQuotesTo=None, isHTML=True).unicode
        if u is None:
            raise StandardConversionError('badly encoded file - invalid bytes need to be patched first')
        a = u.encode('ascii', 'xmlcharrefreplace')
        start = a.find('<')
        if start == -1:
            raise StandardConversionError("no HTML present")
        page = a[start:].replace('\r\n','\n').replace('\r','\n') # hmmmmmmm?!
        return StringIO(page)

    def rules(self):
        l = [SymbolClean(),
             EmptyParagraphsToBreaks(),
             CorrectTypos(),
             UndoNestedTitles(),
             MendUnclosedTags()]
        
        return l

    def template(self):
        return etree.parse(self.template_filename())
        
    def template_filename(self):
        return "template.html"
                        
    def read_and_restructure(self,inlocation,outlocation):
        j = self.make_judgment(inlocation)

        outfile = open(outlocation,'w')
        j.write_html(outfile)
        outfile.close()
        return j
        
    def make_judgment(self,inlocation):
        infile = open(inlocation,'r')
        midfile = self.preprocess(infile)
        page = html.parse(midfile)

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
            title = extract("//title")
            title_text = (title.text or "").strip()
        except CantFindElement:
            raise StandardConversionError("skeleton page, with no title")
        if title_text == "Cisco Systems Inc. Web Authentication Redirect":
            raise StandardConversionError("redirection page")

        court_name_h1 = extract('//td[@align="left"]/h1')
        court_name = (court_name_h1.text or "").strip()
        if court_name == "Not found":
            raise StandardConversionError("empty 'Not Found' page")
        
        try:
            converter = extract('head/meta[@name="Converter"]').attrib["content"]
            conv_no = int("".join(c for c in converter if c.isdigit()) or "0")
        except CantFindElement:
            converter = "None supplied"
            conv_no = 0

        def find_date():

            # parenthesised search object
            r = re.compile("\\(([^()]*)($|\\))")

            def scan(s):
                for raw_date in r.finditer(remove_nb_space(s or "")):
                    attempt(raw_date.groups()[0].strip())

            def attempt(s):
                try:
                    raise GotIt(dateparse(s))
                except (ValueError, TypeError):
                    pass

            def remove_nb_space(s):
                try:
                    return s.replace(u"\xA0"," ")
                except UnicodeDecodeError:
                    return s            

            try:
                # find it in parentheses in the title tag
                scan(title_text)

                # find it in parentheses in a meta title tag
                metatitle = page.find('head/meta[@name="Title"]')
                if metatitle is not None:
                    scan(metatitle.text) ### do I mean the content of that tag?

                # try finding it at the end of the title tag in a more desperate fashion
                raw_date = re.compile("([0-9]* [A-Za-z]* [0-9]*)[^0-9]*$").search(title_text)
                if raw_date:
                    attempt(raw_date.groups()[0])

                # try finding it in subtags of the title tag
                for t in title.iterdescendants():
                    scan(t.text)
                    scan(t.tail)

                # try finding it in the first paragraph of the opinion
                # if this works there's some metadata there
                for t in page.findall("//font"):
                    scan(t.text)

                # try finding it near a link:
                for t in page.findall('//a[@title="Link to BAILII version"]'):
                    scan(t.tail)

                # try in a bold tag (getting desperate now)
                for t in page.findall('//b'):
                    attempt(t.text or "")

                # try finding a "notified: DATE"
                for t in page.findall('//p'):
                    raw_date = re.compile("notified: (.*)$").search(t.text or "")
                    if raw_date:
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
            title_cite = re.compile("^(.*)\\([^(]*$").match(title_text)
            if title_cite is not None:
                return title_cite.groups()[0].strip()
            
            raise CantFindCitation()

        citation = find_citation()

        def find_opinion():
            body = page.find("body")
            hrc = len(body.findall("hr"))
            c = 0
            for x in body.getchildren():
                if x.tag == "hr":
                    if not (0 < c < hrc - 1):
                        x.drop_tree()
                    c += 1
                else:
                    if not (0 < c < hrc):
                        x.drop_tree()
            return body

        opinion = find_opinion()
        opinion = self.massage(opinion)
        substitute('//div[@class="opinion"]/p',opinion)

        substitute("//title",title)

        substitute('//div[@id="content"]/h1',court_name_h1)

        t.find('//a[@id="bc-courtname"]').text = court_name
        t.find('//span[@id="meta-citation"]').text = citation
        t.find('//div[@id="meta-date"]').text = date_str
        t.find('//span[@id="bc-description"]').text = title_text

        return Judgment(xhtml=t,
                        infilename=os.path.basename(inlocation),
                        title=title_text,
                        date=date,
                        citations=citation,
                        courtname=court_name,
                        bailii_url=bailii_url)
