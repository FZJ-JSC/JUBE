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
"""Test the cycle example"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import os
from examples_tests import TestCase

class TestIncludeExample(TestCase.TestExample):

    """Class for testing the include example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "include"
        cls._stdout = [["bar\nTest\n1", "bar\nTest\n2", "bar\nTest\n4"],
                       ["bar\nTest\n1", "bar\nTest\n2", "bar\nTest\n4"]]
        super(TestIncludeExample, cls).setUpClass()
        #Change input file names
        cls._xml_file = os.path.join(cls._path, "main.xml")
        cls._yaml_file = os.path.join(cls._path, "main.yaml")
        super(TestIncludeExample, cls)._execute_commands()

if __name__ == "__main__":
    unittest.main()
