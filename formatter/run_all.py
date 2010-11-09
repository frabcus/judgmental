#!/usr/bin/python
"""
Main script to run to generate all static content

Command-line options:

  --no-sql
        Does not generate an sql index (useful for debugging)

  --slow
        Refuses to use multiprocessing
"""

import sys
import os
from local_convert import *

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
content_dir = os.path.join(file_dir, "../../bailii")
output_dir = os.path.join(file_dir, "../../public_html")
logfile_name = os.path.join(file_dir, "../../errors.log")
dbfile = os.path.join(file_dir, "../../judgmental.db")

infiles = all_html_files(content_dir)

make_sql = True
use_multi_convert = True

for a in sys.argv[1:]:
    if a == "--no-sql":
        print "Option --no-sql selected"
        make_sql = False
    if a == "--slow":
        print "Option --slow selected"
        use_multi_convert = False

logfile = open(logfile_name,'w')
convert_files(infiles, output_dir, make_sql=make_sql, logfile=logfile, dbfile=dbfile, use_multi_convert=use_multi_convert)
logfile.close()
