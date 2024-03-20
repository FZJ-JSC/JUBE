#!/usr/bin/env python3
# JUBE Benchmarking Environment
# Copyright (C) 2008-2024
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
from examples_tests import TestCase 

class TestFilesAndSubExample(TestCase.TestExample):

    """Class for testing the files_and_sub example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "files_and_sub"
        cls._stdout = ["Number: "+i+ "\nZahl: "+j
                       for i in ["1", "2", "4"]
                       for j in ["2", "4", "5"]]
        cls._stdout = [cls._stdout, cls._stdout]
        super(TestFilesAndSubExample, cls).setUpClass()
        super(TestFilesAndSubExample, cls)._execute_commands()

    def test_for_file_in_and_file_out(self):
        '''
        Additional test to check the content of the file.in and file.out files
        '''
        for run_path, command_wps in self._wp_paths.items():
            command_id = int(run_path[-2:])
            #Check for content in work directory
            for wp_id, wp_path in command_wps.items():
                work_path = self._get_work_path(wp_path)
                #Check for content of file.in
                origin_file_in = self._content_of_file(os.path.join(self._path,
                                                                    "file.in"))
                actual_file_in = self._content_of_file(os.path.join(work_path,
                                                                    "file.in"))
                self.assertEqual(actual_file_in, origin_file_in,
                                 "Error: file.in in work for workpackage "
                                 "with id {0} in directory {1} has not the "
                                 "right content".format(wp_id, work_path))

                #Check for content of file.out -> sub successful?
                file_out = self._content_of_file(os.path.join(work_path,
                                                              "file.out"))
                self.assertEqual(file_out, self._stdout[command_id][wp_id],
                                 "Error: file.out in work for workpackage "
                                 "with id {0} in directory {1} has not the "
                                 "right content".format(wp_id, work_path))

if __name__ == "__main__":
    unittest.main()
