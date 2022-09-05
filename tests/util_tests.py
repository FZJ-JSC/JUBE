#!/usr/bin/env python3
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
import jube2.step


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

    def test_resolve_prepares(self):

        steps={}
        steps['step1'] = jube2.step.Step(name='step1', depend=set(), prepare=set(['step2','step3']))
        steps['step2'] = jube2.step.Step(name='step2', depend=set(), prepare=set(['step3']))
        steps['step3'] = jube2.step.Step(name='step3', depend=set(), prepare=set())

        jube2.util.util.resolve_prepares(steps)

        self.assertEqual(steps['step1']._prepare,set(['step2','step3']))
        self.assertEqual(steps['step2']._prepare,set(['step3']))
        self.assertEqual(steps['step3']._prepare,set())
        self.assertEqual(steps['step1']._depend,set())
        self.assertEqual(steps['step2']._depend,set(['step1']))
        self.assertEqual(steps['step3']._depend,set(['step1','step2']))

        steps['step4'] = jube2.step.Step(name='step4', depend=set(), prepare=set(['step4']))

        with self.assertRaises(ValueError):
            jube2.util.util.resolve_prepares(steps)

        steps['step3'] = jube2.step.Step(name='step3', depend=set(), prepare=set(['step4']))
        steps['step4'] = jube2.step.Step(name='step4', depend=set(), prepare=set(['step1']))

        with self.assertRaises(ValueError):
            jube2.util.util.resolve_prepares(steps)

        steps['step4'] = jube2.step.Step(name='step4', depend=set(), prepare=set(['step5']))

        self.assertTrue("step4" in steps.keys())
        self.assertTrue("step5" not in steps.keys())
        steps=jube2.util.util.resolve_prepares(steps)
        self.assertTrue("step4" not in steps.keys())
        self.assertTrue("step5" not in steps.keys())


if __name__ == "__main__":
    unittest.main()
