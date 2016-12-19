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
"""Patternset definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import jube2.parameter
import xml.etree.ElementTree as ET

LOGGER = jube2.log.get_logger(__name__)


class Patternset(object):

    """A Patternset stores a set of pattern and derived pattern."""

    def __init__(self, name=""):
        self._name = name
        self._pattern = jube2.parameter.Parameterset("pattern")
        self._derived_pattern = jube2.parameter.Parameterset("derived_pattern")

    def add_pattern(self, pattern):
        """Add a additional pattern to the patternset. Existing pattern using
        the same name will be overwritten"""
        if pattern.derived:
            if pattern in self._pattern:
                self._pattern.delete_parameter(pattern)
            self._derived_pattern.add_parameter(pattern)
        else:
            if pattern in self._derived_pattern:
                self._derived_pattern.delete_parameter(pattern)
            self._pattern.add_parameter(pattern)

    @property
    def pattern_storage(self):
        """Return the pattern storage"""
        return self._pattern

    @property
    def derived_pattern_storage(self):
        """Return the derived pattern storage"""
        return self._derived_pattern

    def etree_repr(self):
        """Return etree object representation"""
        patternset_etree = ET.Element('patternset')
        patternset_etree.attrib["name"] = self._name
        for pattern in self._pattern:
            patternset_etree.append(
                pattern.etree_repr())
        for pattern in self._derived_pattern:
            patternset_etree.append(
                pattern.etree_repr())
        return patternset_etree

    def add_patternset(self, patternset):
        """Add all pattern from given patternset to the current one"""
        self._pattern.add_parameterset(patternset.pattern_storage)
        self._derived_pattern.add_parameterset(
            patternset.derived_pattern_storage)

    def pattern_substitution(self, parametersets=None):
        """Run pattern substitution using additional parameterset"""
        if parametersets is None:
            parametersets = list()
        self._pattern.parameter_substitution(
            additional_parametersets=parametersets,
            final_sub=True)

    def derived_pattern_substitution(self, parametersets=None):
        """Run derived pattern substitution using additional parameterset"""
        if parametersets is None:
            parametersets = list()
        self._derived_pattern.parameter_substitution(
            additional_parametersets=parametersets,
            final_sub=True)

    @property
    def name(self):
        """Get patternset name"""
        return self._name

    def copy(self):
        """Returns a copy of the Parameterset"""
        new_patternset = Patternset(self._name)
        new_patternset.add_patternset(self)
        return new_patternset

    def is_compatible(self, patternset):
        """Two Patternsets are compatible, if all pattern storages are
        compatible"""
        return self.pattern_storage.is_compatible(
            patternset.pattern_storage) and \
            self.pattern_storage.is_compatible(
                patternset.derived_pattern_storage) and \
            self.derived_pattern_storage.is_compatible(
                patternset.derived_pattern_storage) and \
            self.derived_pattern_storage.is_compatible(
                patternset.pattern_storage)

    def get_incompatible_pattern(self, patternset):
        """Return a set of incompatible pattern names between the current
        and the given parameterset"""
        result = set()
        result.update(self.pattern_storage.get_incompatible_parameter(
            patternset.pattern_storage))
        result.update(self.pattern_storage.get_incompatible_parameter(
            patternset.derived_pattern_storage))
        result.update(self.derived_pattern_storage.get_incompatible_parameter(
            patternset.pattern_storage))
        result.update(self.derived_pattern_storage.get_incompatible_parameter(
            patternset.derived_pattern_storage))

        return result

    def __repr__(self):
        return "Patternset: pattern:{0} derived pattern:{1}".format(
            dict([[pattern.name, pattern.value]
                  for pattern in self._pattern]),
            dict([[pattern.name, pattern.value]
                  for pattern in self._derived_pattern]))

    def __contains__(self, pattern):
        if isinstance(pattern, Pattern):
            if pattern.name in self._pattern:
                return pattern.is_equivalent(
                    self._pattern[pattern.name])
            elif pattern.name in self._derived_pattern:
                return pattern.is_equivalent(
                    self._derived_pattern[pattern.name])
            else:
                return False
        else:
            return (pattern in self._pattern) or \
                   (pattern in self._derived_pattern)

    def __getitem__(self, name):
        """Returns pattern given by name. Is pattern not found, None will
        be returned"""
        if name in self._pattern:
            return self._pattern[name]
        elif name in self._derived_pattern:
            return self._derived_pattern[name]
        else:
            return None


class Pattern(jube2.parameter.StaticParameter):

    """A pattern can be used to scan a result file, using regular expression,
    or to represent a derived pattern."""

    def __init__(self, name, value, pattern_mode="pattern",
                 content_type="string", unit="", default=None):
        self._derived = pattern_mode != "pattern"

        if not self._derived:
            pattern_mode = "text"

        self._default = default

        # Unicode conversion
        value = "" + value

        jube2.parameter.StaticParameter.__init__(
            self, name, value, parameter_type=content_type,
            parameter_mode=pattern_mode)

        self._unit = unit

    @property
    def derived(self):
        """pattern is a derived pattern"""
        return self._derived

    @property
    def content_type(self):
        """Return pattern type"""
        return self._type

    @property
    def default_value(self):
        """Return pattern default value"""
        return self._default

    @property
    def unit(self):
        """Return unit"""
        return self._unit

    def substitute_and_evaluate(self, parametersets=None,
                                final_sub=False, no_templates=True,
                                force_evaluation=False):
        """Substitute all variables inside the pattern value by using the
        parameter inside the given parameterset and additional_parameterset.
        final_sub marks the last substitution.

        Return the new pattern and a boolean value which represent a change
        of value
        """
        try:
            param, changed = \
                jube2.parameter.StaticParameter.substitute_and_evaluate(
                    self, parametersets, final_sub, no_templates,
                    force_evaluation)
        except RuntimeError as re:
            LOGGER.debug(str(re).replace("parameter", "pattern"))
            if self._default is not None:
                value = self._default
            elif self._type in ["int", "float"]:
                value = "nan"
            else:
                value = ""
            pattern = Pattern(
                self._name, value, "text", self._type, self._unit)
            pattern.based_on = self
            return pattern, True

        if changed:
            # Convert parameter to pattern
            if not self.derived:
                pattern_mode = "pattern"
            else:
                pattern_mode = param.mode
            pattern = Pattern(param.name, param.value, pattern_mode,
                              param.parameter_type, self._unit)
            pattern.based_on = param.based_on
        else:
            pattern = param
        return pattern, changed

    def etree_repr(self, use_current_selection=False):
        """Return etree object representation"""
        pattern_etree = ET.Element('pattern')
        pattern_etree.attrib["name"] = self._name
        pattern_etree.attrib["type"] = self._type
        if self._default is not None:
            pattern_etree.attrib["default"] = self._default
        if not self._derived:
            pattern_etree.attrib["mode"] = "pattern"
        else:
            pattern_etree.attrib["mode"] = self._mode

        if self._unit != "":
            pattern_etree.attrib["unit"] = self._unit
        pattern_etree.text = self.value
        return pattern_etree

    def __repr__(self):
        return "Pattern({0})".format(self.__dict__)


def get_jube_pattern():
    """Return jube internal patternset"""
    patternset = Patternset()
    # Pattern for integer number
    patternset.add_pattern(Pattern("jube_pat_int", r"([+-]?\d+)"))
    # Pattern for integer number, no ()
    patternset.add_pattern(Pattern("jube_pat_nint", r"(?:[+-]?\d+)"))
    # Pattern for floating point number
    patternset.add_pattern(
        Pattern("jube_pat_fp", r"([+-]?\d*\.?\d+(?:[eE][-+]?\d+)?)"))
    # Pattern for floating point number, no ()
    patternset.add_pattern(
        Pattern("jube_pat_nfp", r"(?:[+-]?\d*\.?\d+(?:[eE][-+]?\d+)?)"))
    # Pattern for word (all noblank characters)
    patternset.add_pattern(Pattern("jube_pat_wrd", r"(\S+)"))
    # Pattern for word (all noblank characters), no ()
    patternset.add_pattern(Pattern("jube_pat_nwrd", r"(?:\S+)"))
    # Pattern for blank space (variable length)
    patternset.add_pattern(Pattern("jube_pat_bl", r"(?:\s+)"))
    return patternset
