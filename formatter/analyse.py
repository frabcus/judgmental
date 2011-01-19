"""
Extracts metadata from files and stores in a SQL database.
"""

try:
    import sqlite3 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

from dateutil.parser import parse as dateparse
from lxml import html, etree
import re
import os

from general import *



def analyse(file_list, dbfile_name, logfile, process_pool):

    print "-"*25
    print "Analysis..."
    print "Initialising SQLite database"
    conn = sqlite.connect(dbfile_name, check_same_thread = not(process_pool.genuinely_parallel))
    cursor = conn.cursor()
    try:
        create_tables(cursor)
    except sqlite.OperationalError:
        print "FATAL: The database already exists. You must remove it before running me again."
        quit()

    finished_count = Counter()

    def analyse_report(filename):
        "Callback function; reports on success or failure"
        def closure(r):
            "Takes True and a dict, or False and a message"
            (s,x) = r
            try:
                if s:
                    finished_count.inc()
                    print "analyse:%6d. %s"%(finished_count.count, os.path.basename(filename))
                    try:
                        write_metadata_to_sql(x,cursor)
                    except sqlite.IntegrityError, e:
                        raise StandardConversionError("sqlite.IntegrityError: %s"%str(e))
                else:
                    raise StandardConversionError(x)
            except ConversionError, e:
                e.log("analysis",os.path.basename(filename),logfile)
        return closure

    for filename in file_list:
        process_pool.apply_async(analyse_file,(filename,),callback=analyse_report(filename))

    # That's all, folks
    process_pool.close()
    process_pool.join()
    conn.commit()
    conn.close()
    broadcast(logfile,"Extracted metadata from %d files"%(finished_count.count))
        


def create_tables(cursor):
    "Create tables in an SQL database"
    cursor.execute('CREATE TABLE courts (courtid INTEGER PRIMARY KEY ASC, name TEXT UNIQUE)')
    cursor.execute('CREATE TABLE citations (citationid INTEGER PRIMARY KEY ASC, citation TEXT UNIQUE, judgmentid INTEGER)')
    cursor.execute('CREATE TABLE judgments (judgmentid INTEGER PRIMARY KEY ASC, title TEXT, date DATE, courtid INTEGER, filename TEXT UNIQUE, bailii_url TEXT UNIQUE)')



def write_metadata_to_sql(d,cursor):
    "Inserts judgment metadata to SQL database"

    # make sure there's a unique identifier for the court
    court_name = d["court_name"]
    cursor.execute('SELECT courtid FROM courts WHERE name = ?', (court_name,))
    result = cursor.fetchone()
    if result:
        courtid = result[0]
    else:
        cursor.execute('INSERT INTO courts(name) VALUES (?)', (court_name,))
        courtid = cursor.lastrowid

    # insert a record
    cursor.execute('INSERT INTO judgments(title, date, courtid, filename, bailii_url) VALUES (?, ?, ?, ?, ?)', (d["title"], d["date"], courtid, d["filename"], d["bailii_url"]))
    judgmentid = cursor.lastrowid

    # store the citations
    for i in set(i.strip() for i in d["citations"].split(',')):
        cursor.execute('INSERT INTO citations(citation, judgmentid) VALUES (?, ?)', (i,judgmentid))



def analyse_file(filename):
    try:
        page = html.parse(open_bailii_html(filename))

        metadata = {}
        metadata["filename"] = os.path.basename(filename)
        titletag = page.find("//title") 
        metadata["title"] = title = extract(page,"//title")
        metadata["bailii_url"] = extract(page,'//small/i') # should get this by other means?
        metadata["citations"] = find_citations(page,title)
        metadata["court_name"] = extract(page,'//td[@align="left"]/h1')
        metadata["date"] = find_date(page,titletag,title)
        return (True,metadata)
    except ConversionError, e:
        return (False,e.message)



class GotIt(Exception):
    "This is a labour-saving device"
    def __init__(self,value):
        self.value = value



def find_citations(page,title):

    # try looking for a "Cite as:"
    for x in page.findall('//small/br'):
        if x.tail[:8]=="Cite as:":
            return x.tail[8:].strip()

    # does the title have the from "citation (date)"
    title_cite = re.compile("^(.*)\\([^(]*$").match(title)
    if title_cite is not None:
        return title_cite.groups()[0].strip()

    raise CantFindCitation()



def find_date(page,titletag,titletext):
    "Epic function to find the date of the judgment"

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
        scan(titletext)

        # find it in parentheses in a meta title tag
        metatitle = page.find('head/meta[@name="Title"]')
        if metatitle is not None:
            scan(metatitle.text) ### do I mean the content of that tag?

        # try finding it at the end of the title tag in a more desperate fashion
        raw_date = re.compile("([0-9]* [A-Za-z]* [0-9]*)[^0-9]*$").search(titletext)
        if raw_date:
            attempt(raw_date.groups()[0])

            # try finding it in subtags of the title tag
        for t in titletag.iterdescendants():
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



def extract(page,a):
    x = page.find(a)
    if x is None:
        raise CantFindElement(a)
    return (x.text or "").strip()



class CantFindElement(ConversionError):
    def __init__(self,searchstring):
        self.message = "can't find element \"%s\""%searchstring

class CantFindDate(ConversionError):
    def __init__(self):
        self.message = "can't find a date"

class CantFindCitation(ConversionError):
    def __init__(self):
        self.message = "can't find the citations"
