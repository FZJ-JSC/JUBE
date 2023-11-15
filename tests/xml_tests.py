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
"""Test additional xml script examples"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import sys
import filecmp
import re
import glob
import unittest
import os
import shutil
import jube2.main


class TestXMLScripts(unittest.TestCase):

    """Class for testing additional xml scripts"""

    def test_duplicate_replace_and_unequal_options_for_parameters(self):
        """Testing duplicate option replace and unequal options for duplicate parameters"""
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'xml_test_scripts', 'bench_run'))
        jube2.main.main(('run -e '+os.path.join(thisfiledir,
                        'xml_test_scripts/parameter_duplicate_example_with_init_with.xml')).split())
        errorFileExistent = False
        if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run', '000000', '000000_perform_iterations', 'error')):
            errorFileExistent = True
        self.assertFalse(errorFileExistent)

        stdoutFileExistent = True
        if not os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run', '000000', '000000_perform_iterations', 'work', 'stdout')):
            stdoutFileExistent = False
        self.assertTrue(stdoutFileExistent)

        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                      'xml_test_scripts', 'bench_run'))

        return True

    def test_xml_test_01(self):
        """Testing the example xml script xml-test-01.xml"""
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__), 'benchmark_runs'))
        jube2.main.main(('run -e '+os.path.join(thisfiledir,
                        'xml-test-01.xml')).split())
        errorFileExistent = False
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000000_compile', 'error')):
            errorFileExistent = True
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000001_compile', 'error')):
            errorFileExistent = True
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000002_execute_p0', 'error')):
            errorFileExistent = True
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000003_execute_p0', 'error')):
            errorFileExistent = True
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000004_execute_p0', 'error')):
            errorFileExistent = True
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000005_execute_p1', 'error')):
            errorFileExistent = True
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000006_execute_p1', 'error')):
            errorFileExistent = True
        if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000007_execute_p1', 'error')):
            errorFileExistent = True
        self.assertFalse(errorFileExistent)

        stdoutFileExistent = True
        if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000000_compile', 'work', 'stdout')):
            stdoutFileExistent = False
        if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000001_compile', 'work', 'stdout')):
            stdoutFileExistent = False
        if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000002_execute_p0', 'work', 'stdout')):
            stdoutFileExistent = False
        if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000003_execute_p0', 'work', 'stdout')):
            stdoutFileExistent = False
        if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000004_execute_p0', 'work', 'stdout')):
            stdoutFileExistent = False
        if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000005_execute_p1', 'work', 'stdout')):
            stdoutFileExistent = False
        if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000006_execute_p1', 'work', 'stdout')):
            stdoutFileExistent = False
        if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '000007_execute_p1', 'work', 'stdout')):
            stdoutFileExistent = False
        self.assertTrue(stdoutFileExistent)

        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                      'benchmark_runs'))

        return True


if __name__ == "__main__":
    unittest.main()
