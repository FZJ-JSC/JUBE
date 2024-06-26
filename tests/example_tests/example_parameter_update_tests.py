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
"""Test the cycle example"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
from examples_tests import TestCase

class TestParameterUpdateExample(TestCase.TestExample):

    """Class for testing the parameter_update example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "parameter_update"
        cls._stdout = [["iter_never: 0\niter_use: 0\niter_step: 0",
                        "iter_never: 0\niter_use: 1\niter_step: 1",
                        "iter_never: 0\niter_use: 1\niter_step: 2"],
                        ["iter_never: 0\niter_use: 0\niter_step: 0",
                        "iter_never: 0\niter_use: 1\niter_step: 1",
                        "iter_never: 0\niter_use: 1\niter_step: 2"]]
        super(TestParameterUpdateExample, cls).setUpClass()
        super(TestParameterUpdateExample, cls)._execute_commands()

if __name__ == "__main__":
    unittest.main()
