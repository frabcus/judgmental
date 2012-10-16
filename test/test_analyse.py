#!/usr/bin/env python

import unittest
import os

from judgmental.general import open_bailii_html
from cStringIO import StringIO

class TestDateParsing(unittest.TestCase):

    def setUp(self):
        # Not all the files in the input folder will be for this test
        self.test_subjects = []

        # The actual date for each file specified above
        self.test_answers = {}
    
        ### Change location of input files here!
        this_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
        self.input_dir = os.path.join(this_dir, '/input');

    def test_date_parsing(self):
        for f in self.test_subjects:
            html_io = open_bailii_html(f)
            tree = etree.parse(html_io)
            self.assertTrue(tree)

if __name__ == '__main__':
    unittest.main()
