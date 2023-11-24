#!/usr/bin/env python3
# JUBE Benchmarking Environment
# Copyright (C) 2008-2023
# Forschungszentrum Juelich GmbH, Juelich Supercomputing Centre
# http://www.fz-juelich.de/jsc/jube
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Pattern related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import re
import unittest
import jube2.substitute
import os


class TestSubstitute(unittest.TestCase):

    """Substitute test class"""

    def setUp(self):
        #Create file.in 
        with open('file.in', 'w') as file:
            file.write('Number: #NUMBER#')
        self.std_files_data = [["std_file.out", "file.in", "w"]]
        self.std_sub = jube2.substitute.Sub("#NUMBER#", "text", "1")
        self.std_sub_set = jube2.substitute.Substituteset("sub_set",
                                                          self.std_files_data,
                                                          {"#NUMBER#": self.std_sub})
        self.std_sub_set.substitute({}, None)
        self.regex_files_data = [["regex_file.out", "file.in", "w"]]
        self.regex_sub = jube2.substitute.Sub("#.*#", "regex", "1")
        self.regex_sub_set = jube2.substitute.Substituteset("regex_set",
                                                            self.regex_files_data,
                                                            {"#.*#": self.regex_sub})
        self.regex_sub_set.substitute({}, None)

    def test_substitute(self):
        """Test standard and regex substitute"""
        #Do std substitute
        self.std_sub_set.substitute({})
        #Get content of stdout
        with open("std_file.out", 'r') as file:
            std_output = file.read().strip()

        #Do regex substitute
        self.regex_sub_set.substitute({})
        #Get content of regex
        with open("regex_file.out", 'r') as file:
            regex_output = file.read().strip()

        #test if output equal
        self.assertEqual(std_output, regex_output)

    def tearDown(self):
        os.remove("file.in")
        os.remove("std_file.out")
        os.remove("regex_file.out")

if __name__ == "__main__":
    unittest.main()
