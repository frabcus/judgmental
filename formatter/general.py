"""
Common utility code
"""

import string
from cStringIO import StringIO

# a slightly modified version of UnicodeDammit from BeautifulSoup
from dammit import UnicodeDammit



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
    page = a[start:].replace('\r\n','\n')
    page = page.translate(string.maketrans('\r','\n'), '\x0c')
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




def merge(l1,l2):
    "Silly general tool for merging two sorted lists"
    i1 = iter(l1)
    i2 = iter(l2)
    t1 = i1.next()
    n1 = t1[0]
    t2 = i2.next()
    n2 = t2[0]
    while True:
        if n1 < n2:
            t1 = i1.next()
            n1 = t1[0]
        elif n1 > n2:
            t2 = i2.next()
            n2 = t2[0]
        else:
            yield t1 + t2[1:]
            t1 = i1.next()
            n1 = t1[0]
            t2 = i2.next()
            n2 = t2[0]


def collate(l):
    "Silly general tool for combining matching things from a sorted list."

    first = True
    x1 = None
    ds = []
    for (x2,d) in l:
        if first:
            first = False
            x1 = x2
            ds = [d]
        elif x1==x2:
            ds.append(d)
        else:
            yield(x1,ds)
            x1 = x2
            ds = [d]
    if not first:
        yield(x1,ds)
    raise StopIteration
