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
"""Test the examples

This alters the 

"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import os.path
import jube2.main


def main():
    """Main function"""
    ExampleChecker.path_prefix = "../examples"

    examples_tasks = [
        ExampleChecker("hello_world", "hello_world.xml"),
        # ExampleChecker("environment", "environment.xml"),
        # ExampleChecker("jobsystem", "jobsystem.xml"),
    ]

    for checker in examples_tasks:
        checker.run()


class ExampleChecker(object):
    path_prefix = None

    def __init__(self, bench_path, xml_file, bench_run_path=None,
                 check_function=None):
        self._xml_file = os.path.join(self.path_prefix, bench_path, xml_file)

        if bench_run_path is None:
            self._bench_run_path = os.path.join(
                self.path_prefix, bench_path, "bench_run")
        else:
            self._bench_run_path = bench_run_path

        self._check_function = check_function
        print(vars(self))

    def run(self):
        jube2.main.main("run {0}".format(self._xml_file).split())
        if self._check_function:
            self.check_function()
        jube2.main.main("remove -f {0}".format(self._bench_run_path).split())


if __name__ == "__main__":
    main()
