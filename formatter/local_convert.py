from sys import stdout
import os


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
    import hashlib.md5
except ImportError:
    import md5

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


class Counter():
    def __init__(self):
        self.count = 0
    def inc(self):
        self.count += 1


def filehash(fn):
    "takes a filename and returns a hash of the file"
    m = md5.new()
    f = open(fn,'r')
    for l in f:
        m.update(l)
    return (fn,m.digest())


def convert(filenames,outdir):
    try:
        j = BtoJ().make_judgment(filenames[0])
        j.write_html_to_dir(outdir)
        return (True,j,filenames)
    except ConversionError, e:
        return (False,e,filenames)


def convert_files(files,outdir,logfile=stdout,use_multi=multi_enabled):

    hashes = {}

    def filehash_report(t):
        (fn,d) = t
        if d in hashes:
            hashes[d].append(filename)
        else:
            hashes[d] = [filename]

    print "Hashing files..."
    p = pool(use_multi)
    for filename in files:
        p.apply_async(filehash,(filename,),callback=filehash_report)
    p.close()
    p.join()
    print
    print "  ... %d files, of which %d are distinct"%(len(files),len(hashes))

    finished_count = Counter()
        
    def convert_report(r):
        "Takes True and a judgment object, or False and an exception"
        (s,e,filenames) = r
        if s:
            f = filenames[0]
            finished_count.inc()
            print "%6d. %s"%(finished_count.count, os.path.basename(f))
            ### any code for e to upload its metadata should go here
            for filename in filenames[1:]:
                Duplicate(f).log(filename,logfile)
        else:
            for filename in filenames:
                e.log(filename,logfile)

    print "Converting files..."
    p = pool(use_multi)
    for filenames in hashes.itervalues():
        p.apply_async(convert,(filenames,outdir),callback=convert_report)
    p.close()
    p.join()
    print " ... done"


