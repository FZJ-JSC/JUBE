#!/usr/bin/env python
# JUBE Benchmarking Environment
# Copyright (C) 2008-2014
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
"""Testing routines"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import jube2.parameter


class TestParameter(unittest.TestCase):
    """Parameter test class"""
    def test_constant(self):
        """Test Constants"""
        parameter = jube2.parameter.Parameter.create_parameter("test", "2")
        self.assertEqual(parameter.value, "2")
        self.assertFalse(parameter.is_template)

    def test_template(self):
        """Test Template"""
        values = ["2", "3", "4"]
        parameter = jube2.parameter.Parameter.create_parameter("test", "2,3,4")
        self.assertTrue(parameter.is_template)
        self.assertEqual(parameter.value, "2,3,4")

        # Template become constant check
        for idx, static_par in enumerate(parameter.expand()):
            self.assertEqual(static_par.value, values[idx])
            self.assertFalse(static_par.is_template)
            self.assertTrue(static_par.is_equivalent(parameter))

        # Copy check
        parameter2 = parameter.copy()
        self.assertFalse(parameter2 is parameter)
        self.assertTrue(parameter2.is_equivalent(parameter))

        # Equivalent check
        parameter2 = jube2.parameter.Parameter.create_parameter("test", "3")
        self.assertFalse(parameter2.is_equivalent(parameter))
        parameter2 = jube2.parameter.Parameter.create_parameter("test",
                                                                "2,3,4")
        self.assertTrue(parameter2.is_equivalent(parameter))

        # Etree repr check
        etree = parameter.etree_repr()
        self.assertEqual(etree.tag, "parameter")
        self.assertEqual(etree.get("separator"), ",")
        self.assertEqual(etree.get("type"), "string")
        self.assertEqual(etree.text, "2,3,4")

        etree = static_par.etree_repr(use_current_selection=True)
        self.assertEqual(etree.text, "2,3,4")
        self.assertEqual(etree.get("selection"), "4")


class TestParameterSet(unittest.TestCase):
    """ParameterSet test class"""
    def test_set(self):
        # Test add parameter to set
        parameterset = jube2.parameter.Parameterset("test")
        parameter = jube2.parameter.Parameter.create_parameter("test", "2")
        parameter2 = jube2.parameter.Parameter.create_parameter("test2",
                                                                "2,3,4")
        parameterset.add_parameter(parameter)
        parameterset.add_parameter(parameter2)
        self.assertTrue(parameter in parameterset)
        self.assertTrue((["test", "test2"] ==
                         sorted(parameterset.all_parameter_names)))
        constant_dict = parameterset.constant_parameter_dict
        self.assertTrue("test" in constant_dict)
        self.assertFalse("test2" in constant_dict)
        template_dict = parameterset.template_parameter_dict
        self.assertFalse("test" in template_dict)
        self.assertTrue("test2" in template_dict)

        # Test not compatible parameterset
        parameterset2 = jube2.parameter.Parameterset("test2")
        parameter3 = jube2.parameter.Parameter.create_parameter("test3", "5")
        parameter4 = jube2.parameter.Parameter.create_parameter("test2", "4")
        parameterset2.add_parameter(parameter3)
        parameterset2.add_parameter(parameter4)
        self.assertFalse(parameterset.is_compatible(parameterset2))

        # Test clear
        self.assertEqual(len(parameterset2), 2)
        parameterset2.clear()
        self.assertEqual(len(parameterset2), 0)

        # Test compatible parameterset
        parameterset2.add_parameter(parameter3)
        parameter4 = jube2.parameter.Parameter.create_parameter("test2",
                                                                "2,3,4")
        for static_par in parameter4.expand():
            parameterset2.add_parameter(static_par)
        self.assertTrue(parameterset.is_compatible(parameterset2))

        # Test update_parameterset
        parameterset.update_parameterset(parameterset2)
        self.assertEqual(parameterset.template_parameter_dict, dict())
        self.assertEqual(len(parameterset), 2)

        # Test add_parameterset
        parameterset.add_parameterset(parameterset2)
        self.assertEqual(len(parameterset), 3)

        # Check parameterset expand_templates
        parameterset.add_parameter(parameter2)
        self.assertTrue("test2" in parameterset.template_parameter_dict)
        param_list = ["2", "3", "4"]
        for idx, new_parameterset in \
            enumerate(parameterset.expand_templates()):
            self.assertEqual(new_parameterset.template_parameter_dict, dict())
            self.assertEqual(new_parameterset["test2"].value, param_list[idx])

        # Substitution and evaluation check
        parameter_sub = \
            jube2.parameter.Parameter.create_parameter("test4", "$test2")
        parameter_eval = \
            jube2.parameter.Parameter.create_parameter("test5",
                                                       "${test4} * 2",
                                                       parameter_mode="python")
        parameterset.add_parameter(parameter_sub)
        parameterset.add_parameter(parameter_eval)
        self.assertFalse(
            parameter_sub.can_substitute_and_evaluate(parameterset))
        for idx, new_parameterset in \
            enumerate(parameterset.expand_templates()):
            self.assertTrue(
                parameter_sub.can_substitute_and_evaluate(new_parameterset))
            new_parameterset.parameter_substitution()
            self.assertEqual(new_parameterset["test4"].value, param_list[idx])
            self.assertEqual(new_parameterset["test5"].value,
                              str(int(param_list[idx]) * 2))

        # Etree repr check
        etree = parameterset.etree_repr()
        self.assertEqual(etree.tag, "parameterset")
        self.assertEqual(len(etree.findall("parameter")), 5)


if __name__ == "__main__":
    unittest.main()
