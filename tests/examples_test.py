#!/usr/bin/env python
# JUBE Benchmarking Environment
# Copyright (C) 2008-2014
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
"""Test the examples"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import os.path
import jube2.main


EXAMPLES_PREFIX = os.path.join(os.path.dirname(__file__), "../examples")


class TestExamples(unittest.TestCase):
    """Class for testing the included examples"""
    def test_examples(self):
        """Main function"""
        examples_tasks = [
            ExampleChecker("environment", "environment.xml"),
            ExampleChecker("jobsystem", "jobsystem.xml", debug=True),
            ExampleChecker("result_creation", "result_creation.xml"),
            ExampleChecker("files_and_sub", "files_and_sub.xml"),
            ExampleChecker("dependencies", "dependencies.xml"),
            ExampleChecker("tagging", "tagging.xml"),
            ExampleChecker("parameterspace", "parameterspace.xml"),
            ExampleChecker("scripting_parameter", "scripting_parameter.xml"),
            ExampleChecker("include", "main.xml"),
            ExampleChecker("shared", "shared.xml"),
            ExampleChecker("hello_world", "hello_world.xml"),
        ]

        for checker in examples_tasks:
            self.assertTrue(checker.run())


class ExampleChecker(object):
    """Class for checking examples"""
    def __init__(self, bench_path, xml_file, bench_run_path=None,
                 check_function=None, debug=False):
        """Init instance.

        The check_function should return a bool value to indicate the
        success of failure of the test.

        """
        self._xml_file = os.path.join(EXAMPLES_PREFIX, bench_path, xml_file)

        self._bench_run_path = bench_run_path or os.path.join(
            EXAMPLES_PREFIX, bench_path, "bench_run")

        self._check_function = check_function
        self._debug = debug

    def run(self):
        """Run example"""
        success = True
        debug = "--debug" if self._debug else ""
        jube2.main.main("{0} run {1}".format(debug, self._xml_file). split())
        if self._check_function:
            success = self.check_function()
        if not self._debug:
            jube2.main.main("remove -f {0}".format(self._bench_run_path).
                            split())
        return success


if __name__ == "__main__":
    unittest.main()
