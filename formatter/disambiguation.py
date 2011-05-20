"""
Creates disambiguation pages for every ambiguous citation code
"""


from lxml import html, etree
import os
from cStringIO import StringIO

from general import *


with open("template_disambiguation.html",'r') as html_template_file:
    html_template_stringio = StringIO(html_template_file.read())


def disambiguation(file_list, dbfile_name, logfile, output_dir, use_multiprocessing):
    
    print "-"*25
    print "Disambiguation..."

    with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
        ambiguous_citationcodes = list(cursor.execute('SELECT citationcode, GROUP_CONCAT(judgmentid) FROM judgmentcodes JOIN citationcodes ON citationcodes.citationcodeid=judgmentcodes.citationcodeid GROUP BY judgmentcodes.citationcodeid HAVING COUNT (judgmentid)>1'))
    print "Found %d ambiguous codes"%len(ambiguous_citationcodes)

    finished_count = Counter()

    def disambiguate_report(code):
        "Callback function; reports on success or failure"
        def closure(r):
            "Takes True and a list of report strings, or False and a message"
            (s,x) = r
            try:
                if s:
                    finished_count.inc()
                    if len(x)>0:
                        logfile.write("[disambiguation] " + code + " (" + ", ".join(x) + ")" + "\n")
                    print "convert:%6d. %s"%(finished_count.count, code)
                else:
                    raise StandardConversionError(x)
            except ConversionError, e:
                e.log("disambiguate fail",code,logfile)
        return closure

    print "Creating disambiguation files"
    with ProcessManager(use_multiprocessing) as process_pool:
        for (c,s) in ambiguous_citationcodes:
            process_pool.apply_async(disambiguate,(c,s,output_dir,dbfile_name,use_multiprocessing),callback=disambiguate_report(c))


def disambiguate(code,judgmentids_string,output_dir,dbfile_name,use_multiprocessing):
    judgmentids = judgmentids_string.split(",")
    try:

        template = html.parse(html_template_stringio)
        template.find('//title').text = "Disambiguation: %s"%code
        template.find('//h1').text = "Disambiguation: %s"%code
        disambiguation_list = template.find('//ul')

        possibilities = []
        with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
            for j in judgmentids:
                cursor.execute('SELECT title, judgmental_url FROM judgments WHERE judgmentid = ? AND judgmental_url IS NOT NULL ORDER BY date DESC',(j,))
                result = cursor.fetchone()
                if result:
                    possibilities.append(result)

        if len(possibilities) == 0:
            raise StandardConversionError("no judgmental_urls found for citationcode")
        for (t,u) in possibilities:
            li = etree.Element("li")
            a = etree.Element("a")
            a.text = t
            a.attrib["href"] = u
            li.append(a)
            disambiguation_list.append(li)

        path = os.path.join(output_dir, disambiguation_filename(code))
        outfile = open(path,'w')
        outfile.write(etree.tostring(template,pretty_print=True))
        return (True,"")
    except ConversionError,e:
        return (False,e.message)
    except Exception,e:
        try:
            message = traceback.format_exc()
        except:
            message = "unknown exception"
        return (False, message)




