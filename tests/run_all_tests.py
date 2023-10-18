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
"""Collection of all tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
from parameter_tests import TestParameter, TestParameterSet
from multiprocessing_tests import TestMultiprocessing
from pattern_tests import TestPattern
from benchmark_tests import TestBenchmark
from result_database_tests import TestResultDatabase
from examples_tests import TestExample
from yaml_tests import TestYAMLScripts
from xml_tests import TestXMLScripts
from step_tests import TestOperation
from step_tests import TestDoLog
from util_tests import TestUtil
from conf_tests import TestConf


if __name__ == "__main__":
    unittest.main()
