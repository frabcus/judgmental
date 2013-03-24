#!/usr/bin/env python

import unittest
import os
import re

from cStringIO import StringIO
from lxml import html

from judgmental.analyse import find_date
from judgmental.general import open_bailii_html

class TestDateParsing(unittest.TestCase):

    def setUp(self):
        # Files and the correct metadata for each.
        # For each file, tests will only be performed for those metadata
        # with which we are concerned.
        self.test_subjects = \
            {'date': \
                { '_scot_cases_ScotHC_2001_62.html': '2001-07-25' } \
            }

        # Will be populated by a (page, titletag, title) (value) for
        # each filename (key) as the tests run.
        self.inputs_cache = {}

        # Location of input files
        this_dir = os.path.abspath(\
            os.path.realpath(os.path.dirname(__file__)))
        self.input_dir = os.path.join(this_dir, 'input');

    def _get_inputs(self, filename):
        if not filename in self.inputs_cache.keys():
            self.inputs_cache[filename] = ()

            page = html.parse(\
                open_bailii_html(os.path.join(self.input_dir, filename))\
            )
            titletag = page.find("//title")
            title = re.sub('  +', ' ',\
                page.find("//title").text.replace('\n', ' '))

            self.inputs_cache[filename] = (page, titletag, title)

        return self.inputs_cache[filename]
            

    def test_date_parsing(self):
        for f in self.test_subjects['date']:
            page, titletag, title = self._get_inputs(f) 
            found_date = find_date(page, titletag, title)
            self.assertEqual(found_date.strftime('%Y-%m-%d'),\
                self.test_subjects['date'][f])

if __name__ == '__main__':
    unittest.main()
