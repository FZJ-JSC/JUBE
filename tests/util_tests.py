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
        jube2.util.util.convert_type("int","3.141",stop=True)
        with self.assertRaises(ValueError):
            jube2.util.util.convert_type("int","forty-two",stop=True)
        self.assertEqual(jube2.util.util.convert_type("int","forty-two",stop=False),"forty-two")

    def test_expand_dollar_count(self):
        """Test expand_dollar_count"""
        test_text=[]
        test_result_text=[]

        test_text.append("echo -n $$PARAMNAME")
        test_result_text.append("echo -n $$$$PARAMNAME")
        test_text.append("echo -n $$$PARAMNAME")
        test_result_text.append("echo -n $$$PARAMNAME")
        test_text.append("echo -n $$$$PARAMNAME")
        test_result_text.append("echo -n $$$$$$$$PARAMNAME")
        test_text.append("echo -n $$$$$PARAMNAME")
        test_result_text.append("echo -n $$$$$$$PARAMNAME")

        test_text.append("$$PARAMNAME")
        test_result_text.append("$$$$PARAMNAME")
        test_text.append("$$$PARAMNAME")
        test_result_text.append("$$$PARAMNAME")
        test_text.append("$$$$PARAMNAME")
        test_result_text.append("$$$$$$$$PARAMNAME")
        test_text.append("$$$$$PARAMNAME")
        test_result_text.append("$$$$$$$PARAMNAME")

        test_text.append("42")
        test_result_text.append("42")

        test_text.append("echo $$")
        test_result_text.append("echo $$$$")

        for i in range(len(test_text)):
            self.assertEqual(jube2.util.util.expand_dollar_count(text=test_text[i]),test_result_text[i])

    def test_substitution(self):
        """Test substitution"""
        test_substitution_dict={'test1':'test2','test3':'test4'}
        test_text=[]
        test_result_text=[]

        test_text.append("echo -n $$$PARAMNAME")
        test_result_text.append("echo -n $PARAMNAME")
        test_text.append("echo -n $$$$PARAMNAME")
        test_result_text.append("echo -n $$PARAMNAME")
        test_text.append("echo -n $$$$$$$PARAMNAME")
        test_result_text.append("echo -n $$$PARAMNAME")
        test_text.append("echo -n $$$$$$$$PARAMNAME")
        test_result_text.append("echo -n $$$$PARAMNAME")

        test_text.append("$$$PARAMNAME")
        test_result_text.append("$PARAMNAME")
        test_text.append("$$$$PARAMNAME")
        test_result_text.append("$$PARAMNAME")
        test_text.append("$$$$$$$PARAMNAME")
        test_result_text.append("$$$PARAMNAME")
        test_text.append("$$$$$$$$PARAMNAME")
        test_result_text.append("$$$$PARAMNAME")

        test_text.append("42")
        test_result_text.append("42")

        test_text.append("echo $$")
        test_result_text.append("echo $$")

        test_text.append("$$")
        test_result_text.append("$$")

        for i in range(len(test_text)):
            self.assertEqual(jube2.util.util.substitution(text=test_text[i], substitution_dict=test_substitution_dict),test_result_text[i])

    def test_ensure_list(self):
        """Test ensure_list"""
        self.assertEqual(jube2.util.util.ensure_list(42),[42])
        self.assertEqual(type(jube2.util.util.ensure_list(42)),list)
        self.assertEqual(jube2.util.util.ensure_list(""),[""])
        self.assertEqual(type(jube2.util.util.ensure_list("")),list)
        self.assertEqual(jube2.util.util.ensure_list(["",42,3.141]),["",42,3.141])
        self.assertEqual(type(jube2.util.util.ensure_list(["",42,3.141])),list)


if __name__ == "__main__":
    unittest.main()
