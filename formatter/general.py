"""
Common utility code
"""

import string
from cStringIO import StringIO

# a slightly modified version of UnicodeDammit from BeautifulSoup
from dammit import UnicodeDammit

import sys
import os
import traceback

try:
    import sqlite3 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

# Can we speed things up by using multiple cores?
global multi_enabled
try:
    from multiprocessing.pool import Pool
    print "Multiprocessing enabled (Python 2.6/3 style)"
    multi_enabled = True
except ImportError:
    try:
        from processing.pool import Pool
        print "Multiprocessing enabled (Python 2.5 style)"
        multi_enabled = True
    except ImportError:
        print "Multiprocessing disabled"
        multi_enabled = False
from fakepool import Pool as FakePool


class ProcessManager():

    def __init__(self,use_multiprocessing,verbose=False):
        self.use_multiprocessing = use_multiprocessing
        self.verbose = verbose

    def __enter__(self):
        if self.verbose:
            print "Creating process pool"
        if self.use_multiprocessing:
            self.process_pool = Pool()
        else:
            self.process_pool = FakePool()
        return self.process_pool
    
    def __exit__(self,errtype,val,traceback):
        if self.verbose:
            print "Closing and joining process pool"
        self.process_pool.close()
        self.process_pool.join()
        return False



class DatabaseManager():

    def __init__(self,dbfile_name,use_multiprocessing,check=True,verbose=False):
        """
        multiprocessing is True or False.
        execute is a list of pairs consisting of an SQL statement and an error message for if it doesn't work.
        check is whether to ensure the database already exists.
        """

        self.dbfile_name = dbfile_name
        self.check = check
        self.use_multiprocessing = use_multiprocessing
        self.verbose = verbose

    def __enter__(self):
        "Returns a cursor"
        if self.verbose:
            print "Connecting to SQLite database"
        if self.check and not os.path.exists(self.dbfile_name):
            print "FATAL: I need a database file to work on."
            quit()
        self.conn = sqlite.connect(self.dbfile_name,check_same_thread = not(self.use_multiprocessing))
        return self.conn.cursor()

    def __exit__(self,errtype,val,trace):
        if self.verbose:
            print "Committing and closing database connection"
        self.conn.commit()
        self.conn.close()
        return False



def create_tables_interactively(cursor,names,sqlcode):
    try:
        for statement in sqlcode:
            cursor.execute(statement)
    except sqlite.OperationalError, e:
        if str(e)[-14:] == "already exists":
            while True:
                print "One or more of the tables called %s already exists; shall I delete it? (Y/N)"%(", ".join(names))
                l = sys.stdin.readline().strip().upper()
                if l == "N":
                    print "Then I'll abort."
                    quit()
                elif l == "Y":
                    for name in names:
                        try:
                            cursor.execute("DROP TABLE %s"%name)
                        except sqlite.OperationalError, e2:
                            if "on such table" not in str(e2):
                                raise
                    for statement in sqlcode:
                        cursor.execute(statement)
                    break # and a kitkat
        else:
            raise



def open_bailii_html(filename, salvage_bad_pages = True):
    "Sort out encoding problems, discard everything up to the first '<' (eg. the BOM) and do CRLF -> LF"
    inf = open(filename,'r')
    data = inf.read()
    v = UnicodeDammit(data, smartQuotesTo=None, isHTML=True)
    u = v.unicode

    if u is None:
        if not salvage_bad_pages:
            raise StandardConversionError('I cannot read this file: perhaps invalid bytes need to be patched first?')
        d = list(v.triedEncodings)
        if v.declaredHTMLEncoding != 'ascii':
            if 'ascii' in d:
                d.remove('ascii')
        if v.declaredHTMLEncoding != 'utf-8' and (len(data) < 3 or data[:3] != '\xef\xbb\xbf'):
            if 'utf-8' in d:
                d.remove('utf-8')
        d.reverse()
        while len(d) > 0:
            try:
                c = d.pop()
                if c.lower() == "iso-8859-1":
                    c = "windows-1252"
                u = data.decode(c, 'replace')
                break
            except LookupError:
                pass
        if u is None:
            raise Exception("Unexpected error in open_bailii_html. This should be impossible!")

    a = u.encode('ascii', 'xmlcharrefreplace')
    start = a.find('<')
    if start == -1:
        raise StandardConversionError("There is no HTML in this file")
    page = a[start:].replace('\r\n','\n')
    controlcodes='\x01\x02\x03\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    page = page.translate(string.maketrans('\r','\n'), controlcodes)
    return StringIO(page)



class ConversionError(Exception):
    def log(self,stage,filename,logfile):
        logfile.write("[%s] %s: %s\n"%(stage,filename,self.message))

class StandardConversionError(ConversionError):
    def __init__(self,message):
        self.message = message

class SqliteIntegrityError(ConversionError):
    def __init__(self,e):
        self.message = "sqlite.IntegrityError: %s"%str(e)

class NoMetadata(ConversionError):
    def __init__(self):
        self.message = "No metadata exists for this file"



class Counter:
    def __init__(self):
        self.count = 0
    def inc(self):
        self.count += 1
    def add(self,n):
        self.count += n



def broadcast(logfile,message):
    print message
    logfile.write("*** "+message+"\n")



def make_unique(l, normalise=(lambda x: x)):
    seen = set()
    for x in l:
        y = normalise(x)
        if y not in seen:
            seen.add(y)
            yield x



def disambiguation_filename(citationcode):
    return "disambiguation_" + citationcode.replace(' ','_').replace("/","__") + ".html"


