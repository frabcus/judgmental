"""
Reads file metadata from database and transforms files.
"""

from lxml import html, etree
import re
import os

from StringIO import StringIO

from general import *


# must use a global variable to ensure it is visible throughout the process pool
with open("template.html",'r') as html_template_file:
    html_template_stringio = StringIO(html_template_file.read())


def convert(file_list, dbfile_name, logfile, output_dir, use_multiprocessing):

    print "-"*25
    print "Conversion..."

    finished_count = Counter()

    def convert_report(basename):
        "Callback function; reports on success or failure"
        def closure(r):
            "Take True and a list of report strings, or false and a message"
            (s,x) = r
            try:
                if s:
                    finished_count.inc()
                    if len(x)>0:
                        logfile.write("[convert success] " + basename + " (" + ", ".join(x) + ")" + "\n")
                    print "convert:%6d. %s"%(finished_count.count, basename)
                else:
                    raise StandardConversionError(x)
            except ConversionError, e:
                e.log("convert fail",basename,logfile)
        return closure

    print "Converting files"
    with ProcessManager(use_multiprocessing) as process_pool:
        for fullname in file_list:
            basename = os.path.basename(fullname)
            process_pool.apply_async(convert_file,(fullname,basename,dbfile_name,use_multiprocessing,output_dir),callback=convert_report(basename))

    broadcast(logfile,"Converted %d files successfully"%finished_count.count)



def convert_file(fullname,basename,dbfile_name,use_multiprocessing,output_dir):
    try:
        with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
            metadata = list(cursor.execute('SELECT judgmentid,title,date,courts.name,bailii_url FROM judgments JOIN courts ON judgments.courtid=courts.courtid WHERE filename=?',(basename,)))
            try:
                (judgmentid,title,date,court_name,bailii_url) = metadata[0]
            except IndexError:
                raise NoMetadata
            citations = list(x[0] for x in cursor.execute('SELECT citation FROM citations WHERE judgmentid=?',(judgmentid,)))
            crossreferences_out = list(cursor.execute('SELECT citation, title, filename FROM crossreferences JOIN citations ON crossreferences.citationid=citations.citationid JOIN judgments on citations.judgmentid = judgments.judgmentid where crossreferences.judgmentid=?',(judgmentid,)))
            crossreferences_in = list(cursor.execute('SELECT title,filename FROM crossreferences JOIN citations ON crossreferences.citationid=citations.citationid JOIN judgments ON crossreferences.judgmentid=judgments.judgmentid where citations.judgmentid=?',(judgmentid,)))

        page = html.parse(open_bailii_html(fullname))
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
        template.find('//span[@id="meta-citation"]').text = ", ".join(citations)
        template.find('//div[@id="content"]/h1').text = court_name

        outfile = open(os.path.join(output_dir,basename),'w')
        outfile.write(etree.tostring(template, pretty_print=True))
        return (True,report)
    except ConversionError,e:
        return (False,e.message)


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
