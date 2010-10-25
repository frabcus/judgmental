"""
An object representing a judgment and its metadata, and some standard errors in producing them.
"""

from lxml import html


class Judgment():
    "Represents a single judgment"

    def __init__(self,html,infile):
        self.html = html
        self.infile = infile

    def write_html(self,f):
        f.write(html.tostring(self.html, pretty_print = True))



class ConversionError(Exception):
    def log(self,f,logfile):
        logfile.write("%s: %s"%(f,self.message))


class StandardConversionError(ConversionError):
    def __init__(self,message):
        self.message = message


class Duplicate(ConversionError):
    def __init__(self,old):
        self.message = "duplicate of %s"%old
