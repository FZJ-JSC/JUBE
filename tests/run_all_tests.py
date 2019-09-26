#!/usr/bin/env python
# JUBE Benchmarking Environment
# Copyright (C) 2008-2016
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
from parameter_tests import TestParameter, TestParameterSet,
                            TestStaticParameter, TestFixedParameter, 
                            TestTemplateParameter
from pattern_tests import TestPattern, TestPatternset, 
from fileset_test import TestFileset, TestFile, TestLink, TestCopy, TestPrepare
from step_test import TestStep, TestOperation
#from examples_test import TestExamples


if __name__ == "__main__":
    unittest.main()
