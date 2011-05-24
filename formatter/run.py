#!/usr/bin/python
"""
Main script to run to generate all static content

Command-line options:

  --no-analyse
       Does not do the analysis phase (and so does not require the judgmental.db file to be deleted in advance)

  --no-crossreference
       Does not do the crossreferencing

  --no-convert
       Does not generate any html output

  --no-legislation
       Does not add links to legislation

  --no-index
       Does not run the indexing phase

  --no-disambiguation
       Does not run the disambiguation phase

  --delete-db
       Deletes the database file before starting

  --delete-html
       After converting, removes any HTML output still remaining from previous runs. Note that, to ensure continuous usability of the output directory, it is executed only after conversion has occurred.

  --slow
       Refuses to use multiprocessing

  --profile
       Runs the Python C profiler

  --files
       Works only on the files which follow
"""

import sys
import os
import time
from datetime import datetime

import analyse
import crossreference
import convert
import disambiguation
import indexes
import delete_html
from general import *


# standard filenames
file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
input_dir = os.path.join(file_dir, "../../bailii")
output_dir = os.path.join(file_dir, "../../public_html_nonlive/judgments")
logfile_name = os.path.join(file_dir, "../../errors.log")
dbfile_name = os.path.join(file_dir, "../../judgmental_nonlive.db")

# default options
use_multiprocessing = multi_enabled # which is defined by general.py
do_analyse = True
do_crossreference = True
do_convert = True
do_legislation = True
do_index = True
do_disambiguation = True
run_on_all_files = True
do_delete_db = False
do_delete_html = False
profiling = False
file_list = []

# parse command-line options
arguments = sys.argv[1:]
while len(arguments)>0:
    a = arguments[0]
    arguments = arguments[1:]
    if a == "--no-analyse" or a == "--no-analysis":
        print "Option --no-analyse selected"
        do_analyse = False
    elif a == "--no-crossreference":
        print "Option --no-crossreference selected"
        do_crossreference = False
    elif a == "--no-convert":
        print "Option --no-convert selected"
        do_convert = False
    elif a == "--no-legislation":
        print "Option --no-legislation selected"
        do_legislation = False
    elif a == "--no-index":
        print "Option --no-index selected"
        do_index = False
    elif a == "--no-disambiguation":
        print "Option --no-disambiguation selected"
        do_disambiguation = False
    elif a == "--slow":
        print "Option --slow selected"
        use_multiprocessing = False
    elif a == "--delete-html":
        print "Option --delete-html selected"
        do_delete_html = True
    elif a == "--delete-db":
        print "Option --delete-db selected"
        do_delete_db = True
    elif a == "--profile":
        print "Option --profile selected"
        profiling = True
    elif a == "--files":
        print "Using file list supplied"
        run_on_all_files = False
        while len(arguments)>0 and (arguments[0][:2] != "--"):
            file_list.append(arguments[0])
            arguments = arguments[1:]
    else:
        print "FATAL: I don't understand the command-line argument %s"%a
        quit()

# one argument combination is stupid
if (do_analyse, do_crossreference, do_convert) == (True,False,True):
    print "FATAL: You're planning to generate a database without crossreferencing information in. That won't work."
    quit()

# default is to use all files
print "Generating file list"
if run_on_all_files:
    for (path,dirs,files) in os.walk(input_dir):
        for f in files:
            if f[-5:] == ".html":
                file_list.append(os.path.join(path,f))

def do_the_business():
    # open logfile
    with open(logfile_name,'w') as logfile:

        # some details
        broadcast(logfile,"File list contains %d files"%len(file_list))

        # delete the database
        if do_delete_db:
            os.remove(dbfile_name)

        # analysis stage
        if do_analyse:
            start = datetime.now()
            analyse.analyse(file_list=file_list,dbfile_name=dbfile_name,logfile=logfile,use_multiprocessing=use_multiprocessing)
            elapsed = datetime.now() - start
            broadcast(logfile,"Analyse phase took %s"%elapsed)

        # crossreference stage
        if do_crossreference:
            start = datetime.now()
            crossreference.crossreference(file_list=file_list,dbfile_name=dbfile_name,logfile=logfile,use_multiprocessing=use_multiprocessing)
            elapsed = datetime.now() - start
            broadcast(logfile,"Crossreference phase took %s"%elapsed)

        # convert stage
        if do_convert:
            conversion_start = time.time()
            start = datetime.now()
            convert.convert(file_list=file_list,dbfile_name=dbfile_name,logfile=logfile,output_dir=output_dir,use_multiprocessing=use_multiprocessing,do_legislation=do_legislation)
            elapsed = datetime.now() - start
            broadcast(logfile,"Convert phase took %s"%elapsed)
            if do_delete_html:
                delete_html.delete_html(conversion_start,output_dir)

        # disambiguation stage
        if do_disambiguation:
            disambiguation_start = time.time()
            start = datetime.now()
            disambiguation.disambiguation(file_list=file_list,dbfile_name=dbfile_name,logfile=logfile,output_dir=output_dir,use_multiprocessing=use_multiprocessing)
            elapsed = datetime.now() - start
            broadcast(logfile,"Disambiguation phase took %s"%elapsed)

        # index stage
        if do_index:
            start = datetime.now()
            indexes.make_indexes(dbfile_name=dbfile_name,logfile=logfile,output_dir=output_dir,use_multiprocessing=use_multiprocessing)
            elapsed = datetime.now() - start
            broadcast(logfile,"Index phase took %s"%elapsed)


if profiling:
    import cProfile
    cProfile.run("do_the_business()")
else:
    do_the_business()
