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
"""Superclass for testing examples"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import shutil
import os
import jube.main
import examples_tests

EXAMPLES_PREFIX = os.path.join(os.path.dirname(__file__), "../examples")

class TestCase:

    class TestExample(unittest.TestCase):

        """Superclass for testing the included examples"""

        @classmethod
        def setUpClass(cls):
            '''
            Automatically called method before tests in the class are run.

            Create the required paths
            '''
            #Path to example directory, input files and run directory
            cls._path = os.path.join(EXAMPLES_PREFIX, cls._name)
            cls._xml_file = os.path.join(cls._path, cls._name + ".xml")
            cls._yaml_file = os.path.join(cls._path, cls._name + ".yaml")
            cls._bench_run_path = os.path.join(cls._path, "bench_run")

        @classmethod
        def _execute_commands(cls, run_args=[""]):
            '''
            Executes all commands to check the output
            of the examples for correctness.
            '''
            #Delete all existing example runs first
            if os.path.exists(cls._bench_run_path):
                shutil.rmtree(cls._bench_run_path)

            #Create all commands with the specified files and suffixes
            cls._commands = ["run -e --hide-animation {0} {1}".format(file, arg).split() \
                              for arg in run_args \
                              for file in [cls._xml_file, cls._yaml_file]]

            #Execute all commands and save the created worpackage directories
            cls._wp_paths = {}
            for command_id, command in enumerate(cls._commands):
                jube.main.main(command)
                run_path = cls._get_run_path(cls, cls._bench_run_path, command_id)
                cls._wp_paths[run_path] = cls._get_wp_pathes(cls, run_path)

            #Save run arguments for result test
            cls._run_args = run_args

        def test_for_status_files_in_wp_folders(self):
            '''
            Checks that there is a done file and
            no error files in the workpackage directories.
            '''
            for run_path, command_wps in self._wp_paths.items():
                for wp_id, wp_path in command_wps.items():
                    self.assertTrue(self._existing_done_file(wp_path),
                                    "Failed to successfully complete "
                                    "workpackage with id {0}: Missing "
                                    "done file in workpackage directory {1}"
                                    .format(wp_id, wp_path))
                    self.assertFalse(self._existing_error_file(wp_path),
                                    "Failed to successfully complete "
                                    "workpackage with id {0}: Missing "
                                    "done file in workpackage  directory {1}"
                                    .format(wp_id, wp_path))

        def test_for_stdout_content_in_work_folders(self):
            '''
            Checks that the contents of the stdout files in the working
            directories matches the expected contents.
            '''
            for run_path, command_wps in self._wp_paths.items():
                command_id = int(run_path[-2:])
                for wp_id, wp_path in command_wps.items():
                    work_path = self._get_work_path(wp_path)
                    stdout_path = self._get_stdout_file(work_path)
                    stdout = self._content_of_file(stdout_path)
                    self.assertEqual(stdout, self._stdout[command_id][wp_id],
                                     "Error: stdout file for workpackage with "
                                     "id {0} in work directory {1} has not the "
                                     "right content".format(wp_id, stdout_path))

        def test_for_equal_result_data(self):
            '''Checks that the result output matches the target result output'''
            #Checks only if a result output has been processed
            if "-r" in self._run_args:
                for run_path, command_wps in self._wp_paths.items():
                    #Get content of target result output
                    origin_result_path = os.path.join(os.path.dirname(__file__),
                                                      "examples_result_output",
                                                      self._name, "result.dat")
                    origin_result_content = \
                                    self._content_of_file(origin_result_path)

                    #Get actual content of result output
                    run_result_path = os.path.join(run_path, "result",
                                                   "result.dat")
                    run_result_content = self._content_of_file(run_result_path)

                    #Check that both result outputs are the same
                    self.assertEqual(run_result_content, origin_result_content,
                                     "Result content for example {0} not "
                                     "correct".format(self._name))

        def _get_run_path(self, bench_run_path, command_id):
            """Returns the path of the run directory for the given path and id"""
            return os.path.join(bench_run_path, f"{command_id:06}")

        def _get_wp_pathes(self, run_path):
            """
            Returns a dictionary with the path of the workpackage
            directory in the given path to the corresponding
            workpackage id
            """
            workpackages = {}
            for wp_dir in os.listdir(run_path):
                wp_path = os.path.join(run_path, wp_dir)
                # check if directory and id in name
                if os.path.isdir(wp_path) and (wp_dir[:6]).isdigit():
                    #get wp id out of dir name
                    wp_id = int(wp_dir[:6])
                    workpackages[wp_id] = wp_path
            return workpackages

        def _get_stdout_file(self, file_path):
            '''Returns the path of the stdout file for the given path'''
            return os.path.join(file_path, 'stdout')

        def _get_work_path(self, file_path):
            '''Returns the working folder path for the given path'''
            return os.path.join(file_path, "work")

        def _existing_file(self, file_path):
            '''Checks if the file exists in the given path'''
            return os.path.exists(file_path)

        def _existing_done_file(self, file_path):
            '''Checks if the done file exists in the given path'''
            done_file_path = os.path.join(file_path, 'done')
            return self._existing_file(done_file_path)

        def _existing_error_file(self, file_path):
            '''Checks if the error file exists in the given path'''
            error_file_path = os.path.join(file_path, 'error')
            return self._existing_file(error_file_path)

        def _content_of_file(self, file_path):
            '''Returns the contents of the given file'''
            with open(file_path, 'r') as file:
                output = file.read().strip()
            return output

        @classmethod
        def tearDownClass(cls):
            '''
            Automatically called method after all tests in the class have run.

            Deletes the run folder and with it all of the
            output from the examples.
            '''
            shutil.rmtree(cls._bench_run_path)

if __name__ == '__main__':
    '''Import all example tests to run all tests at once'''
    #import to run all example tests
    from example_tests.example_cycle_tests import TestCycleExample
    from example_tests.example_dependencies_tests import TestDependenciesExample
    from example_tests.example_do_log_tests import TestDoLogExample
    from example_tests.example_duplicate_tests import TestDuplicateExample
    from example_tests.example_environment_tests import TestEnvironmentExample
    from example_tests.example_files_and_sub_tests import TestFilesAndSubExample
    from example_tests.example_hello_world_tests import TestHelloWorldExample
    from example_tests.example_include_tests import TestIncludeExample
    from example_tests.example_iterations_tests import TestIterationsExample
    from example_tests.example_parameter_dependencies_tests import TestParameterDependenciesExample
    from example_tests.example_parameter_update_tests import TestParameterUpdateExample
    from example_tests.example_parameterspace_tests import TestParameterspaceExample
    from example_tests.example_result_creation_tests import TestResultCreationExample
    from example_tests.example_result_database_tests import TestResultDatabaseExample
    from example_tests.example_scripting_parameter_tests import TestScriptingParameterExample
    from example_tests.example_scripting_pattern_tests import TestScriptingPatternExample
    from example_tests.example_shared_tests import TestSharedExample
    from example_tests.example_statistic_tests import TestStatisticExample
    from example_tests.example_tagging_tests import TestTaggingExample
    unittest.main()


