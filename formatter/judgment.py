"""
An object representing a judgment and its metadata, and some standard errors in producing them.
"""

from lxml import etree
import os
import datetime
from dateutil.parser import parse as dateparse

try:
    import sqlite3 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite


class Judgment:
    "Represents a single judgment"

    def __init__(self,xhtml,infilename,title,date,citations,courtname,bailii_url):
        self.xhtml = xhtml 
        self.infilename = infilename
        self.title = title
        if type(date) is str:
            date = dateparse(date)
        self.date = datetime.date(date.year, date.month, date.day)
        if type(citations) is str:
            self.citations = [i.strip() for i in citations.split(',')]
        else:
            self.citations = citations
        self.courtname = courtname
        self.bailii_url = bailii_url
        self.outbasename = os.path.basename(infilename).replace(" ","_")

    def write_html(self,f):
        f.write(etree.tostring(self.xhtml, pretty_print = True))

    def write_html_to_dir(self,dirname):
        o = open(os.path.join(dirname,self.outbasename), 'w')
        self.write_html(o)
        o.close()
        
    def write_to_sql(self, cursor):
        "Outputs judgment metadata to SQL database"
        cursor.execute('INSERT OR IGNORE INTO courts(name) VALUES (?)', (self.courtname,))
        self.courtid = cursor.lastrowid
        cursor.execute('INSERT INTO judgments(title, date, courtid, filename, bailii_url) VALUES (?, ?, ?, ?, ?)', (self.title, self.date, self.courtid, self.outbasename, self.bailii_url))
        self.judgmentid = cursor.lastrowid
        for i in self.citations:
            cursor.execute('INSERT INTO citations(citation, judgmentid) VALUES (?, ?)', (i,self.judgmentid))


def create_tables(cursor):
    "Create tables in an SQL database"
    cursor.execute('CREATE TABLE courts (courtid INTEGER PRIMARY KEY ASC, name TEXT UNIQUE)')
    cursor.execute('CREATE TABLE citations (citationid INTEGER PRIMARY KEY ASC, citation TEXT UNIQUE, judgmentid INTEGER)')
    cursor.execute('CREATE TABLE judgments (judgmentid INTEGER PRIMARY KEY ASC, title TEXT, date DATE, courtid INTEGER, filename TEXT UNIQUE, bailii_url TEXT UNIQUE)')


class ConversionError(Exception):
    def log(self,f,logfile):
        logfile.write("%s: %s\n"%(f,self.message))


class StandardConversionError(ConversionError):
    def __init__(self,message):
        self.message = message
