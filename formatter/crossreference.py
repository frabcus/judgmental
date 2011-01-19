"""
Searches for citations to Bailii files
"""

try:
    import sqlite3 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

import re
import os
from general import *
import prefixtree


# trying citationtree as a global variable
citationtree = prefixtree.PrefixTree()


def crossreference(file_list,dbfile_name,logfile,process_pool):

    print "-"*25
    print "Crossreferencing..."

    print "Connecting to SQLite database"
    if not os.path.exists(dbfile_name):
        print "FATAL: I need a database file to read; run the analysis phase."
        quit()
    conn = sqlite.connect(dbfile_name, check_same_thread = not(process_pool.genuinely_parallel))
    cursor = conn.cursor()
    try:
        cursor.execute('CREATE TABLE crossreferences (crossreferenceid INTEGER PRIMARY KEY ASC, judgmentid INTEGER, citationid INTEGER)')
    except sqlite.OperationalError:
        print "FATAL: Crossreference table already exists; either drop it, or start again generating all metadata from scratch."
        quit()

    print "Processing file list"
    # hopefully these two are sorted the same way
    filename_list = sorted((os.path.basename(name),name) for name in file_list)
    judgment_list = cursor.execute('SELECT filename,judgmentid FROM judgments ORDER BY filename')
    all_list = [x for x in merge(filename_list,judgment_list)]
    broadcast(logfile,"Recovered %d files for crossreferencing"%len(all_list))

    # counts files processed and crossreferences found
    finished_count = Counter()
    crossreferences_count = Counter()

    def crossreference_report(judgmentid,filename):
        "Callback function; reports on success or failure"
        def closure(r):
            "Take True and a set, or false and a message"
            (s,x) = r
            try:
                if s:
                    finished_count.inc()
                    print "crossreference:%6d. %s"%(finished_count.count, os.path.basename(filename))
                    try:
                        write_crossreferences_to_sql(judgmentid,x,cursor)
                        crossreferences_count.add(len(x))
                    except sqlite.IntegrityError, e:
                        raise SqliteIntegrityError(e)
                else:
                    raise StandardConversionError(x)
            except ConversionError, e:
                e.log("crossreference",os.path.basename(filename),logfile)
        return closure

    print "Making prefix tree"
    cursor.execute('SELECT citation,citationid FROM citations ORDER BY citation')
    sorted_citations = [(a,i) for (a,i) in cursor if suitable(a)]
    citationtree.populate(sorted_citations)
    broadcast(logfile,"Read %d citation formats in database"%len(sorted_citations))
    
    print "Searching through files"
    for (basename,fullname,judgment_id) in all_list:
        process_pool.apply_async(crossreference_file,(fullname,),callback=crossreference_report(judgment_id,basename))

    process_pool.close()
    process_pool.join()
    conn.commit()
    conn.close()
    broadcast(logfile,"Successfully searched %d files for crossreferences"%finished_count.count)
    broadcast(logfile,"Found %d crossreferences"%crossreferences_count.count)



class NoFileMetadata(ConversionError):
    def __init__(self):
        self.message = "No metadata exists for this file"



def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def remove_extra_spaces(data):
    p = re.compile(r'\s+')
    return p.sub(' ', data)

def prepare_page(data):
    return remove_extra_spaces(remove_html_tags(data))



def crossreference_file(fullname):
    # returns a set of other cited judgments
    try:
        f = open_bailii_html(fullname)
        a = set()
        for (_,_,v) in citationtree.search(prepare_page(f.read()),unambiguous=True):
            a.add(v)
        return (True,a)
    except ConversionError, e:
        return (False,e.message)



def suitable(s):
    "The sad fact of the matter is that some citations are junk."
    ### This means we need to mend the citation extractor!
    return len(s) > 7
    


def write_crossreferences_to_sql(judgmentid,citationset,cursor):
    for citationid in citationset:
        cursor.execute('INSERT INTO crossreferences(judgmentid,citationid) VALUES (?,?)', (judgmentid,citationid))

