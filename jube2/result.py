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
"""Resulttype definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import jube2.util
import xml.etree.ElementTree as ET
import re
import jube2.log

LOGGER = jube2.log.get_logger(__name__)


class Result(object):

    """A generic result type"""

    class ResultData(object):

        """A gerneric result data type"""

        def __init__(self, name):
            self._name = name

        @property
        def name(self):
            """Return the result name"""
            return self._name

        def create_result(self, show=True, filename=None, **kwargs):
            """Create result output"""
            raise NotImplementedError("")

        def add_result_data(self, result_data):
            """Add additional result data"""
            raise NotImplementedError("")

        def __eq__(self, other):
            return self.name == other.name

    def __init__(self, name, res_filter=None):
        self._use = set()
        self._name = name
        self._res_filter = res_filter
        self._result_dir = None
        self._benchmark = None

    @property
    def name(self):
        """Return the result name"""
        return self._name

    @property
    def benchmark(self):
        """Return the benchmark"""
        return self._benchmark

    @property
    def result_dir(self):
        """Return the result_dir"""
        return self._result_dir

    @result_dir.setter
    def result_dir(self, result_dir):
        """Set the result_dir"""
        self._result_dir = result_dir

    @benchmark.setter
    def benchmark(self, benchmark):
        """Set the benchmark"""
        self._benchmark = benchmark

    def add_uses(self, use_names):
        """Add an addtional analyser name"""
        for use_name in use_names:
            if use_name in self._use:
                raise ValueError(("Can't use element \"{0}\" two times")
                                 .format(use_name))
            self._use.add(use_name)

    def create_result_data(self):
        """Create result representation"""
        raise NotImplementedError("")

    def _analyse_data(self):
        """Load analyse data out of given analysers"""
        for analyser_name in self._use:
            analyser = self._benchmark.analyser[analyser_name]
            analyse = analyser.analyse_result
            # Ignore empty analyse results
            if analyse is None:
                LOGGER.warning(("No data found for analyser \"{0}\" "
                                "in benchmark run {1}. "
                                "Run analyse step first please.")
                               .format(analyser_name, self._benchmark.id))
                continue
            for stepname in analyse:
                for wp_id in analyse[stepname]:
                    workpackage = None
                    for wp_tmp in self._benchmark.workpackages[stepname]:
                        if wp_tmp.id == wp_id:
                            workpackage = wp_tmp
                            break

                    # Read workpackage history parameterset
                    parameterset = workpackage.add_jube_parameter(
                        workpackage.history.copy())

                    parameter_dict = dict()
                    for par in parameterset:
                        parameter_dict[par.name] = \
                            jube2.util.convert_type(par.parameter_type,
                                                    par.value, stop=False)

                    analyse_dict = analyse[stepname][wp_id]

                    analyse_dict.update(parameter_dict)

                    # Add jube additional information
                    analyse_dict.update({
                        "jube_res_analyser": analyser_name,
                    })

                    # If res_filter is set, only show matching result lines
                    if self._res_filter is not None:
                        res_filter = jube2.util.substitution(self._res_filter,
                                                             analyse_dict)
                        if not jube2.util.eval_bool(res_filter):
                            continue

                    yield analyse_dict

    def _load_units(self, pattern_names):
        """Load units"""
        units = dict()

        alt_pattern_names = list(pattern_names)
        for i, pattern_name in enumerate(alt_pattern_names):
            for option in ["last", "min", "max", "avg", "sum", "std"]:
                matcher = re.match("^(.+)_{0}$".format(option), pattern_name)
                if matcher:
                    alt_pattern_names[i] = matcher.group(1)

        for analyser_name in self._use:
            if analyser_name not in self._benchmark.analyser:
                raise RuntimeError(
                    "<analyser name=\"{0}\"> not found".format(analyser_name))
            patternset_names = \
                self._benchmark.analyser[analyser_name].use.copy()
            for analyse_files in \
                    self._benchmark.analyser[analyser_name].analyser.values():
                for analyse_file in analyse_files:
                    for use in analyse_file.use:
                        patternset_names.add(use)
            for patternset_name in patternset_names:
                patternset = self._benchmark.patternsets[patternset_name]
                for i, pattern_name in enumerate(pattern_names):
                    alt_pattern_name = alt_pattern_names[i]
                    if (pattern_name in patternset) or \
                            (alt_pattern_name in patternset):
                        pattern = patternset[pattern_name]
                        if pattern is None:
                            pattern = patternset[alt_pattern_name]
                        if (pattern.unit is not None) and (pattern.unit != ""):
                            units[pattern_name] = pattern.unit
        return units

    def etree_repr(self):
        """Return etree object representation"""
        result_etree = ET.Element("result")
        if self._result_dir is not None:
            result_etree.attrib["result_dir"] = self._result_dir
        for use in self._use:
            use_etree = ET.SubElement(result_etree, "use")
            use_etree.text = use
        return result_etree
