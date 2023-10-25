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
from examples_tests import TestCase
#import jube.tests.examples_tests

class TestCycleExample(TestCase.TestExample):

    """Class for testing the cycle example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "cycle"
        cls._stdout = [['0\n1\n2\n3'], ['0\n1\n2\n3']]
        super(TestCycleExample, cls).setUpClass()
        super(TestCycleExample, cls)._execute_commands()

    def test_for_status_files_in_work_folders(self):
        '''
        Additional test to check that there is a done file and
        no error files in the working directories.
        '''
        for run_path, command_wps in self._wp_paths.items():
            for wp_id, wp_path in command_wps.items():
                #get work directory
                work_path = self._get_work_path(wp_path)
                self.assertTrue(self._existing_done_file(work_path),
                                "Failed to successfully complete "
                                "workpackage with id {0}: Missing "
                                "done file in work directory {1}"
                                .format(wp_id, work_path))
                self.assertFalse(self._existing_error_file(work_path),
                                "Failed to successfully complete "
                                "workpackage with id {0}: Missing "
                                "done file in work directory {1}"
                                .format(wp_id, work_path))

if __name__ == "__main__":
    unittest.main()
