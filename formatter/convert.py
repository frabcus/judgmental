"""
Reads file metadata from database and transforms files.
"""

from lxml import html, etree
import re
import os
import traceback

from cStringIO import StringIO
from prefixtree import *
from general import *
from dateutil.parser import parse as dateparse

legislation_tree = PrefixTree()


# must use a global variable to ensure it is visible throughout the process pool
with open("template.html",'r') as html_template_file:
    html_template_stringio = StringIO(html_template_file.read())


def convert(file_list, dbfile_name, logfile, public_html_dir, use_multiprocessing, do_legislation):

    print "-"*25
    print "Conversion..."

    if do_legislation:
        print "Making legislation prefix tree"
        with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
            create_tables_interactively(cursor,['lawreferences'],['CREATE TABLE lawreferences (lawreferenceid INTEGER PRIMARY KEY ASC, judgmentid INTEGER, legislationid INTEGER)'])
            legislation = sorted(make_unique(((unenumerate(violently_normalise(t)),(l,i)) for (t,l,i) in cursor.execute('SELECT title,link,legislationid FROM legislation')),lambda (x,_):x))
            legislation_tree.populate(legislation)
        print "Added %s names of legislation objects"%len(legislation)

    finished_count = Counter()

    def convert_report(basename):
        "Callback function; reports on success or failure"
        def closure(r):
            "Take True, new file name and a list of report strings, or False, None and a message"
            (s,newname,x) = r
            try:
                if s:
                    finished_count.inc()
                    if len(x)>0:
                        logfile.write("[convert success] " + basename + " -> " + newname + " (" + ", ".join(x) + ")" + "\n")
                    print "convert:%6d. %s"%(finished_count.count, basename + " -> " + newname)
                else:
                    raise StandardConversionError(x)
            except ConversionError, e:
                e.log("convert fail",basename,logfile)
        return closure

    print "Converting files"
    with ProcessManager(use_multiprocessing) as process_pool:
        print file_list
        for fullname in file_list:
            basename = os.path.basename(fullname)
            process_pool.apply_async(convert_file,(fullname,basename,dbfile_name,use_multiprocessing,public_html_dir,do_legislation),callback=convert_report(basename))

    broadcast(logfile,"Converted %d files successfully"%finished_count.count)



def convert_file(fullname,basename,dbfile_name,use_multiprocessing,public_html_dir,do_legislation):
    try:
        with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
            metadata = list(cursor.execute('SELECT judgmentid,title,date,courts.name,courts.abbreviated_name,courts.url,bailii_url,judgmental_url FROM judgments JOIN courts ON judgments.courtid=courts.courtid WHERE filename=?',(basename,)))
            try:
                (judgmentid,title,date,court_name,abbreviated_court,court_url,bailii_url,judgmental_url) = metadata[0]
            except IndexError:
                raise NoMetadata
            judgmentcitationcodes = list(x[0] for x in cursor.execute('SELECT citationcode FROM judgmentcodes JOIN citationcodes ON judgmentcodes.citationcodeid=citationcodes.citationcodeid WHERE judgmentid=?',(judgmentid,)))
            crossreferences_out = list(cursor.execute('SELECT citationcode, title, judgmental_url FROM crossreferences JOIN citationcodes ON crossreferences.citationcodeid=citationcodes.citationcodeid JOIN judgmentcodes ON crossreferences.citationcodeid = judgmentcodes.citationcodeid JOIN judgments ON judgmentcodes.judgmentid=judgments.judgmentid WHERE crossreferences.judgmentid=? ORDER BY judgments.date',(judgmentid,)))
            crossreferences_in = list(cursor.execute('SELECT title,judgmental_url FROM crossreferences JOIN judgments ON crossreferences.judgmentid=judgments.judgmentid JOIN judgmentcodes ON crossreferences.citationcodeid=judgmentcodes.citationcodeid WHERE judgmentcodes.judgmentid=? ORDER BY judgments.date',(judgmentid,)))

        pagetext = open_bailii_html(fullname)

        if do_legislation:
            legislation_links = []
            def leglink(t,(l,i)):
                legislation_links.append((judgmentid,i))
                return '<a href="%s">%s</a>'%(l,t)
            newpagetext = StringIO()
            for (n,c) in legislation_tree.search_and_replace(compose_normalisers(violently_normalise,remove_html),leglink,iter(pagetext.read())):
                newpagetext.write(c.encode())
            newpagetext.reset()
            pagetext = newpagetext

        page = html.parse(pagetext)
        opinion = find_opinion(page)

        template = html.parse(html_template_stringio)

        report = []

        # we call these for side-effects
        if mend_unclosed_tags(opinion):
            report.append("mend_unclosed_tags")
        if empty_paragraphs_to_breaks(opinion):
            report.append("empty_paragraphs_to_breaks")

        missing_opinion = template.find('//div[@class="opinion"]/p')
        missing_opinion.getparent().replace(missing_opinion,opinion)

        template.find('//title').text = title
        template.find('//div[@id="meta-date"]').text = date
        template.find('//span[@id="meta-citation"]').text = ", ".join(judgmentcitationcodes)
        template.find('//div[@id="content"]/h1').text = court_name
        template.find('//a[@id="bc-courtname"]').text = court_name
        template.find('//a[@id="bc-courtname"]').set('href',court_url)
        template.find('//span[@id="bc-description"]').text = title

        # add links to crossreferences, or delete the templates for them
        if len(crossreferences_in)==0 and len(crossreferences_out)==0:
            template.find('//div[@id="crossreferences"]').drop_tree()
        else:
            if len(crossreferences_in)==0:
                template.find('//span[@id="crossreferences-in"]').drop_tree()
            else:
                l_in = template.find('//ul[@id="crossreferences-in-list"]')
                for (t,f) in crossreferences_in:
                    li = etree.Element("li")
                    a = etree.Element("a")
                    a.text = t
                    a.attrib["href"] = f
                    li.append(a)
                    l_in.append(li)
            if len(crossreferences_out)==0:
                template.find('//span[@id="crossreferences-out"]').drop_tree()
            else:
                l_out = template.find('//ul[@id="crossreferences-out-list"]')
                for (t,_,f) in crossreferences_out:
                    li = etree.Element("li")
                    a = etree.Element("a")
                    a.text = t
                    a.attrib["href"] = f
                    li.append(a)
                    l_out.append(li)

        path = os.path.join(public_html_dir, judgmental_url.lstrip('/'))
                
        # Write out the judgment
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
        	os.makedirs(dirname)
        outfile = open(path,'w')
        outfile.write(etree.tostring(template, pretty_print=True))

        if do_legislation and legislation_links:
            with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
                for (j,i) in legislation_links:
                    cursor.execute('INSERT INTO lawreferences(judgmentid,legislationid) VALUES (?,?)',(j,i))

        return (True, judgmental_url, report)
    except ConversionError,e:
        return (False, None, e.message)
    except Exception, e:
        try:
            message = traceback.format_exc()
        except:
            message = "unknown exception"
        return (False, None, message)


def find_opinion(page):
    body = page.find("//body")
    if body is None:
        raise StandardConversionError("no body tag")
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



def mend_unclosed_tags(opinion):
    "One page has some horrendous lists of <li><a>, all unclosed."
    been_used = False
    culprit = opinion.find(".//li/a/li")
    while culprit is not None:
        been_used = True
        grandfather = culprit.getparent().getparent()
        greatgrandfather = grandfather.getparent()
        n = greatgrandfather.index(grandfather)
        culprit.drop_tree()
        greatgrandfather.insert(n+1,culprit)
        culprit = opinion.find(".//li/a/li")
    return been_used


def empty_paragraphs_to_breaks(opinion):
    "<p /> --> <br />"
    "<blockquote /> --> <br />"
    been_used = False
    for e in opinion.findall(".//p"):
        if e.getchildren() == [] and (e.text or "").strip() == "":
            e.getparent().replace(e, etree.Element("br"))
            been_used = True
    for e in opinion.findall(".//blockquote"):
        if e.getchildren() == [] and (e.text or "").strip() == "":
            e.getparent().replace(e, etree.Element("br"))
            been_used = True
    return been_used




class CantFindElement(ConversionError):
    def __init__(self,searchstring):
        self.message = "can't find element \"%s\""%searchstring
