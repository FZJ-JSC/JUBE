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
import re
import shutil
import jube2.main
from examples_tests import TestExample 

class TestIterationsExample(TestExample):

    """Class for testing the cycle example"""

    def setUp(self):
        self._name = "iterations"
        self._path = os.path.join(TestExample.EXAMPLES_PREFIX, self._name)
        self._path = os.path.join(TestExample.EXAMPLES_PREFIX, "iterations")
        self._xml_file = os.path.join(self._path, "iterations.xml")
        self._yaml_file = os.path.join(self._path, "iterations.yaml")
        self._bench_run_path = os.path.join(self._path, "bench_run")
        self._commands = ["run -e {0} -r".format(file).split() \
                          for file in [self._xml_file, self._yaml_file]]
        self._wp_paths = None
        self._stdout = [ foo + " iter:"+ iter for foo in ["1", "2", "4"]
                        for iter in ["0", "1"]]
        self._stdout += [ foo + " iter:"+ iter for foo in ["1", "2", "4"]
                         for iter in ["0", "1", "2", "3"]]

    def test_example(self):
        for command in self._commands:
            #execute jube run
            jube2.main.main(command)
            self._run_path = self._get_run_path(self._bench_run_path)

            #check for done file and no error file in workpackage folder
            self._test_for_status_files_in_wp_folders()

            #check also for content in work directory
            for wp_id, wp_path in self._wp_paths.items():
                work_path = self._get_work_path(wp_path)
                #check for content of stdout
                stdout = self._content_of_file(self._get_stdout_file(work_path))
                self.assertEqual(stdout, self._stdout[wp_id],
                                 "Error: stdout file in work for workpackage "
                                 "with id {0} has not the right content"
                                 .format(wp_id))

            self._test_for_equal_result_data()

    def _test_for_equal_result_data(self):
        origin_result_file = open(os.path.join("examples_result_output",
                                               self._name, "result.dat"))
        origin_result_content = \
            [re.findall(r'(\|.+ \| .+ \|)(?: [^|]+ \| [^|]+ \| [^|]+ )(\| .+ \|)'
                        ,line) for line in origin_result_file]
        origin_result_file.close()

        run_result_file = open(os.path.join(self._run_path, "result",
                                            "result.dat"))
        run_result_content = \
            [re.findall(r'(\|.+ \| .+ \|)(?: [^|]+ \| [^|]+ \| [^|]+ )(\| .+ \|)'
                        ,line) for line in run_result_file]
        run_result_file.close()

        for run_line in run_result_content:
            self.assertTrue(run_line in origin_result_content, "Result for "
                            "example {} not correct".format(self._name))

    def tearDown(self):
        #remove bench_run folder after all tests for this example
        pass#shutil.rmtree(self._bench_run_path)


if __name__ == "__main__":
    unittest.main()
