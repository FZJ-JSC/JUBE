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
"""Test the cycle example"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
from examples_tests import TestCase

class TestTaggingExample(TestCase.TestExample):

    """Class for testing the tagging example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "tagging"
        cls._stdout = [["Hallo $world_str"] , ["Hallo $world_str"],
                       ["Hello World"], ["Hello World"],
                       ["Hallo World"], ["Hallo World"]]
        super(TestTaggingExample, cls).setUpClass()

        #Create run arguments for commands with all tag combinations
        tags = ["deu", "eng", "deu eng"]
        run_args = []
        for tag in tags:
            run_args.append("--tag "+tag)
        super(TestTaggingExample, cls)._execute_commands(run_args)

if __name__ == "__main__":
    unittest.main()
