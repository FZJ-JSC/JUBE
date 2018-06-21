# JUBE Benchmarking Environment
# Copyright (C) 2008-2018
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

import jube2.util.util
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
                raise ValueError(("Element \"{0}\" can only be used once")
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

            # Create workpackage chains
            wp_chains = list()
            all_wps = set()
            for ids in [analyse[stepname].keys() for stepname in analyse]:
                all_wps.update(set(map(int, ids)))
            # Create copy of all wps to reduce this list while wps are sorted
            # into the chains
            all_wps_tmp = all_wps.copy()

            while (len(all_wps_tmp) > 0):
                next_id = all_wps_tmp.pop()
                # Create new chain
                wp_chains.append(list())
                # Add all parents to the chain
                for wp in self._benchmark.workpackage_by_id(next_id).\
                        parent_history:
                    if wp.id in all_wps:
                        wp_chains[-1].append(wp.id)
                        all_wps_tmp.discard(wp.id)
                # Add wp itself to the cahin
                wp_chains[-1].append(next_id)
                steps_in_list = set()
                # Add children to the chain, each step can only be added once)
                for wp in self._benchmark.workpackage_by_id(next_id).\
                        children_future:
                    if wp.step.name not in steps_in_list:
                        if wp.id in all_wps:
                            steps_in_list.add(wp.step.name)
                            wp_chains[-1].append(wp.id)
                            all_wps_tmp.discard(wp.id)

            # Add all parent WPs which might be missing in the chain, by
            # using the last WP as a reference. This WPs does not provide any
            # analyse data but, their parameter will be available
            for i, chain in enumerate(wp_chains):
                for wp in self._benchmark.workpackage_by_id(chain[-1]).\
                        parent_history:
                    if wp.id not in chain:
                        wp_chains[i] = [wp.id] + chain

            # Create output datasets by combining analyse and parameter data
            for chain in wp_chains:
                analyse_dict = dict()
                for wp_id in chain:
                    workpackage = self._benchmark.workpackage_by_id(wp_id)
                    # add analyse data
                    if (wp_id in all_wps):
                        analyse_dict.update(
                            analyse[workpackage.step.name][wp_id])
                    # add parameter
                    parameter_dict = dict()
                    for par in workpackage.parameterset:
                        value = \
                            jube2.util.util.convert_type(par.parameter_type,
                                                         par.value, stop=False)
                        # add suffix to the parameter name
                        if (par.name + "_" + workpackage.step.name
                                not in parameter_dict):
                            parameter_dict[par.name + "_" +
                                           workpackage.step.name] = value
                        # parmater without suffix si used for the last WP in
                        # the chain
                        if wp_id == chain[-1]:
                            parameter_dict[par.name] = value
                    analyse_dict.update(parameter_dict)
                    # Add jube additional information
                    analyse_dict.update({
                        "jube_res_analyser": analyser_name,
                    })

                # If res_filter is set, only show matching result lines
                if self._res_filter is not None:
                    res_filter = jube2.util.util.substitution(
                        self._res_filter, analyse_dict)
                    if not jube2.util.util.eval_bool(res_filter):
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
