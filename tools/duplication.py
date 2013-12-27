#!/usr/bin/python

"""
Finds duplicate files. If called as a script, works on the directory given as the first argument
"""


import sys
import os

# Get a hash algorithm
try:
    from hashlib import md5
except ImportError:
    from md5 import md5


def filehash(fn):
    "takes a filename and returns a hash of the file"
    m = md5()
    f = open(fn,'r')
    for l in f:
        m.update(l)
    return m.digest()


def make_hashes(files):
    hashes = {}

    for fullname in files:
        d = filehash(fullname)
        if d in hashes:
            hashes[d].append(fullname)
        else:
            hashes[d] = [fullname]

    print "There are %d files, of which %d are distinct."%(len(files),len(hashes))

    return hashes





def all_html_files(root):
    "all html files in a directory, recursively"
    l = []

    for (path,dirs,files) in os.walk(root):
        for f in files:
            if f[-5:] == ".html":
                fullname = os.path.join(path,f)
                l.append(fullname)

    return l



if __name__=="__main__":
    file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
    content_dir = os.path.join(file_dir, "../../bailii")

    h = make_hashes(all_html_files(content_dir))

    print "Duplicates are:"
    for (x,l) in h.iteritems():
        if len(l)>1:
            print " ".join('"%s"'%(x.split("/bailii/")[-1]) for x in l)
            print
