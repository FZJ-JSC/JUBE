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
"""Parameter related classes"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import itertools
import xml.etree.ElementTree as ET
import copy
import jube2.util
import jube2.conf
import jube2.log
import re

LOGGER = jube2.log.get_logger(__name__)


class Parameterset(object):

    """A parameterset represent a template or a specific product space. It
    cann combined with other Parametersets."""

    def __init__(self, name=""):
        self._name = name
        self._parameters = dict()

    def clear(self):
        """Remove all stored parameters"""
        self._parameters = dict()

    def copy(self):
        """Returns a deepcopy of the Parameterset"""
        new_parameterset = Parameterset(self._name)
        new_parameterset.add_parameterset(self)
        return new_parameterset

    @property
    def name(self):
        """Return name of the Parameterset"""
        return self._name

    @property
    def has_templates(self):
        """This Parameterset contains template paramters?"""
        for parameter in self._parameters.values():
            if parameter.is_template:
                return True
        return False

    @property
    def parameter_dict(self):
        """Return dictionary name -> parameter"""
        return dict(self._parameters)

    @property
    def all_parameters(self):
        """Return list of all parameters"""
        return self._parameters.values()

    @property
    def all_parameter_names(self):
        """Return list of all parameter names"""
        return self._parameters.keys()

    def add_parameterset(self, parameterset):
        """Add all parameters from given parameterset, existing ones will
        be overwritten"""
        for parameter in parameterset:
            self.add_parameter(parameter.copy())
        return self

    def update_parameterset(self, parameterset):
        """Overwrite existing parameters. Don't add new parameters"""
        for parameter in parameterset:
            if parameter in self:
                self._parameters[parameter.name] = parameter.copy()

    def add_parameter(self, parameter):
        """Add a new parameter"""
        self._parameters[parameter.name] = parameter

    def delete_parameter(self, parameter):
        """Delete a parameter"""
        name = ""
        if isinstance(parameter, Parameter):
            name = parameter.name
        else:
            name = parameter
        if name in self._parameters:
            del self._parameters[name]

    @property
    def constant_parameter_dict(self):
        """Return dictionary representation of all constant parameters"""
        return dict([(parameter.name, parameter)
                     for parameter in self._parameters.values()
                     if not parameter.is_template])

    @property
    def template_parameter_dict(self):
        """Return dictionary representation of all template parameters"""
        return dict([(parameter.name, parameter)
                     for parameter in self._parameters.values()
                     if parameter.is_template])

    @property
    def export_parameter_dict(self):
        """Return dictionary representation of all export parameters"""
        return dict([(parameter.name, parameter)
                     for parameter in self._parameters.values()
                     if (not parameter.is_template) and parameter.export])

    def is_compatible(self, parameterset):
        """Two Parametersets are compatible, if the intersection only contains
        equivilant parameters"""
        # Find parameternames which exists in both parametersets
        intersection = set(self.all_parameter_names) & \
            set(parameterset.all_parameter_names)
        for name in intersection:
            if not self[name].is_equivalent(parameterset[name]):
                return False
        return True

    def get_incompatible_parameter(self, parameterset):
        """Return a set of incompatible parameter names between the current
        and the given parameterset"""
        result = set()
        intersection = set(self.all_parameter_names) & \
            set(parameterset.all_parameter_names)
        for name in intersection:
            if not self[name].is_equivalent(parameterset[name]):
                result.add(name)
        return result

    def expand_templates(self):
        """Expand all remaining templates in the Parameterset and returns the
        resulting parametersets
        """
        parameter_list = list()
        # Create all possible constant parameter representations
        for parameter in self.template_parameter_dict.values():
            expanded_parameter_list = list()
            for static_param in parameter.expand():
                expanded_parameter_list.append(static_param)
            parameter_list.append(expanded_parameter_list)
        # Generator
        for parameters in itertools.product(*parameter_list):
            parameterset = self.copy()
            # Addition of the constant parameters will overwrite the templates
            for parameter in parameters:
                parameterset.add_parameter(parameter)
            yield parameterset

    def __contains__(self, parameter):
        if isinstance(parameter, Parameter):
            if parameter.name in self._parameters:
                return parameter.is_equivalent(
                    self._parameters[parameter.name])
            else:
                return False
        else:
            return parameter in self._parameters

    def __getitem__(self, name):
        if name in self._parameters:
            return self._parameters[name]
        else:
            return None

    def __iter__(self):
        for parameter in self.all_parameters:
            yield parameter

    def etree_repr(self, use_current_selection=False):
        """Return etree object representation"""
        parameterset_etree = ET.Element('parameterset')
        if len(self._name) > 0:
            parameterset_etree.attrib["name"] = self._name
        for parameter in self._parameters.values():
            parameterset_etree.append(
                parameter.etree_repr(use_current_selection))
        return parameterset_etree

    def __len__(self):
        return len(self._parameters)

    def __repr__(self):
        return "Parameterset:{0}".format(
            dict([[parameter.name, parameter.value]
                  for parameter in self.all_parameters]))

    def parameter_substitution(self, additional_parametersets=None,
                               final_sub=False):
        """Substitute all parameter inside the parameterset. Parameters from
        additional_parameterset will be used for substitution but will not be
        added to the set. final_sub marks the last substitution process."""
        set_changed = True
        max_count = jube2.conf.MAX_RECURSIVE_SUB
        while set_changed and (not self.has_templates) and (max_count > 0):
            set_changed = False
            max_count -= 1

            # Create dependencies
            depend_dict = dict()
            for par in self:
                if not par.is_template:
                    depend_dict[par.name] = set()
                    for other_par in self:
                        # search for parameter usage
                        if par.depends_on(other_par):
                            depend_dict[par.name].add(other_par.name)

            # Resolve dependencies
            substitution_list = [self._parameters[name] for name in
                                 jube2.util.resolve_depend(depend_dict)]

            # Do substition and evaluation if possible
            for par in substitution_list:
                if par.can_substitute_and_evaluate(self):
                    parametersets = [self]
                    if additional_parametersets is not None:
                        parametersets += additional_parametersets
                    new_par, param_changed = \
                        par.substitute_and_evaluate(parametersets)
                    set_changed = set_changed or param_changed
                    if param_changed:
                        self.add_parameter(new_par)

        if final_sub:
            parameter = [par for par in self]
            for par in parameter:
                if par.is_template:
                    LOGGER.debug(
                        ("Parameter ${0} = {1} is handled as " +
                         "a template and will not be evaluated.\n").format(
                            par.name, par.value))
                else:
                    new_par, param_changed = \
                        par.substitute_and_evaluate(final_sub=True)
                    if param_changed:
                        self.add_parameter(new_par)


class Parameter(object):

    """Contains data for single Parameter. This Parameter can be a constant
    value, a template or a specific value out of a given template"""

    # This regex can be used to find variables inside parameter values
    parameter_regex = r"(?<!\$)(?:\$\$)*\$(?!\$)(\{{)?{0}(?(1)\}}|(?=\W|$))"

    def __init__(self, name, value, separator=None, parameter_type="string",
                 parameter_mode="text", export=False):
        self._name = name
        self._value = value
        if separator is None:
            self._separator = jube2.conf.DEFAULT_SEPARATOR
        else:
            self._separator = separator
        self._type = parameter_type
        self._mode = parameter_mode
        self._based_on = None
        self._export = export
        self._lvl = 0

    @staticmethod
    def create_parameter(name, value, separator=None, parameter_type="string",
                         selected_value=None, parameter_mode="text",
                         export=False, no_templates=False):
        """Parameter constructor.
        Return a Static- or TemplateParameter based on the given data."""
        if separator is None:
            sep = jube2.conf.DEFAULT_SEPARATOR
        else:
            sep = separator

        # Unicode conversion
        value = "" + value

        # Check weather a new template should be created or not
        if no_templates:
            values = [value]
        else:
            values = [val.strip() for val in value.split(sep)]

        if len(values) == 1 or \
           (parameter_mode in jube2.conf.ALLOWED_SCRIPTTYPES):
            result = StaticParameter(name, value, separator, parameter_type,
                                     parameter_mode, export)
        else:
            result = TemplateParameter(name, values, separator, parameter_type,
                                       parameter_mode, export)

        if selected_value is not None:
            tmp = result
            parameter_mode = "text"
            result = StaticParameter(name, selected_value, separator,
                                     parameter_type, parameter_mode, export)
            result.based_on = tmp
        return result

    def copy(self):
        """Returns Parameter copy (flat copy)"""
        return copy.copy(self)

    @property
    def name(self):
        """Returns the Parameter name"""
        return self._name

    @property
    def lvl(self):
        """Return the Parameter level"""
        return self._lvl

    @property
    def export(self):
        """Return if parameter should be exported"""
        return self._export

    @property
    def mode(self):
        """Return parameter mode"""
        return self._mode

    @property
    def value(self):
        """Return parameter value"""
        return self._value

    @property
    def based_on(self):
        """The base of the current Parameter"""
        return self._based_on

    @based_on.setter
    def based_on(self, parameter):
        """The Parameter based on another one"""
        self._based_on = parameter
        self._lvl = parameter.lvl + 1

    @property
    def based_on_mode(self):
        """Return the root parameter mode inside the based_on graph"""
        if self._based_on is None:
            return self._mode
        else:
            return self._based_on.based_on_mode

    @property
    def based_on_value(self):
        """Return the root value inside the based_on graph"""
        if self._based_on is None:
            return self.value
        else:
            return self._based_on.based_on_value

    @property
    def is_template(self):
        """Return whether the parameter is a template"""
        return isinstance(self, TemplateParameter)

    @property
    def parameter_type(self):
        """Return parametertype"""
        return self._type

    def is_equivalent(self, parameter):
        """Checks whether the given and the current Parament based on
        equivalent templates or equivalent scripts."""
        if self._lvl == parameter.lvl:
            result = self.value == parameter.value
        else:
            result = True
        if (self._based_on is not None) or (parameter.based_on is not None):
            if (self._based_on is not None) and \
               (self._lvl >= parameter.lvl):
                self_based_on = self._based_on
            else:
                self_based_on = self
            if (parameter.based_on is not None) and \
               (self._lvl <= parameter.lvl):
                other_based_on = parameter.based_on
            else:
                other_based_on = parameter
            result = result and self_based_on.is_equivalent(other_based_on)
        return result

    def etree_repr(self, use_current_selection=False):
        """Return etree object representation"""
        parameter_etree = ET.Element('parameter')
        parameter_etree.attrib["name"] = self._name

        parameter_etree.attrib["type"] = self._type
        parameter_etree.attrib["separator"] = self._separator
        parameter_etree.text = self.based_on_value
        if use_current_selection and (parameter_etree.text != self.value):
            parameter_etree.attrib["mode"] = self.based_on_mode
            parameter_etree.attrib["selection"] = self.value
        else:
            parameter_etree.attrib["mode"] = self._mode
        if self._export:
            parameter_etree.attrib["export"] = "true"

        return parameter_etree

    def __repr__(self):
        return "Parameter({0})".format(self.__dict__)


class StaticParameter(Parameter):

    """A StaticParameter can be substituted and evaluated."""

    def can_substitute_and_evaluate(self, parameterset):
        """A parameter can be substituted and evaluated if there are no
        depending templates or unevaluated parameter inside"""
        param_names = \
            [found[1] for found in
             re.findall(Parameter.parameter_regex.format("(.+?)"),
                        self._value)]
        return all([(param_name not in parameterset) or
                    ((not parameterset[param_name].is_template) and
                     (not parameterset[param_name].mode in
                      jube2.conf.ALLOWED_SCRIPTTYPES))
                    for param_name in param_names])

    def depends_on(self, parameter):
        """Checks the parameter depends on an other parameter."""
        return bool(
            re.search(Parameter.parameter_regex.format(parameter.name),
                      self._value))

    def substitute_and_evaluate(self, parametersets=None,
                                final_sub=False, no_templates=False):
        """Substitute all variables inside the parameter value by using the
        parameters inside the given parameterset and additional_parameterset.
        final_sub marks the last substitution.

        Return the new parameter and a boolean value which represent a change
        of value
        """
        value = self._value
        if not final_sub:
            # Replace a even number of $ by $$$$, because they will be
            # substituted to $$. Even number will stay the same, odd number
            # will shrink in every turn
            # $$ -> $$$$ -> $$
            # $$$ -> $$$ -> $
            # $$$$ -> $$$$$$$$ -> $$$$
            # $$$$$ -> $$$$$$$ -> $$$
            value = re.sub(r"(\$\$)(?=(\$\$|[^$]))", "$$$$", value)
        parameter_dict = dict()
        if parametersets is not None:
            for parameterset in parametersets:
                parameter_dict.update(
                    dict([(name, param.value) for name, param in
                          parameterset.constant_parameter_dict.items()]))
        value = jube2.util.substitution(value, parameter_dict)
        # Run parameter evaluation, if value is fully expanded and
        # Parameter is a script
        mode = self._mode
        if ((not re.search(
            Parameter.parameter_regex.format("(.+?)"), value)) or
                final_sub) and (self._mode in jube2.conf.ALLOWED_SCRIPTTYPES):
            try:
                # Run additional substitution to remove $$ before running
                # script evaluation to allow usage of environment variables
                if not final_sub:
                    value = jube2.util.substitution(value, parameter_dict)
                # Run script evaluation
                value = jube2.util.script_evaluation(value, self._mode)
                # Insert new $$ if needed
                if not final_sub:
                    value = re.sub(r"\$", "$$", value)
                # Select new parameter mode
                mode = "text"
            except Exception as exception:
                raise RuntimeError(("Can not evaluate \"{0}\" for " +
                                    "parameter \"{1}\": {2}").format(
                    value, self.name, str(exception)))
        changed = value != self._value

        if changed:
            param = Parameter.create_parameter(name=self._name,
                                               value=value,
                                               separator=self._separator,
                                               parameter_type=self._type,
                                               parameter_mode=mode,
                                               export=self._export,
                                               no_templates=no_templates)
            param.based_on = self
        else:
            param = self
        return param, changed


class TemplateParameter(Parameter):

    """A TemplateParameter represent a set of possible parameter values,
    which can be accessed by a single name. To use the template in a specific
    environment, it must be expanded."""

    @property
    def value(self):
        """Return Template values"""
        return self._separator.join(self._value)

    def expand(self):
        """Expand Template and produce set of static parameter"""
        for index in range(len(self._value)):
            value = self._value[index]
            static_param = StaticParameter(name=self._name,
                                           value=value,
                                           separator=self._separator,
                                           parameter_type=self._type,
                                           export=self._export)
            static_param.based_on = self
            yield static_param
