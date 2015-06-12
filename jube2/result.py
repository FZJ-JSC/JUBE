# JUBE Benchmarking Environment
# Copyright (C) 2008-2015
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
import jube2.conf
import xml.etree.ElementTree as ET
import re
import jube2.log
import operator
import os

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

        def create_result(self, show=True, filename=None):
            """Create result output"""
            raise NotImplementedError("")

        def add_result_data(self, result_data):
            """Add additional result data"""
            raise NotImplementedError("")

        def __eq__(self, other):
            return self.name == other.name

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
                    yield analyse_dict

    def _load_units(self, pattern_names):
        """Load units"""
        units = dict()

        alt_pattern_names = list(pattern_names)
        for i, pattern_name in enumerate(alt_pattern_names):
            for option in ["last", "min", "max", "avg", "sum"]:
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

    class TableData(Result.ResultData):

        """Table data"""

        def __init__(self, name, style, separator):
            Result.ResultData.__init__(self, name)
            self._style = style
            self._separator = separator
            self._data = list()
            self._columns = list()
            self._benchmark_ids = list()

        @property
        def columns(self):
            """Return columns"""
            return self._columns

        @property
        def data(self):
            """Return table data"""
            return self._data

        @property
        def benchmark_ids(self):
            """Return benchmark ids"""
            return self._benchmark_ids

        def add_id_information(self, reverse=False):
            """Add additional id column to table data."""
            id_column = Table.Column("id")
            self._columns.insert(0, id_column)
            for i, data in enumerate(self._data):
                data.insert(0, self._benchmark_ids[i])
            self._data.sort(key=operator.itemgetter(0), reverse=reverse)
            for i, data in enumerate(self._data):
                self._data[i][0] = str(data[0])

        def add_result_data(self, result_data):
            """Add additional result data"""
            if self.name != result_data.name:
                raise RuntimeError("Cannot combine to different result sets.")
            self.add_rows(result_data.columns, result_data.data,
                          result_data.benchmark_ids)

        def add_rows(self, columns, data, benchmark_ids):
            """Add a list of additional rows to current table result data."""
            order = list()
            last_index = len(self._columns)
            # Find matching rows
            for column in columns:
                if column in self._columns:
                    index = self._columns.index(column)
                    # Check weather column occurs multiple times
                    while index in order:
                        try:
                            index = self._columns.index(column, index + 1)
                        except ValueError:
                            index = len(self._columns)
                            self._columns.append(column)
                else:
                    index = len(self._columns)
                    self._columns.append(column)
                order.append(index)
            # Fill up existing rows
            if last_index != len(self._columns):
                for row in self._data:
                    row += [column.null_value
                            for column in self._columns[last_index:]]
            # Add new rows
            for row in data:
                new_row = [column.null_value for column in self._columns]
                for i, index in enumerate(order):
                    new_row[index] = row[i]
                self._data.append(new_row)
                if type(benchmark_ids) is int:
                    self._benchmark_ids.append(benchmark_ids)
            if type(benchmark_ids) is list:
                self._benchmark_ids += benchmark_ids

        def __str__(self):
            colw = list()
            for column in self._columns:
                if column.colw is None:
                    colw.append(0)
                else:
                    colw.append(column.colw)
            data = list()
            data.append([column.resulting_name for column in self._columns])
            data += self._data
            return jube2.util.text_table(
                data, use_header_line=True, auto_linebreak=False, colw=colw,
                indent=0, pretty=(self._style == "pretty"),
                separator=self._separator)

        def create_result(self, show=True, filename=None):
            """Create result output"""
            result_str = str(self)

            # Print result to screen
            if show:
                LOGGER.info(result_str)
                LOGGER.info("\n")
            else:
                LOGGER.debug(result_str)
                LOGGER.debug("\n")

            # Print result to file
            if filename is not None:
                file_handle = open(filename, "w")
                file_handle.write(result_str)
                file_handle.close()

    class Column(object):

        """Class represents one table column"""

        def __init__(self, name, title=None, colw=None, format_string=None,
                     null_value=""):
            self._name = name
            self._title = title
            self._colw = colw
            self._format_string = format_string
            self._null_value = null_value
            self._unit = None

        @property
        def title(self):
            """Column title"""
            return self._title

        @property
        def name(self):
            """Column name"""
            return self._name

        @property
        def colw(self):
            """Column width"""
            return self._colw

        @property
        def null_value(self):
            """Column width"""
            return self._null_value

        @property
        def format(self):
            """Column format"""
            return self._format_string

        @property
        def unit(self):
            """Column unit"""
            return self._unit

        @unit.setter
        def unit(self, unit):
            """Set column title"""
            self._unit = unit

        @property
        def resulting_name(self):
            """Column name based on name, title and unit"""
            if self._title is not None:
                name = self._title
            else:
                name = self._name
                if self._unit is not None:
                    name += "[{0}]".format(self._unit)
            return name

        def etree_repr(self):
            """Return etree object representation"""
            column_etree = ET.Element("column")
            column_etree.text = self._name
            if self._colw is not None:
                column_etree.attrib["colw"] = str(self._colw)
            if self._format_string is not None:
                column_etree.attrib["format"] = self._format_string
            if self._title is not None:
                column_etree.attrib["title"] = self._title
            if self._null_value != "":
                column_etree.attrib["null_value"] = self._null_value
            return column_etree

        def __eq__(self, other):
            return self.resulting_name == other.resulting_name

        def __hash__(self):
            return hash(self.resulting_name)

    def __init__(self, name, style="csv",
                 separator=jube2.conf.DEFAULT_SEPARATOR,
                 sort_names=None):
        Result.__init__(self, name)
        self._style = style
        self._separator = separator
        self._columns = list()
        if sort_names is None:
            self._sort_names = list()
        else:
            self._sort_names = sort_names

    def add_column(self, name, colw=None, format_string=None, title=None,
                   null_value=""):
        """Add an additional column to the table"""
        self._columns.append(Table.Column(name, title, colw, format_string,
                                          null_value))

    def create_result_data(self):
        """Create result representation"""

        result_data = Table.TableData(self._name, self._style,
                                      self._separator)

        # Read pattern/parameter units if available
        units = self._load_units([column.name for column in self._columns])
        for column in self._columns:
            if column.name in units:
                column.unit = units[column.name]

        sort_data = list()
        for dataset in self._analyse_data():
            # Add additional data if needed
            for sort_name in self._sort_names:
                if sort_name not in dataset:
                    dataset[sort_name] = None
            sort_data.append(dataset)

        # Sort the resultset
        if len(self._sort_names) > 0:
            LOGGER.debug("sort using: {0}"
                         .format(jube2.conf.DEFAULT_SEPARATOR.join(
                             self._sort_names)))
            sort_data = sorted(sort_data,
                               key=operator.itemgetter(*self._sort_names))

        # Create table data
        table_data = list()
        for dataset in sort_data:
            row = list()
            cnt = 0
            for column in self._columns:
                if column.name in dataset:
                    cnt += 1
                    # Format data values to create string representation
                    if column.format is not None:
                        value = jube2.util.format_value(column.format,
                                                        dataset[column.name])
                    else:
                        if dataset[column.name] is None:
                            value = column.null_value
                        else:
                            value = str(dataset[column.name])
                    row.append(value)
                else:
                    row.append(column.null_value)

            if cnt > 0:
                table_data.append(row)
        result_data.add_rows(self._columns, table_data, self._benchmark.id)

        return result_data

    def etree_repr(self, new_cwd=None):
        """Return etree object representation"""
        result_etree = Result.etree_repr(self, new_cwd)
        table_etree = ET.SubElement(result_etree, "table")
        table_etree.attrib["name"] = self._name
        table_etree.attrib["style"] = self._style
        table_etree.attrib["seperator"] = self._separator
        if len(self._sort_names) > 0:
            table_etree.attrib["sort"] = \
                jube2.conf.DEFAULT_SEPARATOR.join(self._sort_names)
        for column in self._columns:
            table_etree.append(column.etree_repr())
        return result_etree
