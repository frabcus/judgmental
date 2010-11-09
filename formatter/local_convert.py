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

# Get a hash algorithm
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

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


def filehash(fn):
    "takes a filename and returns a hash of the file"
    m = md5()
    f = open(fn,'r')
    for l in f:
        m.update(l)
    return m.digest()


def make_hashes(files,hashfile,use_multi=multi_enabled):
    hashes = {}

    def filehash_report(fn):
        def closure(d):
            if d in hashes:
                hashes[d].append(fn)
            else:
                hashes[d] = [fn]
        return closure

    print "Hashing files..."
    p = pool(use_multi)
    for filename in files:
        p.apply_async(filehash,(filename,),callback=filehash_report(filename))
    p.close()
    p.join()
    print
    print "  ... %d files, of which %d are distinct"%(len(files),len(hashes))

    f = open(hashfile,'w')
    pickle.dump(hashes,f)
    f.close()

    return hashes


def read_hashes(hashfile):
    f = open(hashfile,'r')
    hashes = pickle.load(f)
    f.close()
    return hashes


def convert(filenames,outdir):
    "Returns True and a judgment, or False and a message"
    try:
        j = BtoJ().make_judgment(filenames[0])
        j.write_html_to_dir(outdir)
        return (True,j)
    except ConversionError, e:
        return (False,e.message)


def convert_files(files,outdir,hashfile=os.devnull,refresh_hashes=True,logfile=stdout,dbfile=':memory:',use_multi_hash=multi_enabled,use_multi_convert=multi_enabled):

    if not refresh_hashes:
        hashes = read_hashes(hashfile)
        files_set1 = set(files)
        files_set2 = set()
        for l in hashes.itervalues():
            files_set2.update(l)
        if files_set1 != files_set2:
            print "File list has changed"
            refresh_hashes = True
        else:
            print "Using stored file list"
            
    if refresh_hashes:
        hashes = make_hashes(files,hashfile,use_multi=use_multi_hash)

    finished_count = Counter()
        
    def convert_report(filenames):
        def closure(r):
            "Takes True and a judgment object, or False and a message"
            (s,x) = r
            if s:
                f = filenames[0]
                finished_count.inc()
                print "%6d. %s"%(finished_count.count, os.path.basename(f))
                try:
                    x.write_to_sql(cursor)
                except sqlite.IntegrityError, e:
                    StandardConversionError("sqlite.IntegrityError: %s"%str(e)).log(os.path.basename(f),logfile) # should be handled better?
                #conn.commit()
                for filename in filenames[1:]:
                    Duplicate(os.path.basename(f)).log(os.path.basename(filename),logfile)
            else:
                for filename in filenames:
                    StandardConversionError(x).log(os.path.basename(filename),logfile)
        return closure

    print "Initialising SQLite database..."
    if multi_enabled and use_multi_convert:
        conn = sqlite.connect(dbfile, check_same_thread = False)
    else:
        conn = sqlite.connect(dbfile)
    cursor = conn.cursor()
    try:
        create_tables(cursor)
    except sqlite.OperationalError: # should be handled better?
        print "Database file already exists. Remove it first if you are sure..."
        quit()
    print "Converting files..."
    p = pool(use_multi_convert)
    for filenames in hashes.itervalues():
        p.apply_async(convert,(filenames,outdir),callback=convert_report(filenames))
    p.close()
    p.join()
    conn.commit()
    conn.close()
    print " ... done"


