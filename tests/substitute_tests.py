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
import os
import shutil
import jube2.substitute
import jube2.main

PATH_PREFIX = os.path.join(os.path.dirname(__file__))

class TestSubstitute(unittest.TestCase):

    """Substitute test class"""


    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the required paths
        '''
        cls._path = os.path.join(PATH_PREFIX, 'substitute_test_scripts')
        cls._input_path = os.path.join(cls._path, 'main.xml')
        cls._bench_run_path = os.path.join(cls._path, "bench_run")
        cls._run_path = os.path.join(cls._bench_run_path, "000000")
        cls._wp_path = os.path.join(cls._run_path, "000000_run")
        cls._work_path = os.path.join(cls._wp_path, "work")

        if os.path.exists(cls._bench_run_path):
            shutil.rmtree(cls._bench_run_path)

    def test_regex_substitute(self):
        """Test standard and regex substitute"""
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

    def test_init_with_substitution(self):
        """Testing for existing files and content"""
        jube2.main.main(('run -e '+ self._input_path).split())
        # Test for done file
        done_file = os.path.join(self._wp_path, 'done')
        self.assertTrue(os.path.exists(done_file), "Failed to successfully "
                        "complete workpackage with id 0: Missing done file in "
                        "workpackage directory {0}".format(self._wp_path))
        # Test for error file
        error_file_path = os.path.join(self._wp_path, 'error')
        self.assertFalse(os.path.exists(error_file_path), "Failed to "
                         "successfully complete workpackage with id 0: Missing "
                         "done file in workpackage  directory {0}"
                         .format(self._wp_path))
        # Test for stderr (empty?)
        stderr_file = os.path.join(self._work_path, 'stderr')
        with open(stderr_file, 'r') as file:
            stderr_output = file.read().strip()
        self.assertEqual(stderr_output, "", "Error: stderr file for workpackage "
                         "with id 0 in work directory {0} has not the right "
                         "content".format(self._work_path))
        # Test for same submit.job.in
        original_submit_file = os.path.join('../platform/slurm', 'submit.job.in')
        with open(original_submit_file, 'r') as file:
            origin_submit_output = file.read().strip()
        check_submit_file = os.path.join (self._work_path, 'submit.job.in')
        with open(check_submit_file, 'r') as file:
            check_submit_output = file.read().strip()
        self.assertEqual(origin_submit_output, check_submit_output, "Error: "
                         "submit.job.in file for workpackage with id 0 in "
                         "work directory {0} has not the right content"
                         .format(self._work_path))
        # Test for submit.job substitute
        stdout_file = os.path.join(self._work_path, 'stdout')
        with open(stdout_file, 'r') as file:
            stdout_output = file.read().strip()
        submit_file = os.path.join(self._work_path, 'submit.job')
        with open(submit_file, 'r') as file:
            submit_output = file.read().strip()
        self.assertEqual(stdout_output, submit_output, "Error: submit.job file "
                         "for workpackage with id 0 in work directory {0} has "
                         "not the right content".format(self._work_path))
        self.assertNotEqual(submit_output, check_submit_output, "Error: There "
                            "has been no substitution for the submit job file "
                            "for workpackage with id 0 in work directory {0}"
                            .format(self._work_path))
        # Search for non-substituted vars
        sub_vars_regex = re.compile("(#[A-Z_]*?#)")
        matches = re.findall(sub_vars_regex, submit_output)
        self.assertEqual(matches, [], "Error: There has been no substitution "
                         "for the submit job file for workpackage with id 0 in "
                         "work directory {0}".format(self._work_path))
        # Compare both submit.job files
        check_file = os.path.join(self._path, 'submit.job')
        with open(check_file, 'r') as file:
            check_output = file.read().strip()
        self.assertEqual(check_output, submit_output, "Error: The substitution "
                         "in the submit.job for workpackage with id 0 in work "
                         "directory {0} has failed or is incorrect "
                         .format(self._work_path))

    @classmethod
    def tearDownClass(cls):
        '''
        Automatically called method after all tests in the class have run.

        Deletes the run folder and all created files.
        '''
        shutil.rmtree(cls._bench_run_path)
        if os.path.exists("file.in"):
            os.remove("file.in")
        if os.path.exists("std_file.out"):
            os.remove("std_file.out")
        if os.path.exists("regex_file.out"):
            os.remove("regex_file.out")

if __name__ == "__main__":
    unittest.main()
