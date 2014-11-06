"""Resulttype definition"""

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

import jube2.util
import xml.etree.ElementTree as ET
import re
import jube2.log
import operator
import collections
import os

logger = jube2.log.getLogger(__name__)


class Result(object):

    """A generic result type"""

    def __init__(self, name):
        self._use = set()
        self._name = name
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

    def create_result(self):
        """Create result representation"""
        raise NotImplementedError("")

    def _analyse_data(self):
        """Load analyse data out of given analyzers"""
        for analyzer_name in self._use:
            analyzer = self._benchmark.analyzer[analyzer_name]
            analyse = analyzer.analyse_result
            # Ignore empty analyse results
            if analyse is None:
                logger.warning(("No data found for analyzer \"{0}\". "
                                "Run analyse step first please.")
                               .format(analyzer_name))
                continue
            for stepname in analyse:
                for wp_id in analyse[stepname]:
                    workpackage = None
                    for wp in self._benchmark.workpackages[stepname]:
                        if wp.id == wp_id:
                            workpackage = wp
                            break

                    # Read workpackage history parameterset
                    parameterset = workpackage.history
                    parameterset.add_parameterset(
                        self._benchmark.get_jube_parameterset())
                    parameterset.add_parameterset(
                        self._benchmark.steps[stepname]
                        .get_jube_parameterset())
                    parameterset.add_parameterset(
                        workpackage.get_jube_parameterset())
                    parameter_dict = dict()
                    for par in parameterset:
                        parameter_dict[par.name] = \
                            jube2.util.convert_type(par.parameter_type,
                                                    par.value, stop=False)

                    for filename in analyse[stepname][wp_id]:
                        analyse_dict = analyse[stepname][wp_id][filename]

                        analyse_dict.update(parameter_dict)

                        # Add jube additional information
                        analyse_dict.update({
                            "jube_res_analyzer": analyzer_name,
                            "jube_res_file": filename,
                        })
                        yield analyse_dict

    def _load_units(self, pattern_names):
        """Load units"""
        units = dict()

        alt_pattern_names = list(pattern_names)
        for i, pattern_name in enumerate(alt_pattern_names):
            for option in ["last", "min", "max", "avg", "sum"]:
                matcher = re.match("^(.+)_{}$".format(option), pattern_name)
                if matcher:
                    alt_pattern_names[i] = matcher.group(1)

        for analyzer_name in self._use:
            for patternset_name in self._benchmark.analyzer[analyzer_name].use:
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

    def etree_repr(self, new_cwd=None):
        """Return etree object representation"""
        result_etree = ET.Element("result")
        if self._result_dir is not None:
            if (new_cwd is not None) and (not os.path.isabs(self._result_dir)):
                result_etree.attrib["result_dir"] = \
                    os.path.relpath(self._result_dir, new_cwd)
            else:
                result_etree.attrib["result_dir"] = self._result_dir
        for use in self._use:
            use_etree = ET.SubElement(result_etree, "use")
            use_etree.text = use
        return result_etree


class Table(Result):

    """A ascii based result table"""

    def __init__(self, name, style="csv",
                 separator=jube2.util.DEFAULT_SEPARATOR,
                 sort_names=None):
        Result.__init__(self, name)
        self._style = style
        self._separator = separator
        self._columns = collections.OrderedDict()
        if sort_names is None:
            self._sort_names = list()
        else:
            self._sort_names = sort_names

    def add_column(self, name, colw=None, format_string=None):
        """Add an additional column to the table"""
        self._columns[name] = {"name": name,
                               "colw": colw,
                               "format": format_string}

    def create_result(self):
        """Create result representation"""
        table_data = list()
        row = list()
        colw = list()
        units = self._load_units(self._columns.keys())
        for column in self._columns.values():
            value = column["name"]
            if column["name"] in units:
                value += "[{}]".format(units[column["name"]])
            row.append(value)
            if column["colw"] is None:
                colw.append(0)
            else:
                colw.append(column["colw"])
        table_data.append(row)

        sort_data = list()
        for dataset in self._analyse_data():
            # Add additional data if needed
            for sort_name in self._sort_names:
                if sort_name not in dataset:
                    dataset[sort_name] = ""
            sort_data.append(dataset)

        # Sort the resultset
        if len(self._sort_names) > 0:
            logger.debug("sort using: {0}"
                         .format(jube2.util.DEFAULT_SEPARATOR.join(
                             self._sort_names)))
            sort_data = sorted(sort_data,
                               key=operator.itemgetter(*self._sort_names))

        for dataset in sort_data:
            row = list()
            cnt = 0
            for column_name in self._columns:
                if column_name in dataset:
                    cnt += 1
                    if (column_name in self._columns) and \
                       (self._columns[column_name]["format"] is not None):
                        value = \
                            jube2.util.format_value(
                                self._columns[column_name]["format"],
                                dataset[column_name])
                    else:
                        value = str(dataset[column_name])
                    row.append(value)
                else:
                    row.append("")
            if cnt > 0:
                table_data.append(row)

        result_str = jube2.util.text_table(table_data, use_header_line=True,
                                           auto_linebreak=False, colw=colw,
                                           indent=0,
                                           pretty=(self._style == "pretty"),
                                           separator=self._separator)
        return result_str

    def etree_repr(self, new_cwd=None):
        """Return etree object representation"""
        result_etree = Result.etree_repr(self, new_cwd)
        table_etree = ET.SubElement(result_etree, "table")
        table_etree.attrib["name"] = self._name
        table_etree.attrib["style"] = self._style
        table_etree.attrib["seperator"] = self._separator
        if len(self._sort_names) > 0:
            table_etree.attrib["sort"] = \
                jube2.util.DEFAULT_SEPARATOR.join(self._sort_names)
        for column_name in self._columns:
            column_etree = ET.SubElement(table_etree, "column")
            column_etree.text = column_name
            if self._columns[column_name]["colw"] is not None:
                column_etree.attrib["colw"] = \
                    str(self._columns[column_name]["colw"])
            if self._columns[column_name]["format"] is not None:
                column_etree.attrib["format"] = \
                    self._columns[column_name]["format"]
        return result_etree
