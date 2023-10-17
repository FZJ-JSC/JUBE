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

class TestDoLogExample(TestExample):

    """Class for testing the cycle example"""

    def setUp(self):
        self._path = os.path.join(TestExample.EXAMPLES_PREFIX, "do_log")
        self._xml_file = os.path.join(self._path, "do_log.xml")
        self._yaml_file = os.path.join(self._path, "do_log.yaml")
        self._bench_run_path = os.path.join(self._path, "bench_run")
        self._commands = ["run -e {0}".format(file).split() \
                          for file in [self._xml_file, self._yaml_file]]
        self._stdout = "loreipsum4"


    def test_example(self):
        for command in self._commands:
            #execute jube run
            jube2.main.main(command)

            #get paths to check for files and content
            run_path = self._get_run_path(self._bench_run_path)
            wp_names = self._get_wp_paths(run_path)
            for wp in wp_names:
                wp_path = os.path.join(run_path, wp)
                if wp != "execute_shared":
                    wp_id = int(wp[:6])
                    #check for done file and no error file in workpackage folder
                    self.assertTrue(self._existing_done_file(wp_path),
                                    "Error: done file for workpackage folder "
                                    "{0} does not exist".format(wp))
                    self.assertFalse(self._existing_error_file(wp_path),
                                    "Error: error file for workpackage folder "
                                    "{0} does exist".format(wp))
                    #check also for do_log files
                    do_log_path = os.path.join(wp_path, 'do_log')
                    self.assertTrue(self._existing_file(do_log_path),
                                    "Error: do_log file for workpackage folder "
                                    "{0} does not exist".format(wp))
                else:
                    #check if loreipsum files exist and content is the same
                    for i in range(1, 6):
                        loreipsum_path = os.path.join(wp_path, "loreipsum"+str(i))
                        self.assertTrue(self._existing_file(loreipsum_path),
                                        "Error: loreipsum"+str(i)+" file for shared "
                                        "folder {0} does not exist".format(wp))
                        self.assertEqual(self._content_of_file(os.path.join(
                                         self._path, "loreipsum"+str(i))),
                                         self._content_of_file(loreipsum_path),
                                         "Error: loreipsum"+str(i)+" file for shared "
                                         "folder {0} has not the right content".format(wp))
                    self.assertEqual(self._content_of_file(self._get_stdout_file(wp_path)),
                                     self._stdout, "Error: stdout file for shared "
                                     "folder {0} has not the right content".format(wp))

                #check for right content in stdout file
                #work_path = os.path.join(wp_path, "work")
                #stdout_path = self._get_stdout_file(work_path)
                #self.assertEqual(self._stdout[wp_id], self._content_of_file(stdout_path), f"{stdout_path}")

    def tearDown(self):
        #remove bench_run folder after all tests for this example
        shutil.rmtree(self._bench_run_path)


if __name__ == "__main__":
    unittest.main()
