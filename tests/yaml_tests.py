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
"""Test additional yaml example scripts"""

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
import jube2.util.yaml_converter


class TestYAMLScripts(unittest.TestCase):

    """Class for testing additional yaml scripts"""

    def test_newline_separator(self):
        """Testing newline separator"""
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'yaml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'yaml_test_scripts', 'bench_run'))
        jube2.main.main(('run -e '+os.path.join(thisfiledir,
                        'yaml_test_scripts/newline_separator.yaml')).split())
        errorFileExistent = False
        if os.path.exists(os.path.join(thisfiledir, 'yaml_test_scripts', 'bench_run', '000000', '000000_execute', 'error')):
            errorFileExistent = True
        if os.path.exists(os.path.join(thisfiledir, 'yaml_test_scripts', 'bench_run', '000000', '000001_execute', 'error')):
            errorFileExistent = True
        self.assertFalse(errorFileExistent)
        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                      'yaml_test_scripts', 'bench_run'))

    def test_multiple_benchmarks(self):
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'yaml_test_scripts', 'bench_run_1')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'yaml_test_scripts', 'bench_run_1'))
        if os.path.exists(os.path.join(thisfiledir, 'yaml_test_scripts', 'bench_run_2')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'yaml_test_scripts', 'bench_run_2'))
        jube2.main.main(('run -e '+os.path.join(thisfiledir,
                        'yaml_test_scripts/multiple_benchmarks.yaml')).split())
        stdoutFileExistent = True
        if not os.path.exists(os.path.join(thisfiledir, 'yaml_test_scripts', 'bench_run_1', '000000', '000000_execute', 'work', 'stdout')):
            stdoutFileExistent = False
        if not os.path.exists(os.path.join(thisfiledir, 'yaml_test_scripts', 'bench_run_2', '000000', '000000_execute', 'work', 'stdout')):
            stdoutFileExistent = False
        self.assertTrue(stdoutFileExistent)
        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                      'yaml_test_scripts', 'bench_run_1'))
        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                      'yaml_test_scripts', 'bench_run_2'))

    def test_overwrite_parameterset(self):
        """Testing errors due to overwriting the parameterset within yaml"""
        thisfiledir = os.path.dirname(__file__)
        if os.path.exists(os.path.join(thisfiledir, 'yaml_test_scripts', 'bench_run')):
            shutil.rmtree(os.path.join(os.path.dirname(__file__),
                          'yaml_test_scripts', 'bench_run'))

        try:
            import ruamel.yaml
            try:
                jube2.util.yaml_converter.YAML_Converter(os.path.join(thisfiledir,'yaml_test_scripts/overwrite_parameterset.yaml'))
            except ruamel.yaml.constructor.DuplicateKeyError:
                return
        except ImportError:
            try:
                jube2.main.main(('run -e '+os.path.join(thisfiledir,
                            'yaml_test_scripts/overwrite_parameterset.yaml')).split())
            except SystemExit:
                return



if __name__ == "__main__":
    unittest.main()
