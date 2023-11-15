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
"""Test the cycle example"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import os
import re
from examples_tests import TestCase

class TestIterationsExample(TestCase.TestExample):

    """Class for testing the iterations example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "iterations"
        cls._stdout = [ foo + " iter:"+ iter for foo in ["1", "2", "4"]
                        for iter in ["0", "1"]]
        cls._stdout += [ foo + " iter:"+ iter for foo in ["1", "2", "4"]
                         for iter in ["0", "1", "2", "3"]]
        cls._stdout = [cls._stdout, cls._stdout]
        super(TestIterationsExample, cls).setUpClass()
        super(TestIterationsExample, cls)._execute_commands(["-r"])

    def test_for_equal_result_data(self):
        '''
        Overwrites the original test (TestExample.test_for_equal_result_data())
        for the result output to allow an example specific test.
        '''
        for run_path, command_wps in self._wp_paths.items():
            #Get content of target result output
            result_file_path = os.path.join(os.path.dirname(__file__),
                                            "../examples_result_output",
                                            self._name, "result.dat")
            origin_result_file = open(result_file_path)
            origin_result_content = \
                [re.findall(r'(\|.+ \| .+ \|)(?: [^|]+ \| [^|]+ \| [^|]+ )(\| .+ \|)'
                            ,line) for line in origin_result_file]
            origin_result_file.close()

            #Get actual content of result output
            run_result_file = open(os.path.join(run_path, "result",
                                                "result.dat"))
            run_result_content = \
                [re.findall(r'(\|.+ \| .+ \|)(?: [^|]+ \| [^|]+ \| [^|]+ )(\| .+ \|)'
                            ,line) for line in run_result_file]
            run_result_file.close()

            #Check that the two results using a regular expression are the same.
            for run_line in run_result_content:
                self.assertTrue(run_line in origin_result_content, "Result for "
                                "example {} not correct".format(self._name))

if __name__ == "__main__":
    unittest.main()
