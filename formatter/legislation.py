#!/usr/bin/python

# Obtain list of all legislation from legislation.gov.uk's Atom feed.

# TODO: Currently just retrieves UK Public General Acts.  Decide what other
# legislation is worth fetching.

# TODO: Welsh regulations have both English and Welsh names contained
# in the title attribute.  Currently we just dump all this into the
# database - would be better to split it up and create two entries.
		
# TODO: Old acts sometimes contain "(repealed)" in the title.	

import feedparser
import sys
from general import *

verbose = False

def getandparse(uri, cursor):

	d = feedparser.parse(uri)
	if verbose: print d.feed.links
		
	for entry in d.entries:
		title = entry.title
		link = [l.href for l in entry.links if l.rel=="self"][0]
		
		
		if title[:4] == "The ":
			title = title[4:]
			
		if verbose: print title
		cursor.execute('INSERT INTO legislation(title,link) VALUES (?,?)',(title,link))

	try:
		newuri =  [l.href for l in d.feed.links if l.rel=="next"][0]
		if verbose: print newuri
		# Strange time loop in 1976
		if newuri == uri:
			return None
		return newuri
	except IndexError:
		return None


arguments = sys.argv[1:]
while len(arguments)>0:
    a = arguments[0]
    arguments = arguments[1:]
    if a == "--verbose":
    	verbose = True

uritemplate = "http://legislation.data.gov.uk/ukpga/%d/data.feed"
dbfile = "../../judgmental_nonlive.db"

with DatabaseManager(dbfile, False) as cursor:
	create_tables_interactively(cursor,['legislation'],['CREATE TABLE legislation (legislationid INTEGER PRIMARY KEY ASC, title TEXT, link TEXT)'])

	for year in range(1801,2011):
		if verbose: print year
		uri = uritemplate % year
		while uri is not None:
			uri = getandparse(uri, cursor)
