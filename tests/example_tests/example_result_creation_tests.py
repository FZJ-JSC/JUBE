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
import jube2.main
from examples_tests import TestCase

class TestResultCreationExample(TestCase.TestExample):

    """Class for testing the result_creation example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "result_creation"
        cls._stdout = [["", "", ""], ["", "", ""]]
        super(TestResultCreationExample, cls).setUpClass()
        super(TestResultCreationExample, cls)._execute_commands(["-r"])

    def test_for_de_and_en_files(self):
        '''
        Additional test to check the content of the de and en files
        '''
        origin_stdout = [[text + ": "+ number for text in ["Zahl", "Number"]]
                        for number in ["1", "2", "4"]]
        for run_path, command_wps in self._wp_paths.items():
            for wp_id, wp_path in command_wps.items():
                work_path = self._get_work_path(wp_path)
                #Check for content of de file
                de_file = os.path.join(work_path, "de")
                stdout = self._content_of_file(de_file)
                self.assertEqual(stdout, origin_stdout[wp_id][0],
                                 "Error: de file in work for workpackage "
                                 "with id {0} in directory {1} has not the "
                                 "right content".format(wp_id, de_file))

                #Check for content of en file
                en_file = os.path.join(work_path, "en")
                stdout = self._content_of_file(en_file)
                self.assertEqual(stdout, origin_stdout[wp_id][1],
                                 "Error: en file in work for workpackage "
                                 "with id {0} in directory {1} has not the "
                                 "right content".format(wp_id, de_file))

if __name__ == "__main__":
    unittest.main()
