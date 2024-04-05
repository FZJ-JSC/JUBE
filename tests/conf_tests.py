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
"""Test the configurations"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import jube.conf
from jube.util.version import StrictVersion

class TestConf(unittest.TestCase):

    """Class for testing the configurations"""

    def test_version_number(self):
        """version number testing"""
        StrictVersion(jube.conf.JUBE_VERSION)


if __name__ == "__main__":
    unittest.main()
