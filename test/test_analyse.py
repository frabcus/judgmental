#!/usr/bin/env python

import unittest
import os
import re

from cStringIO import StringIO
from lxml import html

from judgmental.analyse import analyse_file

class TestDateParsing(unittest.TestCase):

    def setUp(self):
        # Files and the correct metadata for each
        self.test_subjects = \
            {'_scot_cases_ScotHC_2001_62.html': \
                { 'date': '2001-07-25' } \
            }

        ### Change location of input files here!
        this_dir = os.path.abspath(\
            os.path.realpath(os.path.dirname(__file__)))
        self.input_dir = os.path.join(this_dir, 'input');

    def test_date_parsing(self):
        for k in self.test_subjects:
            (s, metadata) = analyse_file(os.path.join(self.input_dir, k))
            self.assertTrue(s) # Analysis apparently successful
            self.assertEqual(metadata['date'].strftime('%Y-%m-%d'),\
                self.test_subjects[k]['date'])

if __name__ == '__main__':
    unittest.main()
