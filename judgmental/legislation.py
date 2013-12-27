#!/usr/bin/env python

# Obtain list of all legislation from legislation.gov.uk's Atom feed.

# TODO: Currently just retrieves UK Public General Acts.  Decide what other
# legislation is worth fetching.

# TODO: Welsh regulations have both English and Welsh names contained
# in the title attribute.  Currently we just dump all this into the
# database - would be better to split it up and create two entries.
        
# TODO: Old acts sometimes contain "(repealed)" in the title.    

import feedparser
import sys
from general import \
    create_tables_interactively,\
    DatabaseManager

class ImportLegislation:

    def __init__(self, \
        cursor, \
        dbfile="../../judgmental_nonlive.db", \
        uritemplate="http://legislation.data.gov.uk/ukpga/%d/data.feed", \
        verbose=False):

        self.uritemplate = uritemplate
        self.dbfile = dbfile
        self.verbose = verbose
        self.cursor = cursor

        if not self.cursor:
            self.cursor = DatabaseManager(self.dbfile, False)

    def getandparse(self, uri):
        """
        Grab legislation.gov.uk atom feed, parse, and insert legislation
        titles and links into db; assumes table `legislation` exists.
        """
    
        d = feedparser.parse(uri)
    
        if self.verbose: print d.feed.links
            
        for entry in d.entries:
            title = entry.title
            link = [l.href for l in entry.links if l.rel == "self"][0]
            
            
            if title[:4] == "The ":
                title = title[4:]
                
            if self.verbose: print title
    
            self.cursor.execute(\
                'INSERT INTO legislation(title,link) VALUES (?,?)', \
                (title,link))
    
        try:
            newuri =  [l.href for l in d.feed.links if l.rel == "next"][0]
            if self.verbose: print newuri
            # Strange time loop in 1976
            if newuri == uri:
                return None
            return newuri
        except IndexError:
            return None
    
    def run(self):
        """
        Driver method; marshal pre-requisites and call getandparse() for each
        year 1801 - <this_year>
        """
        create_tables_interactively(\
            self.cursor,\
            ['legislation'],\
            ['CREATE TABLE legislation (legislationid INTEGER PRIMARY KEY ASC, title TEXT, link TEXT)']\
        )
    
        for year in range(1801, 2012):
            if self.verbose: print year
            uri = self.uritemplate % year
            while uri is not None:
                uri = self.getandparse(uri)

if __name__ == "__main__":
    verbose = ''
    arguments = sys.argv[1:]
    while len(arguments) > 0:
        a = arguments[0]
        arguments = arguments[1:]
        if a == "--verbose":
            verbose = True

    importer = ImportLegislation(verbose=verbose)
    importer.run()
