#!/usr/bin/env python3
# JUBE Benchmarking Environment
# Copyright (C) 2008-2022
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
import jube2.main
from examples_tests import TestCase

class TestSharedExample(TestCase.TestExample):

    """Class for testing the shared example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "shared"
        cls._stdout = [["", "", ""], ["", "", ""]]
        super(TestSharedExample, cls).setUpClass()
        super(TestSharedExample, cls)._execute_commands()

    def test_additional(self):
        '''
        Additional test to check the content of the shared directories
        '''
        for run_path, command_wps in self._wp_paths.items():
            #Check the content of the files in shared directory
            shared_path = os.path.join(run_path, "a_step_shared")

            #Check for existence of id file
            id_file = os.path.join(shared_path, "all_ids")
            self.assertTrue(self._existing_file(id_file),
                            "Error: id file for shared "
                            "folder {0} does not exist".format(shared_path))
            #Check for content of id file
            id_content = self._content_of_file(id_file)
            self.assertEqual(id_content, "0\n1\n2",
                             "Error: id file for shared folder {0} "
                             "has not the right content".format(shared_path))

            #Check for content of stdout file
            stdout = self._content_of_file(self._get_stdout_file(shared_path))
            self.assertEqual(stdout, "0\n1\n2",
                             "Error: stdout for shared folder {0} "
                             "has not the right content".format(shared_path))

if __name__ == "__main__":
    unittest.main()
