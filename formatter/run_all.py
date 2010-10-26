#!/usr/bin/python

# Main script to run to generate all static content

import os
from local_convert import *

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
content_dir = os.path.join(file_dir, "../../bailii")
output_dir = os.path.join(file_dir, "../../judgmental")
logfile_name = os.path.join(file_dir, "../../errors.log")

infiles = all_html_files(content_dir)

### next goal: phase out this step
duds = set()
print "Creating list of dud files..."
dudfile = open("dud-file-data.txt",'r')
for l in dudfile:
    l = l.strip()
    if len(l) == 0:
        continue
    if l[0] == '#':
        continue
    duds.add(l)
dudfile.close()
print "  ... there are %d dud filenames"%len(duds)

infiles = [f for f in infiles if os.path.basename(f) not in duds]

logfile = open(logfile_name,'w')
convert_files(infiles, output_dir, logfile=logfile)
logfile.close()
