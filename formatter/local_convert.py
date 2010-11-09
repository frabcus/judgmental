from sys import stdout
import os
import pickle

try:
    import sqlite3 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite


# Look see if we can speed things up by using multiple cores
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

from judgment import *
from fakepool import Pool as FakePool
from bailii_to_judgmental import *


def pool(use_multi):
    if use_multi:
        if not multi_enabled:
            raise ValueError("Multiprocessing is disabled")
        print "  (using multiprocessing)"
        return Pool()
    else:
        return FakePool()


def all_html_files(root):
    "all html files in a directory, recursively"
    l = []

    for (path,dirs,files) in os.walk(root):
        for f in files:
            if f[-5:] == ".html":
                l.append(os.path.join(path,f))

    return l


class Counter:
    def __init__(self):
        self.count = 0
    def inc(self):
        self.count += 1


def convert(filename,outdir):
    "Returns True and a judgment, or False and a message"
    try:
        j = BtoJ().make_judgment(filename)
        j.write_html_to_dir(outdir)
        return (True,j)
    except ConversionError, e:
        return (False,e.message)


def convert_files(files,outdir,logfile=stdout,dbfile=':memory:',use_multi_convert=True,make_sql=True):

    use_multi_convert = use_multi_convert and multi_enabled

    finished_count = Counter()
        
    def convert_report(filename):
        def closure(r):
            "Takes True and a judgment object, or False and a message"
            (s,x) = r
            if s:
                finished_count.inc()
                print "%6d. %s"%(finished_count.count, os.path.basename(filename))
                if make_sql:
                    try:
                        x.write_to_sql(cursor)
                    except sqlite.IntegrityError, e:
                        StandardConversionError("sqlite.IntegrityError: %s"%str(e)).log(os.path.basename(f),logfile) # should be handled better?
                #conn.commit()
            else:
                StandardConversionError(x).log(os.path.basename(filename),logfile)
        return closure

    if make_sql:
        print "Initialising SQLite database..."
        conn = sqlite.connect(dbfile)
        cursor = conn.cursor()
        try:
            create_tables(cursor)
        except sqlite.OperationalError: # should be handled better?
            print "Database file already exists. Remove it first if you are sure..."
            quit()
    print "Converting files..."
    p = pool(use_multi_convert)
    for filename in files:
        p.apply_async(convert,(filename,outdir),callback=convert_report(filename))
    p.close()
    p.join()
    if make_sql:
        conn.commit()
        conn.close()
    print " ... done"


