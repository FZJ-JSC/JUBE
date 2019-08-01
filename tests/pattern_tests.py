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
"""Pattern related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import re

import unittest
import jube2.pattern


class TestPattern(unittest.TestCase):

    """Pattern test class"""

    def setUp(self):
        self.std_pattern = jube2.pattern.Pattern("std", ".*", unit="s", 
                                                 default="none")
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
        self.assertEqual(self.derived_pattern.default_value, None)
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
        self.assertEqual(etree.get("default"), "none")
        self.assertEqual(etree.tag, "pattern")
        self.assertEqual(etree.get("type"), "string")
        self.assertEqual(etree.get("mode"), "pattern")
        self.assertEqual(etree.text, ".*")
        etree = self.calculate_pattern.etree_repr()
        self.assertEqual(etree.get("mode"), "python")

    def test_jube_pattern(self):
        """Test JUBE internal pattern"""
        patterns = {
            name: self.jube_pattern[name].value for name in (
                "jube_pat_int", "jube_pat_nint", "jube_pat_fp", "jube_pat_nfp",
                "jube_pat_wrd", "jube_pat_nwrd", "jube_pat_bl")
        }

        for pattern, mystr, result in TEST_PATTERNS_EQUAL:
            findall = re.findall(pattern.format(**patterns), mystr)
            # If there is no match, set it to None
            if len(findall) == 0:
                findall = [None]
            match = findall[0]
            self.assertEqual(
                match, result, "'{pattern}' on '{mystr}' matches '{match}' "
                "and not '{result}'".format(**locals()))

class TestPatternset(unittest.TestCase):
    def setUp(self):
        self.patt_set = jube2.pattern.Patternset(name="test_set")
        self.patt_set2 = jube2.pattern.Patternset(name="test_set2")
        self.std_pattern = jube2.pattern.Pattern("std", ".*", unit="s", 
                                                 pattern_mode= "std")
        self.std_pattern2 = jube2.pattern.Pattern("std", ".*", unit="s")
        self.std_pattern3 = jube2.pattern.Pattern("std", ".*", unit="s", 
                                                 pattern_mode= "std")
        self.std_pattern4 = jube2.pattern.Pattern("std2", ".*", unit="s")
        
    def test_patt(self):
        #Test add_pattern
        self.assertEqual(self.patt_set.name, "test_set")
        self.assertTrue(self.std_pattern.derived)
        self.assertEqual(str(self.patt_set), str(self.patt_set2))
        self.assertEqual(self.patt_set['std'], None)
        self.patt_set.add_pattern(self.std_pattern)
        self.patt_set2.add_pattern(self.std_pattern2)
        self.assertEqual(str(self.patt_set2.get_incompatible_pattern(self.patt_set)), 'set()')
        
    def test_add(self):
        self.patt_set.add_pattern(self.std_pattern)
        self.assertEqual(str(self.patt_set.derived_pattern_storage), "Parameterset:{'std': '.*'}")
        self.patt_set.add_pattern(self.std_pattern2)
        self.assertEqual(str(self.patt_set.pattern_storage), "Parameterset:{'std': '.*'}")
        self.patt_set.add_pattern(self.std_pattern)
        self.assertEqual(str(self.patt_set.derived_pattern_storage), "Parameterset:{'std': '.*'}")
        self.patt_set3 = self.patt_set.copy()
        self.patt_set.add_patternset(self.patt_set2)
        self.assertTrue(self.patt_set.is_compatible(self.patt_set3))
        
    def test_etree_repr(self):
        self.patt_set.add_pattern(self.std_pattern3)
        self.patt_set.add_pattern(self.std_pattern4)
        etree_repr = self.patt_set.etree_repr()
        self.assertEqual(etree_repr.attrib['name'], 'test_set')
        self.assertEqual(len(etree_repr), 2)
        self.assertEqual(etree_repr[0].attrib['name'], 'std2')
        self.assertEqual(etree_repr[1].attrib['name'], 'std')
        

TEST_PATTERNS_FULL = [
    # Simple patterns with full match
    (pat, mystr, mystr) for pat, mystr in (
        (r"^{jube_pat_int}$", "1"),
        (r"^{jube_pat_int}$", "123"),
        (r"^{jube_pat_int}$", "+123"),
        (r"^{jube_pat_int}$", "-123"),
        (r"^{jube_pat_fp}$", "1"),
        (r"^{jube_pat_fp}$", "12"),
        (r"^{jube_pat_fp}$", ".1"),
        (r"^{jube_pat_fp}$", ".12"),
        (r"^{jube_pat_fp}$", "1."),
        (r"^{jube_pat_fp}$", "12."),
        (r"^{jube_pat_fp}$", "12.34"),
        (r"^{jube_pat_fp}$", "+12.34"),
        (r"^{jube_pat_fp}$", "-12.34"),
        (r"^{jube_pat_fp}$", "-12.34e1"),
        (r"^{jube_pat_fp}$", "-12.34E-5"),
        (r"^{jube_pat_fp}$", "-12.34E+56"),
        (r"^{jube_pat_wrd}$", "jube"),
        (r"^{jube_pat_wrd}$", "jube2"),
        (r"^{jube_pat_bl}$", "  "),
    )
]

TEST_PATTERNS_EQUAL = TEST_PATTERNS_FULL + [
    # Simple patterns that do not match
    (r"^{jube_pat_int}$", "1.2", None),
    (r"^{jube_pat_fp}$", "12x3", None),
    (r"^{jube_pat_fp}$", "+-12.34", None),
    (r"^{jube_pat_fp}$", "-12.34e", None),
    (r"^{jube_pat_wrd}$", "jube 2", None),
    # More complex patterns
    (r"^{jube_pat_int} {jube_pat_nint} {jube_pat_int}$", "1 2 3", ("1", "3")),
    (r"^{jube_pat_fp} {jube_pat_nfp} {jube_pat_fp}$", "1 2 3", ("1", "3")),
    (r"^{jube_pat_wrd} {jube_pat_nwrd} {jube_pat_wrd}$", "1 2 3", ("1", "3")),
    (r"^{jube_pat_wrd}{jube_pat_bl}{jube_pat_wrd}$", "jube 2", ("jube", "2")),
]


if __name__ == "__main__":
    unittest.main()
