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
import shutil
import jube2.main
from examples_tests import TestExample 

class TestSharedExample(TestExample):

    """Class for testing the cycle example"""

    def setUp(self):
        self._path = os.path.join(TestExample.EXAMPLES_PREFIX, "shared")
        self._xml_file = os.path.join(self._path, "shared.xml")
        self._yaml_file = os.path.join(self._path, "shared.yaml")
        self._bench_run_path = os.path.join(self._path, "bench_run")
        self._commands = ["run -e {0}".format(file).split() \
                          for file in [self._xml_file, self._yaml_file]]
        self._wp_paths = None

    def test_example(self):
        for command in self._commands:
            #execute jube run
            jube2.main.main(command)
            self._run_path = self._get_run_path(self._bench_run_path)

            #check for done file and no error file in workpackage folder
            self._test_for_status_files_in_wp_folders()

            #check content of files in shared directory
            shared_path = os.path.join(self._run_path, "a_step_shared")

            #id file exists and correct content?
            id_file = os.path.join(shared_path, "all_ids")
            self.assertTrue(self._existing_file(id_file),
                            "Error: id file for shared "
                            "folder {0} does not exist".format(shared_path))
            id_content = self._content_of_file(id_file)
            self.assertEqual(id_content, "0\n1\n2",
                             "Error: id file for shared folder {0} "
                             "has not the right content".format(shared_path))

            #stdout correct content?
            stdout = self._content_of_file(self._get_stdout_file(shared_path))
            self.assertEqual(stdout, "0\n1\n2",
                             "Error: stdout for shared folder {0} "
                             "has not the right content".format(shared_path))

    def tearDown(self):
        #remove bench_run folder after all tests for this example
        shutil.rmtree(self._bench_run_path)


if __name__ == "__main__":
    unittest.main()
