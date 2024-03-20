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
from yaml_tests import TestYAMLScripts
from xml_tests import TestXMLScripts
from step_tests import TestOperation
from step_tests import TestDoLog
from util_tests import TestUtil
from conf_tests import TestConf
from substitute_tests import TestSubstitute


if __name__ == "__main__":
    unittest.main()
