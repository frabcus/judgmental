#!/usr/bin/python

# Main script to run to generate all static content

import os
import sys

from bailli_to_judgmental import BtoJ 

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
content_dir = os.path.join(file_dir, "../content")
output_dir = os.path.join(file_dir, "../output")

btoj = BtoJ()

btoj.massage_page_to_file(os.path.join(content_dir, "about.html"), os.path.join(output_dir, "about.html"))

