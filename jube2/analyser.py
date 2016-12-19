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
"""The Analyser class handles the analyse process"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as ET
import jube2.log
import os
import re
import glob
import math
import jube2.pattern
import jube2.util.util
import jube2.util.output

LOGGER = jube2.log.get_logger(__name__)


class Analyser(object):

    """The Analyser handles the analyse process and store all important data
    to run a new analyse."""

    class AnalyseFile(object):

        """A file which should be analysed"""

        def __init__(self, path):
            self._path = path
            self._use = set()

        def add_uses(self, use_names):
            """Add an addtional patternset name"""
            for use_name in use_names:
                if use_name in self._use:
                    raise ValueError(("Can't use element \"{0}\" two times")
                                     .format(use_name))
                self._use.add(use_name)

        def __eq__(self, other):
            result = len(self._use.symmetric_difference(other.use)) == 0
            return result and (self._path == other.path)

        def __repr__(self):
            return "AnalyseFile({0})".format(self._path)

        @property
        def use(self):
            """Return uses"""
            return self._use

        @property
        def path(self):
            """Get file path"""
            return self._path

        def etree_repr(self):
            """Return etree object representation"""
            file_etree = ET.Element("file")
            file_etree.text = self._path
            if len(self._use) > 0:
                file_etree.attrib["use"] = \
                    jube2.conf.DEFAULT_SEPARATOR.join(self._use)
            return file_etree

    def __init__(self, name, reduce_iteration=True):
        self._name = name
        self._use = set()
        self._analyse = dict()
        self._benchmark = None
        self._analyse_result = None
        self._reduce_iteration = reduce_iteration

    @property
    def benchmark(self):
        """Get benchmark information"""
        return self._benchmark

    @benchmark.setter
    def benchmark(self, benchmark):
        """Set benchmark information"""
        self._benchmark = benchmark

    @property
    def use(self):
        """Return uses"""
        return self._use

    @property
    def analyser(self):
        """Return analyse dict"""
        return self._analyse

    @property
    def analyse_result(self):
        """Return analyse result"""
        return self._analyse_result

    @analyse_result.setter
    def analyse_result(self, analyse_result):
        """Set analyse result"""
        self._analyse_result = analyse_result

    def add_analyse(self, step_name, analyse_file):
        """Add an addtional analyse file"""
        if step_name not in self._analyse:
            self._analyse[step_name] = list()
        if analyse_file not in self._analyse[step_name]:
            self._analyse[step_name].append(analyse_file)

    def add_uses(self, use_names):
        """Add an addtional patternset name"""
        for use_name in use_names:
            if use_name in self._use:
                raise ValueError(("Can't use element \"{0}\" two times")
                                 .format(use_name))
            self._use.add(use_name)

    @property
    def name(self):
        """Get analyser name"""
        return self._name

    def etree_repr(self):
        """Return etree object representation"""
        analyser_etree = ET.Element("analyser")
        analyser_etree.attrib["name"] = self._name
        analyser_etree.attrib["reduce"] = str(self._reduce_iteration)
        for use in self._use:
            use_etree = ET.SubElement(analyser_etree, "use")
            use_etree.text = use
        for step_name in self._analyse:
            analyse_etree = ET.SubElement(analyser_etree, "analyse")
            analyse_etree.attrib["step"] = step_name
            for fileobj in self._analyse[step_name]:
                analyse_etree.append(fileobj.etree_repr())
        return analyser_etree

    def _combine_and_check_patternsets(self, patternset, uses):
        """Combine patternsets given by uses and check compatibility"""
        for use in uses:
            if use not in self._benchmark.patternsets:
                raise RuntimeError(("<patternset name=\"{0}\"> used but not " +
                                    "found").format(use))
            if not patternset.is_compatible(self._benchmark.patternsets[use]):
                incompatible_names = patternset.get_incompatible_pattern(
                    self._benchmark.patternsets[use])
                raise RuntimeError(("Can't use patternset \"{0}\" " +
                                    "in analyser \"{1}\", because there are " +
                                    "incompatible pattern name combinations: "
                                    "{2}")
                                   .format(use, self._name,
                                           ",".join(incompatible_names)))
            patternset.add_patternset(self._benchmark.patternsets[use])

    def analyse(self):
        """Run the analyser"""
        LOGGER.debug("Run analyser \"{0}\"".format(self._name))
        if self._benchmark is None:
            raise RuntimeError("No benchmark found using analyser {0}"
                               .format(self._name))

        result = dict()

        # Combine all patternsets
        patternset = jube2.pattern.Patternset()
        self._combine_and_check_patternsets(patternset, self._use)

        # Print debug info
        debugstr = "  available pattern:\n"
        debugstr += \
            jube2.util.output.text_table(
                [("pattern", "value")] +
                sorted([(par.name, par.value) for par in
                        patternset.pattern_storage]),
                use_header_line=True, indent=9,
                align_right=False)
        debugstr += "\n  available derived pattern:\n"
        debugstr += \
            jube2.util.output.text_table(
                [("pattern", "value")] +
                sorted([(par.name, par.value) for par in
                        patternset.derived_pattern_storage]),
                use_header_line=True, indent=9,
                align_right=False)
        LOGGER.debug(debugstr)

        for stepname in self._analyse:
            result[stepname] = dict()
            LOGGER.debug("  analyse step \"{0}\"".format(stepname))
            if stepname not in self._benchmark.steps:
                raise RuntimeError(("Could not find <step name=\"{0}\"> "
                                    "when using analyser \"{1}\"").format(
                                        stepname, self._name))
            step = self._benchmark.steps[stepname]
            workpackages = set(self._benchmark.workpackages[stepname])
            while len(workpackages) > 0:
                root_workpackage = workpackages.pop()
                match_dict = dict()
                local_patternset = patternset.copy()
                result[stepname][root_workpackage.id] = dict()
                # Should multiple iterations be reduced to a single result line
                if self._reduce_iteration:
                    siblings = set(root_workpackage.iteration_siblings)
                else:
                    siblings = set([root_workpackage])
                while len(siblings) > 0:
                    workpackage = siblings.pop()
                    if workpackage in workpackages:
                        workpackages.remove(workpackage)

                    # Ignore workpackages not started yet
                    if not workpackage.started:
                        continue

                    # Get parameterset of current workpackage
                    parameterset = \
                        workpackage.add_jube_parameter(
                            workpackage.history.copy())

                    parameter = \
                        dict([[par.name, par.value] for par in
                              parameterset.constant_parameter_dict.values()])

                    for file_obj in self._analyse[stepname]:
                        if step.alt_work_dir is not None:
                            file_path = step.alt_work_dir
                            file_path = jube2.util.util.substitution(
                                file_path, parameter)
                            file_path = \
                                os.path.expandvars(
                                    os.path.expanduser(file_path))
                            file_path = os.path.join(
                                self._benchmark.file_path_ref, file_path)
                        else:
                            file_path = workpackage.work_dir

                        filename = \
                            jube2.util.util.substitution(file_obj.path,
                                                         parameter)
                        filename = \
                            os.path.expandvars(os.path.expanduser(filename))

                        file_path = os.path.join(file_path, filename)
                        for path in glob.glob(file_path):
                            # scan files
                            LOGGER.debug(("    scan file {0}").format(path))

                            new_result_dict, match_dict = \
                                self._analyse_file(path, local_patternset,
                                                   parameterset, match_dict,
                                                   file_obj.use)
                            result[stepname][root_workpackage.id].update(
                                new_result_dict)

                # Set default pattern values if available and necessary
                new_result_dict = result[stepname][root_workpackage.id]
                for pattern in local_patternset.pattern_storage:
                    if (pattern.default_value is not None) and \
                            (pattern.name not in new_result_dict):
                        default = pattern.default_value
                        # Convert default value
                        if pattern.content_type == "int":
                            if default == "nan":
                                default = float("nan")
                            else:
                                default = int(float(default))
                        elif pattern.content_type == "float":
                            default = float(default)
                        new_result_dict[pattern.name] = default
                        new_result_dict[pattern.name + "_cnt"] = 0
                        new_result_dict[pattern.name + "_last"] = default
                        if pattern.content_type in ["int", "float"]:
                            new_result_dict.update(
                                {pattern.name + "_sum": default,
                                 pattern.name + "_min": default,
                                 pattern.name + "_max": default,
                                 pattern.name + "_avg": default,
                                 pattern.name + "_sum2": default**2,
                                 pattern.name + "_std": 0})

                # Evaluate derived pattern
                if len(result[stepname][root_workpackage.id]) > 0:
                    new_result_dict = self._eval_derived_pattern(
                        local_patternset, parameterset,
                        result[stepname][root_workpackage.id])
                    result[stepname][root_workpackage.id].update(
                        new_result_dict)

        self._analyse_result = result

    def _eval_derived_pattern(self, patternset, parameterset, result_dict):
        """Evaluate all derived pattern in patternset using parameterset
        and result_dict"""
        resultset = jube2.parameter.Parameterset()
        for name in result_dict:
            resultset.add_parameter(
                jube2.parameter.Parameter.create_parameter(
                    name, value=str(result_dict[name])))

        # Get jube patternset
        jube_pattern = jube2.pattern.get_jube_pattern()
        # calculate derived pattern
        patternset.derived_pattern_substitution(
            [parameterset, resultset, jube_pattern.pattern_storage])

        new_result_dict = dict()
        # Convert content type
        for par in patternset.derived_pattern_storage:
            if par.mode not in jube2.conf.ALLOWED_SCRIPTTYPES:
                new_result_dict[par.name] = \
                    jube2.util.util.convert_type(par.content_type,
                                                 par.value, stop=False)
        return new_result_dict

    def _analyse_file(self, file_path, patternset, parameterset,
                      match_dict=None, additional_uses=None):
        """Scan given files with given pattern and produce a result
        parameterset"""
        if additional_uses is None:
            additional_uses = set()
        if match_dict is None:
            match_dict = dict()

        if not os.path.isfile(file_path):
            return dict(), match_dict

        local_patternset = patternset.copy()

        # Add file specific uses
        self._combine_and_check_patternsets(local_patternset, additional_uses)

        # Store all derived pattern in original patternset
        for pattern in local_patternset.derived_pattern_storage:
            if pattern not in patternset:
                patternset.add_pattern(pattern)

        # Unique pattern/parameter check
        if (not parameterset.is_compatible(
                local_patternset.pattern_storage)) or \
           (not parameterset.is_compatible(
                local_patternset.derived_pattern_storage)):

            incompatible_names = parameterset.get_incompatible_parameter(
                local_patternset.pattern_storage)
            incompatible_names.update(parameterset.get_incompatible_parameter(
                local_patternset.derived_pattern_storage))
            raise RuntimeError(("A pattern and a parameter (\"{0}\") "
                                "using the same name in "
                                "analyser \"{1}\"").format(
                                    ",".join(incompatible_names), self._name))

        # Get jube patternset
        jube_pattern = jube2.pattern.get_jube_pattern()

        # Do pattern substitution
        local_patternset.pattern_substitution(
            [parameterset, jube_pattern.pattern_storage])

        patternlist = [p for p in local_patternset.pattern_storage]

        file_handle = open(file_path, "r")
        # Read file content
        data = file_handle.read()
        for pattern in patternlist:
            if pattern.name not in match_dict:
                match_dict[pattern.name] = dict()
            try:
                regex = re.compile(pattern.value, re.MULTILINE)
            except re.error as ree:
                raise RuntimeError(("Error inside pattern \"{0}\" : " +
                                    "\"{1}\" : {2}")
                                   .format(pattern.name, pattern.value, ree))
            # Run regular expression
            matches = re.findall(regex, data)
            # If there are different groups reduce result shape
            if regex.groups > 1:
                match_list = list()
                for match in matches:
                    match_list = match_list + list(match)
            else:
                match_list = matches
            # Remove empty matches
            match_list = [match for match in match_list if match != ""]

            # Convert to pattern type
            new_match_list = list()
            for match in match_list:
                try:
                    if pattern.content_type == "int":
                        if match == "nan":
                            new_match_list.append(float("nan"))
                        else:
                            new_match_list.append(int(float(match)))
                    elif pattern.content_type == "float":
                        new_match_list.append(float(match))
                    else:
                        new_match_list.append(match)
                except ValueError:
                    LOGGER.warning(("\"{0}\" can't be represented " +
                                    "as a \"{1}\"")
                                   .format(match, pattern.content_type))
            match_list = new_match_list

            if len(match_list) > 0:
                # First match is default
                if "first" not in match_dict[pattern.name]:
                    match_dict[pattern.name]["first"] = match_list[0]

                for match in match_list:
                    if pattern.content_type in ["int", "float"]:
                        if "min" in match_dict[pattern.name]:
                            match_dict[pattern.name]["min"] = \
                                min(match_dict[pattern.name]["min"], match)
                        else:
                            match_dict[pattern.name]["min"] = match
                        if "max" in match_dict[pattern.name]:
                            match_dict[pattern.name]["max"] = \
                                max(match_dict[pattern.name]["max"], match)
                        else:
                            match_dict[pattern.name]["max"] = match
                        if "sum" in match_dict[pattern.name]:
                            match_dict[pattern.name]["sum"] += match
                        else:
                            match_dict[pattern.name]["sum"] = match
                        if "sum2" in match_dict[pattern.name]:
                            match_dict[pattern.name]["sum2"] += match**2
                        else:
                            match_dict[pattern.name]["sum2"] = match**2

                    if "cnt" in match_dict[pattern.name]:
                        match_dict[pattern.name]["cnt"] += 1
                    else:
                        match_dict[pattern.name]["cnt"] = 1

                if pattern.content_type in ["int", "float"]:
                    if match_dict[pattern.name]["cnt"] > 0:
                        match_dict[pattern.name]["avg"] = \
                            (match_dict[pattern.name]["sum"] /
                             match_dict[pattern.name]["cnt"])

                    if match_dict[pattern.name]["cnt"] > 1:
                        match_dict[pattern.name]["std"] = math.sqrt(
                            (abs(match_dict[pattern.name]["sum2"] -
                                 (match_dict[pattern.name]["sum"]**2 /
                                  match_dict[pattern.name]["cnt"])) /
                             (match_dict[pattern.name]["cnt"] - 1)))
                    else:
                        match_dict[pattern.name]["std"] = 0

                match_dict[pattern.name]["last"] = match_list[-1]

        info_str = "      file \"{0}\" scanned pattern found:\n".format(
            os.path.basename(file_path))
        info_str += jube2.util.output.text_table(
            [(_name, ", ".join(["{0}:{1}".format(key, con)
                                for key, con in value.items()]))
             for _name, value in match_dict.items()],
            indent=9, align_right=True, auto_linebreak=True)
        LOGGER.debug(info_str)
        file_handle.close()

        # Create result dict
        result_dict = dict()
        for pattern_name in match_dict:
            for option in match_dict[pattern_name]:
                if option == "first":
                    name = pattern_name
                else:
                    name = "{0}_{1}".format(pattern_name, option)
                result_dict[name] = match_dict[pattern_name][option]

        return result_dict, match_dict

    def analyse_etree_repr(self):
        """Create an etree representation of a analyse dict:
        stepname -> workpackage_id -> filename -> patternname -> value
        """
        etree = list()
        for stepname in self._analyse_result:
            step_etree = ET.Element("step")
            step_etree.attrib["name"] = stepname
            for workpackage_id in self._analyse_result[stepname]:
                workpackage_etree = ET.SubElement(step_etree, "workpackage")
                workpackage_etree.attrib["id"] = str(workpackage_id)
                for pattern in self._analyse_result[stepname][workpackage_id]:
                    if type(self._analyse_result[stepname][workpackage_id]
                            [pattern]) is int:
                        content_type = "int"
                    elif type(self._analyse_result[stepname][
                              workpackage_id][pattern]) is float:
                        content_type = "float"
                    else:
                        content_type = "string"
                    pattern_etree = ET.SubElement(workpackage_etree, "pattern")
                    pattern_etree.attrib["name"] = pattern
                    pattern_etree.attrib["type"] = content_type
                    pattern_etree.text = \
                        str(self._analyse_result[stepname][workpackage_id]
                            [pattern])
            etree.append(step_etree)
        return etree
