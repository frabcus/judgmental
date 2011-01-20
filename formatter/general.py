"""
Common utility code
"""


from cStringIO import StringIO

# a slightly modified version of UnicodeDammit from BeautifulSoup
from dammit import UnicodeDammit

import os

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







def open_bailii_html(filename):
    "Sort out encoding problems, discard everything up to the first '<' (eg. the BOM) and do CRLF -> LF"
    inf = open(filename,'r')
    data = inf.read()
    u = UnicodeDammit(data, smartQuotesTo=None, isHTML=True).unicode
    if u is None:
        raise StandardConversionError('I cannot read this file: the invalid bytes need to be patched first')
    a = u.encode('ascii', 'xmlcharrefreplace')
    start = a.find('<')
    if start == -1:
        raise StandardConversionError("There is no HTML in this file")
    page = a[start:].replace('\r\n','\n').replace('\r','\n') # hmmmmmmm?!
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
