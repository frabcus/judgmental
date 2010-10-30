#!/usr/bin/python

# Main script to run to generate all static content

import os
from local_convert import *

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
content_dir = os.path.join(file_dir, "../../bailii")
output_dir = os.path.join(file_dir, "../../public_html")
logfile_name = os.path.join(file_dir, "../../errors.log")
hashfile = os.path.join(file_dir, "../../hashes.data")

infiles = all_html_files(content_dir)

logfile = open(logfile_name,'w')
convert_files(infiles, output_dir, hashfile=hashfile, logfile=logfile)
logfile.close()
