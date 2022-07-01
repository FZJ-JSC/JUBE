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
"""Multiprocessing related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import re

import unittest
import jube2.benchmark
import jube2.workpackage


class TestMultiprocessing(unittest.TestCase):

    """Multiprocessing test class"""

    def setUp(self):
        pass

    def test_multiprocessing(self):
        """Test multiprocessing execution"""
        pass


if __name__ == "__main__":
    unittest.main()
