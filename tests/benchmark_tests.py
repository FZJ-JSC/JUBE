"""Nose-test routines"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import jube2.parameter


def test_parameter():
    """Check parameter class"""
    # Constant check
    parameter = jube2.parameter.Parameter.create_parameter("test", "2")
    assert parameter.value == "2"
    assert not parameter.is_template
    # Template check
    values = ["2", "3", "4"]
    parameter = jube2.parameter.Parameter.create_parameter("test", "2,3,4")
    assert parameter.is_template
    assert parameter.value == "2,3,4"
    # Template become constant check
    for i, static_par in enumerate(parameter.expand()):
        assert static_par.value == values[i]
        assert not static_par.is_template
        assert static_par.is_equivalent(parameter)
    # Copy check
    parameter2 = parameter.copy()
    assert parameter2 is not parameter
    assert parameter2.is_equivalent(parameter)
    # Equivalent check
    parameter2 = jube2.parameter.Parameter.create_parameter("test", "3")
    assert not parameter2.is_equivalent(parameter)
    parameter2 = jube2.parameter.Parameter.create_parameter("test", "2,3,4")
    assert parameter2.is_equivalent(parameter)
    # Etree repr check
    etree = parameter.etree_repr()
    assert etree.tag == "parameter"
    assert etree.get("separator") == ","
    assert etree.get("type") == "string"
    assert etree.text == "2,3,4"
    etree = static_par.etree_repr(use_current_selection=True)
    assert etree.text == "2,3,4"
    assert etree.get("selection") == "4"


def test_parameterset():
    """Check parameterset class"""
    # Test add parameter to set
    parameterset = jube2.parameter.Parameterset("test")
    parameter = jube2.parameter.Parameter.create_parameter("test", "2")
    parameter2 = jube2.parameter.Parameter.create_parameter("test2", "2,3,4")
    parameterset.add_parameter(parameter)
    parameterset.add_parameter(parameter2)
    assert parameter in parameterset
    assert ("test" in parameterset.all_parameter_names) and \
           ("test2" in parameterset.all_parameter_names)
    constant_dict = parameterset.constant_parameter_dict
    assert "test" in constant_dict
    assert "test2" not in constant_dict
    constant_dict = parameterset.template_parameter_dict
    assert "test" not in constant_dict
    assert "test2" in constant_dict
    # Test not compatible parameterset
    parameterset2 = jube2.parameter.Parameterset("test2")
    parameter3 = jube2.parameter.Parameter.create_parameter("test3", "5")
    parameter4 = jube2.parameter.Parameter.create_parameter("test2", "4")
    parameterset2.add_parameter(parameter3)
    parameterset2.add_parameter(parameter4)
    assert not parameterset.is_compatible(parameterset2)
    # Test clear
    assert len(parameterset2) == 2
    parameterset2.clear()
    assert len(parameterset2) == 0
    # Test compatible parameterset
    parameterset2.add_parameter(parameter3)
    parameter4 = jube2.parameter.Parameter.create_parameter("test2", "2,3,4")
    for static_par in parameter4.expand():
        parameterset2.add_parameter(static_par)
    assert parameterset.is_compatible(parameterset2)
    # Test update_parameterset
    parameterset.update_parameterset(parameterset2)
    assert parameterset.template_parameter_dict == {}
    assert len(parameterset) == 2
    # Test add_parameterset
    parameterset.add_parameterset(parameterset2)
    assert len(parameterset) == 3
    # Check parameterset expand_templates
    parameterset.add_parameter(parameter2)
    assert "test2" in parameterset.template_parameter_dict
    param_list = ["2", "3", "4"]
    for i, new_parameterset in enumerate(parameterset.expand_templates()):
        assert new_parameterset.template_parameter_dict == {}
        assert new_parameterset["test2"].value == param_list[i]
    # Substitution and evaluation check
    parameter_sub = \
        jube2.parameter.Parameter.create_parameter("test4", "$test2")
    parameter_eval = \
        jube2.parameter.Parameter.create_parameter("test5",
                                                   "${test4} * 2",
                                                   parameter_mode="python")
    parameterset.add_parameter(parameter_sub)
    parameterset.add_parameter(parameter_eval)
    assert not parameter_sub.can_substitute_and_evaluate(parameterset)
    for i, new_parameterset in enumerate(parameterset.expand_templates()):
        assert parameter_sub.can_substitute_and_evaluate(new_parameterset)
        new_parameterset.parameter_substitution()
        assert new_parameterset["test4"].value == param_list[i]
        assert new_parameterset["test5"].value == str(int(param_list[i]) * 2)
    # Etree repr check
    etree = parameterset.etree_repr()
    assert etree.tag == "parameterset"
    assert len(etree.findall("parameter")) == 5
