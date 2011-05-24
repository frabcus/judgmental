"""
Extracts metadata from files and stores in a SQL database.
"""

from dateutil.parser import parse as dateparse
from lxml import html, etree
import re
import os
import levenshtein
import courts

from general import *



def analyse(file_list, dbfile_name, logfile, use_multiprocessing):

    print "-"*25
    print "Analysis..."
    with DatabaseManager(dbfile_name,use_multiprocessing,check=False) as cursor:
        create_tables(cursor)

        finished_count = Counter()

        def analyse_report(filename):
            "Callback function; reports on success or failure"
            def closure(r):
                "Takes True and a dict, or False and a message"
                (s,d) = r
                try:
                    if s:
                        try:
                            write_metadata_to_sql(d,cursor)
                        except sqlite.IntegrityError, e:
                            raise StandardConversionError("sqlite.IntegrityError: %s - Citations extracted: %s "%(str(e), d['citations']))
                        finished_count.inc()
                        print "analyse:%6d. %s"%(finished_count.count, os.path.basename(filename))
                    else:
                        raise StandardConversionError(d)
                except ConversionError, e:
                    e.log("analysis",os.path.basename(filename),logfile)
            return closure

        with ProcessManager(use_multiprocessing) as process_pool:
            for filename in file_list:
                process_pool.apply_async(analyse_file,(filename,dbfile_name,use_multiprocessing),callback=analyse_report(filename))

    broadcast(logfile,"Extracted metadata from %d files"%(finished_count.count))
        

def best_filename(year, abbreviated_court, citations):
    """Choose the best name for this judgment from the available citations. Is a generator, returning alternative versions."""

    dummy_citation = "[%d] %s " % (year, abbreviated_court)
    
    (distance, name) = min((levenshtein.levenshtein(dummy_citation, s, deletion_cost=2,substitution_cost=2), s) for s in citations)
    
    #If the distance is too great, complain
    if len(name) < len(dummy_citation):
    	raise StandardConversionError("Could not assign a filename. Dummy citation is '%s'; closest actual citation is '%s', with distance %d"%(dummy_citation,name,distance))
    
    basic_name = abbreviated_court+"/"+str(year)+"/"+name.replace(' ','_').replace('/','__')

    yield basic_name + ".html"
    for c in range(1,100):
        yield basic_name + "_%d"%c + ".html"
    raise StandardConversionError("something's going wrong: we can't give this a filename")


def create_tables(cursor):
    "Create tables in an SQL database"
    s = ['CREATE TABLE courts (courtid INTEGER PRIMARY KEY ASC, name TEXT UNIQUE, abbreviated_name TEXT UNIQUE)',
         'CREATE TABLE citationcodes (citationcodeid INTEGER PRIMARY KEY ASC, citationcode TEXT UNIQUE)',
         'CREATE TABLE judgmentcodes (judgmentcodeid INTEGER PRIMARY KEY ASC, citationcodeid INTEGER, judgmentid INTEGER)',
         'CREATE TABLE judgments (judgmentid INTEGER PRIMARY KEY ASC, title TEXT, date DATE, courtid INTEGER, filename TEXT UNIQUE, bailii_url TEXT UNIQUE, judgmental_url TEXT UNIQUE)',
         'CREATE TABLE parties (partyid INTEGER PRIMARY KEY ASC, name TEXT, position INTEGER, judgmentid INTEGER)']
    create_tables_interactively(cursor,['courts','citationcodes','judgmentcodes','judgments','parties'],s)


def analyse_file(filename,dbfile_name,use_multiprocessing):
    try:
        page = html.parse(open_bailii_html(filename))

        metadata = {}
        metadata["filename"] = os.path.basename(filename)
        titletag = page.find("//title") 
        metadata["title"] = title = re.sub('  +', ' ',extract(page,"//title").replace('\n', ' '))
        metadata["bailii_url"] = extract(page,'//small/i') # should get this by other means?
        citations = find_citations(page,title)
        # weakly normalise the citations
        metadata["citations"] = set(re.sub('  +', ' ',i).replace('.','').replace("'","") for i in citations)
        metadata["court_name"] = extract(page,'//td[@align="left"]/h1')
        metadata["date"] = find_date(page,titletag,title)
        metadata["parties"] = parties_from_title(title)
        return (True,metadata)
    except ConversionError, e:
        return (False,e.message)


def write_metadata_to_sql(d,cursor):
    "Inserts judgment metadata to SQL database"

    # make sure there's a record for the court
    def get_court(court_name):
        cursor.execute('SELECT courtid,abbreviated_name FROM courts WHERE name = ?', (court_name,))
        result = cursor.fetchone()
        return result

    result = get_court(d["court_name"])
    if not result:
        abbreviated_court,d["court_name"] = min((levenshtein.levenshtein(d["court_name"], long), short, long) for (short, long) in courts.courts)[1:]
        result = get_court(d["court_name"])

    if result:
        (courtid,abbreviated_court) = result
    else:
        cursor.execute('INSERT INTO courts(name, abbreviated_name) VALUES (?,?)', (d["court_name"],abbreviated_court))
        courtid = cursor.lastrowid

    # insert a record
    for judgmental_url in best_filename(d["date"].year, abbreviated_court, d["citations"]):
        try:
            cursor.execute('INSERT INTO judgments(title, date, courtid, filename, bailii_url, judgmental_url) VALUES (?, ?, ?, ?, ?, ?)', (d["title"], d["date"], courtid, d["filename"], d["bailii_url"], judgmental_url))
            break
        except sqlite.IntegrityError:
            pass
    judgmentid = cursor.lastrowid

    # store the citations
    for c in d["citations"]:
        cursor.execute('SELECT citationcodeid FROM citationcodes WHERE citationcode = ?', (c,))
        result = cursor.fetchone()
        if result:
            i = result[0]
        else:
            cursor.execute('INSERT INTO citationcodes(citationcode) VALUES (?)', (c,))
            i = cursor.lastrowid
        cursor.execute('INSERT INTO judgmentcodes(citationcodeid, judgmentid) VALUES (?, ?)', (i,judgmentid))

    # store the parties
    for (i,n) in d["parties"]:
        cursor.execute('INSERT INTO parties(position, name, judgmentid) VALUES (?, ?, ?)', (i,n,judgmentid))



class GotIt(Exception):
    "This is a labour-saving device"
    def __init__(self,value):
        self.value = value



def find_citations(page,title):

    # This is messy, ad-hoc code that needs to be cleaned up

    # Important: if you are still using this in the year 2999 make sure to fix the millenium bugs below. Although perhaps UK case law data will be a bit more open by then? Well, I can dream...

    def rstrip_date(s):
        date = re.search(r'.+?(\([^(]+)$', s)
        if date is not None:
            possible_date = date.group(1).split(')')[0].strip(', \n(')
            if possible_date.isdigit():
                if re.search(r'^[12]\d\d\d$', possible_date) is not None:
                    return s[:date.start(1)].strip()
                else:
                    return s
            try:
                dateparse(possible_date)
                s = s[:date.start(1)].strip()
            except (ValueError, TypeError):
                pass
        return s

    def make_citeset(s):
        o = set(re.sub('  +',' ',i.strip(', \n')) for i in s.replace(u'\xa0',' ').split('\n'))
        o.discard('')
        j = set()
        for cite in o:
            year = re.search(r'\[[12]\d\d\d\]|\([12]\d\d\d\)',cite)
            if year is not None:
                cite = cite[year.start():]
                subcites = set()
                if cite[0] == '[':
                    r = re.compile(r'.+?(\[[12]\d\d\d\])')
                else:
                    r = re.compile(r'.+?(\([12]\d\d\d\))')
                while True:
                    year_next = r.search(cite)
                    if year_next is not None:
                        prev = rstrip_date(cite[:year_next.start(1)].rstrip(' \n'))
                        if len(prev) > 6:
                            subcites.add(prev)
                        cite = cite[year_next.start(1):]
                    else:
                        break
                cite = rstrip_date(cite)
                if len(cite) > 6:
                    subcites.add(cite)
                j = j.union(subcites)
            else:
                j.add(rstrip_date(cite))
        j.discard('')
        return j

    # try looking for a "Cite as:"
    for x in page.findall('//small/br'):
        if x.tail[:8]=="Cite as:":
            c = make_citeset(x.tail[8:])
            if c:
                return c

    # does the title have the form "something [citeyear] stuff"?
    title_cite = re.search(r"\[[12]\d\d\d\]",title)
    if title_cite is not None:
        x = title[title_cite.start():].replace(';','\n')
        c = make_citeset(x)
        if c:
            return c

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
        return g.value.date()

    raise CantFindDate()



def parties_from_title(title):
    """
    We attempt to recognise the name of the parties to the case.

    We generate a list of pairs (i,x) where i is 1 if it occurs before the "v." (so quite likely a claimant) and 2 if it occurs afterwards (so probably a respondant), and x is the name of the party.
    """

    title,_,_ = title.partition("[")
    first,_,second = title.replace(" v. "," v ").partition(" v ")

    if second:
        return [(1,p.strip()) for p in second.split("&amp;")]+[(2,p.strip()) for p in first.split("&")]
    else:
        return []



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
