#!/usr/bin/env python
# JUBE Benchmarking Environment
# Copyright (C) 2008-2015
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
"""Pattern related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import jube2.pattern


class TestPattern(unittest.TestCase):

    """Pattern test class"""

    def setUp(self):
        self.std_pattern = jube2.pattern.Pattern("std", ".*", unit="s")
        self.std_pattern2 = jube2.pattern.Pattern("std2", ".*")
        self.derived_pattern = jube2.pattern.Pattern(
            "derived", "$std2", pattern_mode="text")
        self.calculate_pattern = jube2.pattern.Pattern(
            "derived", "100*2", pattern_mode="python", content_type="int")
        self.calculate_pattern_non_derived = jube2.pattern.Pattern(
            "non_derived", "100*$derived",
            pattern_mode="pattern", content_type="int")
        self.jube_pattern = jube2.pattern.get_jube_pattern()

    def test_std_pattern(self):
        """Test standard pattern"""
        self.assertEqual(self.std_pattern.name, "std")
        self.assertEqual(self.std_pattern.value, ".*")
        self.assertEqual(self.std_pattern.unit, "s")
        self.assertEqual(self.std_pattern.content_type, "string")
        result_pattern, changed = self.std_pattern.substitute_and_evaluate([])
        self.assertFalse(changed)
        self.assertEqual(id(result_pattern), id(self.std_pattern))
        self.assertTrue(repr(self.std_pattern).startswith("Pattern({"))
        self.assertTrue(repr(self.std_pattern).endswith("})"))

    def test_derived_pattern(self):
        """Test derived pattern"""
        self.assertTrue(self.derived_pattern.derived)
        self.assertFalse(self.std_pattern.derived)
        patternset = jube2.pattern.Patternset("test_set")
        patternset.add_pattern(self.std_pattern2)
        result_pattern, changed = self.derived_pattern.substitute_and_evaluate(
            [patternset.pattern_storage])
        self.assertTrue(changed)
        self.assertEqual(result_pattern.value, self.std_pattern2.value)
        self.assertNotEqual(id(result_pattern), id(self.derived_pattern))

    def test_calculate_pattern(self):
        """Test pattern evaluation"""
        result_pattern, changed = \
            self.calculate_pattern.substitute_and_evaluate([])
        self.assertTrue(changed)
        self.assertEqual(result_pattern.value, "200")
        patternset = jube2.pattern.Patternset("test_set")
        patternset.add_pattern(result_pattern)
        result_pattern, changed = \
            self.calculate_pattern_non_derived.substitute_and_evaluate(
                [patternset.derived_pattern_storage])
        self.assertTrue(changed)
        self.assertEqual(result_pattern.value, "100*200")

    def test_etree_repr(self):
        """check etree repr"""
        etree = self.std_pattern.etree_repr()
        self.assertEqual(etree.tag, "pattern")
        self.assertEqual(etree.get("type"), "string")
        self.assertEqual(etree.get("mode"), "pattern")
        self.assertEqual(etree.text, ".*")
        etree = self.calculate_pattern.etree_repr()
        self.assertEqual(etree.get("mode"), "python")

    def test_jube_Pattern(self):
        """Test JUBE internal pattern"""
        self.assertEqual(self.jube_pattern["jube_pat_int"].value, "([+-]?\d+)")
        self.assertEqual(self.jube_pattern["jube_pat_nint"].value,
                         "(?:[+-]?\d+)")
        self.assertEqual(self.jube_pattern["jube_pat_fp"].value,
                         "([+-]?\d*\.?\d+(?:[eE][-+]?\d+)?)")
        self.assertEqual(self.jube_pattern["jube_pat_nfp"].value,
                         "(?:[+-]?\d*\.?\d+(?:[eE][-+]?\d+)?)")
        self.assertEqual(self.jube_pattern["jube_pat_wrd"].value, "(\S+)")
        self.assertEqual(self.jube_pattern["jube_pat_nwrd"].value, "(?:\S+)")
        self.assertEqual(self.jube_pattern["jube_pat_bl"].value, "(?:\s+)")

if __name__ == "__main__":
    unittest.main()
