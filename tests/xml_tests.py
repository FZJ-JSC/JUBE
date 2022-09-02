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
        for i in ["0_compile","1_compile","2_execute_p0","3_execute_p0","4_execute_p0","5_execute_p1","6_execute_p1","7_execute_p1"]:
            if os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '00000'+i, 'error')):
                errorFileExistent = True
        self.assertFalse(errorFileExistent)

        stdoutFileExistent = True
        for i in ["0_compile","1_compile","2_execute_p0","3_execute_p0","4_execute_p0","5_execute_p1","6_execute_p1","7_execute_p1"]:
            if not os.path.exists(os.path.join(thisfiledir, 'benchmark_runs', '000000', '00000'+i, 'work', 'stdout')):
                stdoutFileExistent = False
        self.assertTrue(stdoutFileExistent)

        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                      'benchmark_runs'))

        return True

    def test_stepdepend_1(self):
        """Testing stepdepend_1 sample script"""
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'xml_test_scripts', 'bench_run'))
        jube2.main.main(('run -e '+os.path.join(thisfiledir,
                        'xml_test_scripts/stepdepend_1.xml')).split())
        errorFileExistent = False
        for i in ["000000_step_1","000001_step_2","000002_step_3"]:
            if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run', '000000', i, 'error')):
                errorFileExistent = True
        self.assertFalse(errorFileExistent)

        stdoutFileExistent = True
        for i in ["000000_step_1","000001_step_2","000002_step_3"]:
            if not os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run', '000000', i, 'work', 'stdout')):
                stdoutFileExistent = False
        self.assertTrue(stdoutFileExistent)

        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                      'xml_test_scripts', 'bench_run'))

        return True

    def test_stepdepend_2(self):
        """Testing stepdepend_2 sample script"""
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'xml_test_scripts', 'bench_run'))

        with self.assertRaises(SystemExit):
            jube2.main.main(('run -e '+os.path.join(thisfiledir,
                        'xml_test_scripts/stepdepend_2.xml')).split())

        if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'xml_test_scripts', 'bench_run'))

        return True

    def test_stepprepare_1(self):
        """Testing stepprepare_1 sample script"""
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'xml_test_scripts', 'bench_run'))
        jube2.main.main(('run -e '+os.path.join(thisfiledir,
                        'xml_test_scripts/stepprepare_1.xml')).split())
        errorFileExistent = False
        for i in ["0_perform_iterations_1","1_perform_iterations_2","2_perform_iterations_3"]:
            if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run', '000000', '00000'+i, 'error')):
                errorFileExistent = True
        self.assertFalse(errorFileExistent)

        stdoutFileExistent = True
        for i in ["0_perform_iterations_1","1_perform_iterations_2","2_perform_iterations_3"]:
            if not os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run', '000000', '00000'+i, 'work', 'stdout')):
                stdoutFileExistent = False
        self.assertTrue(stdoutFileExistent)

        stdoutFileNonExistent = True
        for i in ["3_perform_iterations_4","4_perform_iterations_5"]:
            if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run', '000000', '00000'+i, 'work', 'stdout')):
                stdoutFileNonExistent = False
        self.assertTrue(stdoutFileNonExistent)

        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                      'xml_test_scripts', 'bench_run'))

        return True

    def test_stepprepare_2(self):
        """Testing stepprepare_2 sample script"""
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'xml_test_scripts', 'bench_run'))

        with self.assertRaises(SystemExit):
            jube2.main.main(('run -e '+os.path.join(thisfiledir,
                        'xml_test_scripts/stepprepare_2.xml')).split())

        if os.path.exists(os.path.join(thisfiledir, 'xml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'xml_test_scripts', 'bench_run'))

        return True


if __name__ == "__main__":
    unittest.main()
