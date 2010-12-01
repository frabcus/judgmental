#!/usr/bin/python

"""
Command-line script to convert files named on the command line; useful for debugging.

Does not require that the directory be specified; can find them from the filename alone. So the following are all equivalent:
  ./run_one.py _uk_cases_SIAC_2007_42_2005.html
  ./run_one.py ../../bailii/_uk_cases_SIAC/_uk_cases_SIAC_2007_42_2005.html
  ./run_one.py doesnt/matter/at/all/_uk_cases_SIAC_2007_42_2005.html
"""

import sys, os, re
from local_convert import convert

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
content_dir = os.path.join(file_dir, "../../bailii")
output_dir = os.path.join(file_dir, "../../public_html")

r = re.compile("(_[a-z]*_cases_[A-Za-z]*)")

for givenname in sys.argv[1:]:
    basename = os.path.basename(givenname)
    indir = r.match(basename).groups()[0]
    infilename = os.path.join(content_dir, indir, basename)
    convert(infilename,output_dir)
