"""
Searches for citations to Bailii files
"""

import re
import os
from general import *
import prefixtree


# trying citationtree as a global variable
citationtree = prefixtree.PrefixTree()


def crossreference(file_list, dbfile_name, logfile, use_multiprocessing):

    print "-"*25
    print "Crossreferencing..."

    with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
        try:
            cursor.execute('CREATE TABLE crossreferences (crossreferenceid INTEGER PRIMARY KEY ASC, judgmentid INTEGER, citationid INTEGER)')
        except sqlite.OperationalError:
            print "FATAL: Crossreference table already exists; either drop it, or start again generating all metadata from scratch."
            quit()

        print "Making prefix tree"
        cursor.execute('SELECT citation,citationid FROM citations ORDER BY citation')
        sorted_citations = [(a,i) for (a,i) in cursor if suitable(a)]
        citationtree.populate(sorted_citations)
        broadcast(logfile,"Read %d citation formats in database"%len(sorted_citations))

    # counts files processed and crossreferences found
    finished_count = Counter()
    crossreferences_count = Counter()
    
    def crossreference_report(basename):
        "Callback function; reports on success or failure"
        def closure(r):
            "Take True and a number, or false and a message"
            (s,m) = r
            try:
                if s:
                    finished_count.inc()
                    crossreferences_count.add(m)
                    print "crossreference:%6d. %s"%(finished_count.count,basename)
                else:
                    raise StandardConversionError(m)
            except ConversionError,e:
                e.log("crossreference",basename,logfile)
        return closure

    print "Searching through files"
    with ProcessManager(use_multiprocessing) as process_pool:
        for fullname in file_list:
            basename = os.path.basename(fullname)
            process_pool.apply_async(crossreference_file,(fullname,basename,dbfile_name,use_multiprocessing),callback=crossreference_report(basename))

    broadcast(logfile,"Successfully searched %d files for crossreferences"%finished_count.count)
    broadcast(logfile,"Found %d crossreferences"%crossreferences_count.count)




def crossreference_file(fullname,basename,dbfile_name,use_multiprocessing):
    # returns a set of other cited judgments
    try:
        f = open_bailii_html(fullname)
        citationset = set()
        for (_,_,v) in citationtree.search(prepare_page(f.read()),unambiguous=True):
            citationset.add(v)
        with DatabaseManager(dbfile_name,use_multiprocessing) as cursor:
            try:
                jids = list(cursor.execute('SELECT judgmentid FROM judgments WHERE filename=?',(basename,)))
                if len(jids)>0:
                    judgmentid = jids[0][0]
                else:
                    raise NoMetadata
                for citationid in citationset:
                    cursor.execute('INSERT INTO crossreferences(judgmentid,citationid) VALUES (?,?)', (judgmentid,citationid))
            except sqlite.IntegrityError, e:
                raise SqliteIntegrityError(e)
        return (True,len(citationset))
    except ConversionError, e:
        return (False,e.message)





def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def remove_extra_spaces(data):
    p = re.compile(r'\s+')
    return p.sub(' ', data)

def prepare_page(data):
    return remove_extra_spaces(remove_html_tags(data))






def suitable(s):
    "The sad fact of the matter is that some citations are junk."
    ### This means we need to mend the citation extractor!
    return len(s) > 7
    



