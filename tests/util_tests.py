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
"""Util related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import jube2.util.util


class TestUtil(unittest.TestCase):

    """Util python file test class"""

    def test_convert_type(self):
        """Test convert_type"""
        self.assertEqual(type(jube2.util.util.convert_type("int","42",stop=True)),int)
        self.assertEqual(type(jube2.util.util.convert_type("float","42",stop=True)),float)
        self.assertEqual(type(jube2.util.util.convert_type("float","3.141",stop=True)),float)
        with self.assertRaises(TypeError):
            jube2.util.util.convert_type("int","3.141",stop=True)
        with self.assertRaises(ValueError):
            jube2.util.util.convert_type("int","forty-two",stop=True)
        self.assertEqual(jube2.util.util.convert_type("int","forty-two",stop=False),"forty-two")


if __name__ == "__main__":
    unittest.main()
