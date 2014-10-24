"""The Analyzer class handles the analyze process"""

# #############################################################################
# #  JUBE Benchmarking Environment                                           ##
# #  http://www.fz-juelich.de/jsc/jube                                       ##
# #############################################################################
# #  Copyright (c) 2008-2014                                                 ##
# #  Forschungszentrum Juelich, Juelich Supercomputing Centre                ##
# #                                                                          ##
# #  See the file LICENSE in the package base directory for details          ##
# #############################################################################

from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as ET
import logging
import os
import re
import jube2.pattern
import jube2.util

logger = logging.getLogger(__name__)


class Analyzer(object):

    """The Analyzer handles the anlyse process and store all importtant data
    to run a new analyse."""

    def __init__(self, name):
        self._name = name
        self._use = set()
        self._analyse = dict()
        self._benchmark = None
        self._analyse_result = None

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
    def analyse_result(self):
        """Return analyse result"""
        return self._analyse_result

    @analyse_result.setter
    def analyse_result(self, analyse_result):
        """Set analyse result"""
        self._analyse_result = analyse_result

    def add_analyse(self, step_name, filename):
        """Add an addtional analyse file"""
        if step_name not in self._analyse:
            self._analyse[step_name] = set()
        self._analyse[step_name].add(filename)

    def add_uses(self, use_names):
        """Add an addtional patternset name"""
        for use_name in use_names:
            if use_name in self._use:
                raise ValueError(("Can't use element \"{0}\" two times")
                                 .format(use_name))
            self._use.add(use_name)

    @property
    def name(self):
        """Get analyzer name"""
        return self._name

    def etree_repr(self):
        """Return etree object representation"""
        analyzer_etree = ET.Element("analyzer")
        analyzer_etree.attrib["name"] = self._name
        for use in self._use:
            use_etree = ET.SubElement(analyzer_etree, "use")
            use_etree.text = use
        for analyse in self._analyse:
            analyse_etree = ET.SubElement(analyzer_etree, "analyse")
            analyse_etree.attrib["step"] = analyse
            for filename in self._analyse[analyse]:
                file_etree = ET.SubElement(analyse_etree, "file")
                file_etree.text = filename
        return analyzer_etree

    def analyse(self):
        """Run the analyzer"""
        logger.debug("Run analyser \"{}\"".format(self._name))
        if self._benchmark is None:
            raise RuntimeError("No benchmark found using analyser {}"
                               .format(self._name))

        result = dict()

        # Combine all patternsets
        patternset = jube2.pattern.Patternset()
        for use in self._use:
            if use not in self._benchmark.patternsets:
                raise RuntimeError(("<patternset name=\"{}\"> used but not " +
                                    "found").format(use))
            if not patternset.is_compatible(self._benchmark.patternsets[use]):
                raise RuntimeError(("Can't use patternset \"{0}\" " +
                                    "in analyser \"{1}\"")
                                   .format(use, self._name))
            patternset.add_patternset(self._benchmark.patternsets[use])

        # Get jube patternset
        jube_pattern = jube2.pattern.get_jube_pattern()

        # Print debug info
        debugstr = "  available pattern:\n"
        debugstr += \
            jube2.util.table([("pattern", "value")] +
                             sorted([(par.name, par.value) for par in
                                     patternset.pattern_storage]),
                             use_header_line=True, indent=9,
                             align_right=False)
        debugstr += "\n  available derived pattern:\n"
        debugstr += \
            jube2.util.table([("pattern", "value")] +
                             sorted([(par.name, par.value) for par in
                                     patternset.derived_pattern_storage]),
                             use_header_line=True, indent=9,
                             align_right=False)
        logger.debug(debugstr)

        for stepname in self._analyse:
            result[stepname] = dict()
            logger.debug("  analyse step \"{}\"".format(stepname))
            step = self._benchmark.steps[stepname]
            for workpackage in self._benchmark.workpackages[stepname]:
                result[stepname][workpackage.id] = dict()
                # Ignore workpackages not started yet
                if not workpackage.started:
                    continue

                local_patternset = patternset.copy()

                # Get parameterset of current workpackage
                parameterset = workpackage.history.copy()

                # Add internal parameter
                parameterset.add_parameterset(
                    self._benchmark.get_jube_parameterset())
                parameterset.add_parameterset(
                    step.get_jube_parameterset())
                parameterset.add_parameterset(
                    workpackage.get_jube_parameterset())

                parameter = \
                    dict([[par.name, par.value] for par in
                          parameterset.constant_parameter_dict.values()])

                # Unique pattern/parameter check
                if (not parameterset.is_compatible(
                        local_patternset.pattern_storage)) or \
                   (not parameterset.is_compatible(
                        local_patternset.derived_pattern_storage)):
                    raise RuntimeError(("A pattern and a parameter "
                                        "using the same name in "
                                        "analyzer \"{}\"").format(self._name))

                # Do pattern substitution
                local_patternset.pattern_substitution(
                    [parameterset, jube_pattern.pattern_storage])
                pattern = [p for p in local_patternset.pattern_storage]

                for filename in self._analyse[stepname]:
                    if step.alt_work_dir is not None:
                        file_path = step.alt_work_dir
                    else:
                        file_path = workpackage.work_dir
                    file_path = os.path.join(file_path, filename)
                    file_path = jube2.util.substitution(file_path, parameter)

                    # scan file
                    result_dict = Analyzer._analyse_file(file_path, pattern)

                    if len(result_dict) > 0:
                        resultset = jube2.parameter.Parameterset()
                        for name in result_dict:
                            resultset.add_parameter(
                                jube2.parameter.Parameter.
                                create_parameter(name,
                                                 value=str(
                                                     result_dict[name])))

                        # calculate derived pattern
                        derived_pattern = \
                            local_patternset.derived_pattern_storage.copy()
                        derived_pattern.parameter_substitution(
                            [parameterset, resultset,
                             jube_pattern.pattern_storage],
                            final_sub=True)

                        # Convert content type
                        for par in derived_pattern:
                            result_dict[par.name] = \
                                jube2.util.convert_type(par.content_type,
                                                        par.value,
                                                        stop=False)

                        # Store result data
                        result[stepname][workpackage.id][filename] = \
                            result_dict

        self._analyse_result = result

    @staticmethod
    def _analyse_file(file_path, patternlist):
        """Scan given file with given pattern and produce a result
        parameterset"""
        result_dict = dict()

        if os.path.isfile(file_path):
            file_handle = open(file_path, "r")
            # Read file content
            data = file_handle.read()
            for pattern in patternlist:
                regex = re.compile(pattern.value, re.MULTILINE)
                # Run regular expression
                matches = re.findall(regex, data)
                # If there are differnt groups reduce result shape
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
                            new_match_list.append(int(match))
                        elif pattern.content_type == "float":
                            new_match_list.append(float(match))
                        else:
                            new_match_list.append(match)
                    except ValueError:
                        logger.warning(("\"{0}\" can't be represented " +
                                        "as a \"{1}\"")
                                       .format(match, pattern.content_type))
                match_list = new_match_list

                if len(match_list) > 0:
                    result = dict()
                    # First match is default
                    result["first"] = match_list[0]
                    number_sum = 0
                    if pattern.content_type in ["int", "float"]:
                        for match in match_list:
                            number_sum += match

                            if "min" in pattern.reduce_option:
                                if "min" in result:
                                    result["min"] = min(result["min"], match)
                                else:
                                    result["min"] = match
                            if "max" in pattern.reduce_option:
                                if "max" in result:
                                    result["max"] = max(result["max"], match)
                                else:
                                    result["max"] = match
                        if "sum" in pattern.reduce_option:
                            result["sum"] = number_sum
                        if "avg" in pattern.reduce_option:
                            result["avg"] = number_sum / len(match_list)
                    if "last" in pattern.reduce_option:
                        result["last"] = match_list[-1]
                    if "cnt" in pattern.reduce_option:
                        result["cnt"] = len(match_list)

                    # Create parameter of result dict
                    for option in result:
                        if option == "first":
                            name = pattern.name
                        else:
                            name = "{0}_{1}".format(pattern.name, option)
                        result_dict[name] = result[option]
            info_str = "    scanned file \"{0}\" {1}pattern found:\n".format(
                os.path.basename(file_path),
                "" if len(result_dict) > 0 else "no ")
            info_str += \
                jube2.util.table([(name, str(value))
                                  for name, value in result_dict.items()],
                                 indent=9, align_right=True,
                                 auto_linebreak=True)
            logger.debug(info_str)
            file_handle.close()
        return result_dict

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
                for filename in self._analyse_result[stepname][workpackage_id]:
                    file_etree = ET.SubElement(workpackage_etree, "file")
                    file_etree.attrib["name"] = filename
                    for pattern in self._analyse_result[
                            stepname][workpackage_id][filename]:
                        if type(self._analyse_result[stepname][workpackage_id][
                                filename][pattern]) is int:
                            content_type = "int"
                        elif type(self._analyse_result[stepname][
                                  workpackage_id][filename][pattern]) is float:
                            content_type = "float"
                        else:
                            content_type = "string"
                        pattern_etree = ET.SubElement(file_etree, "pattern")
                        pattern_etree.attrib["name"] = pattern
                        pattern_etree.attrib["type"] = content_type
                        pattern_etree.text = \
                            str(self._analyse_result[stepname][workpackage_id][
                                filename][pattern])
            etree.append(step_etree)
        return etree
