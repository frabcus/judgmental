#!/usr/bin/env python

import unittest
import os
import re

from cStringIO import StringIO
from lxml import html

from judgmental.analyse import analyse_file

class TestDateParsing(unittest.TestCase):

    def setUp(self):
        # Not all the files in the input folder will be for this test
        self.test_subjects = ['_scot_cases_ScotHC_2001_62.html']

        # The actual date for each file specified above
        self.test_answers = {'_scot_cases_ScotHC_2001_62.html': '2001-07-25'}

        ### Change location of input files here!
        this_dir = os.path.abspath(\
            os.path.realpath(os.path.dirname(__file__)))
        self.input_dir = os.path.join(this_dir, 'input');

    def test_date_parsing(self):
        for f in self.test_subjects:
            (s, metadata) = analyse_file(os.path.join(self.input_dir, f))
            self.assertTrue(s) # Analysis apparently successful
            self.assertEqual(metadata['date'].strftime('%Y-%m-%d'),\
                self.test_answers[f])

if __name__ == '__main__':
    unittest.main()
