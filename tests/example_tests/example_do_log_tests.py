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
from examples_tests import TestCase 

class TestDoLogExample(TestCase.TestExample):

    """Class for testing the do_log example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "do_log"
        cls._stdout = [["", "", "", "", ""],
                       ["", "", "", "", ""]]
        super(TestDoLogExample, cls).setUpClass()
        super(TestDoLogExample, cls)._execute_commands()

    def test_for_do_log_and_stdout_files(self):
        '''
        Additional test to check the existence of the do_log files,
        the contents of the stdout files in the shared directory
        and the existence and contents of the loreipsum files
        in the shared directory.
        '''
        for run_path, command_wps in self._wp_paths.items():
            for wp_id, wp_path in command_wps.items():
                #Check for the existence of the do_log files
                do_log_path = os.path.join(wp_path, 'do_log')
                self.assertTrue(self._existing_file(do_log_path),
                                "Error: do_log file for workpackage with "
                                "id {0} in directory {1} does not exist"
                                .format(wp_id, do_log_path))

            #Check for the contents of the stdout files in the shared directory
            shared_path = os.path.join(run_path, "execute_shared")
            stdout = self._content_of_file(self._get_stdout_file(shared_path))
            self.assertEqual(stdout, "loreipsum4", "Error: stdout file for "
                             "shared directory {0} has not the right content"
                             .format(shared_path))
            #Check for the existence and contents of the loreipsum files
            for i in range(1, 6):
                loreipsum_path = os.path.join(shared_path, "loreipsum"+str(i))
                self.assertTrue(self._existing_file(loreipsum_path),
                                "Error: loreipsum"+str(i)+" file for shared "
                                "directory {0} does not exist".format(shared_path))
                self.assertEqual(self._content_of_file(os.path.join(
                                 self._path, "loreipsum"+str(i))),
                                 self._content_of_file(loreipsum_path),
                                 "Error: loreipsum"+str(i)+" file for shared "
                                 "directory {0} has not the right content"
                                 .format(shared_path))

if __name__ == "__main__":
    unittest.main()
