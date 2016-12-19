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
"""Tabletype definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

from jube2.result_types.keyvaluesresult import KeyValuesResult
from jube2.result import Result
import xml.etree.ElementTree as ET
import jube2.log
import jube2.util.output

LOGGER = jube2.log.get_logger(__name__)


class Table(KeyValuesResult):

    """A ascii based result table"""

    class TableData(KeyValuesResult.KeyValuesData):

        """Table data"""

        def __init__(self, name_or_other, style, separator, transpose):
            if type(name_or_other) is KeyValuesResult.KeyValuesData:
                self._name = name_or_other.name
                self._keys = name_or_other.keys
                self._data = name_or_other.data
                self._benchmark_ids = name_or_other.benchmark_ids
            else:
                KeyValuesResult.KeyValuesData.__init__(self, name_or_other)
            self._style = style
            self._separator = separator
            # Ignore separator if pretty style is used
            if self._style == "pretty":
                self._separator = None
            elif self._separator is None:
                self._separator = jube2.conf.DEFAULT_SEPARATOR
            self._transpose = transpose

        @property
        def _columns(self):
            """Get columns"""
            return self._keys

        @property
        def style(self):
            """Get style"""
            return self._style

        @style.setter
        def style(self, style):
            """Set style"""
            self._style = style

        @property
        def separator(self):
            """Get separator"""
            return self._separator

        @separator.setter
        def separator(self, separator):
            """Set separator"""
            self._separator = separator

        def __str__(self):
            colw = list()
            for column in self._columns:
                if type(column) is Table.Column:
                    if column.colw is None:
                        colw.append(0)
                    else:
                        colw.append(column.colw)
                else:
                    colw.append(0)
            data = list()
            data.append([column.resulting_name for column in self._columns])
            data += self._data
            if self._style == "pretty":
                output = "{0}:\n".format(self.name)
            else:
                output = ""
            output += jube2.util.output.text_table(
                data, use_header_line=True, auto_linebreak=False, colw=colw,
                indent=0, pretty=(self._style == "pretty"),
                separator=self._separator, transpose=self._transpose)

            return output

        def create_result(self, show=True, filename=None, **kwargs):
            """Create result output"""
            # If there are multiple benchmarks, add benchmark id information
            if len(set(self._benchmark_ids)) > 1:
                self.add_id_information(reverse=kwargs.get("reverse", False))

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

    class Column(KeyValuesResult.DataKey):

        """Class represents one table column"""

        def __init__(self, name, title=None, colw=None, format_string=None,
                     unit=None):
            KeyValuesResult.DataKey.__init__(self, name, title, format_string,
                                             unit)
            self._colw = colw

        @property
        def colw(self):
            """Column width"""
            return self._colw

        def etree_repr(self):
            """Return etree object representation"""
            column_etree = KeyValuesResult.DataKey.etree_repr(self)
            column_etree.tag = "column"
            if self._colw is not None:
                column_etree.attrib["colw"] = str(self._colw)
            return column_etree

    def __init__(self, name, style="csv",
                 separator=jube2.conf.DEFAULT_SEPARATOR,
                 sort_names=None,
                 transpose=False,
                 res_filter=None):
        KeyValuesResult.__init__(self, name, sort_names, res_filter)
        self._style = style
        self._separator = separator
        self._transpose = transpose

    def add_column(self, name, colw=None, format_string=None, title=None):
        """Add an additional column to the dataset"""
        self._keys.append(Table.Column(name, title, colw, format_string))

    def add_key(self, name, format_string=None, title=None, unit=None):
        """Add an additional key to the dataset"""
        self._keys.append(Table.Column(name, title, None, format_string))

    def create_result_data(self):
        """Create result data"""
        result_data = KeyValuesResult.create_result_data(self)
        return Table.TableData(result_data, self._style, self._separator,
                               self._transpose)

    def etree_repr(self):
        """Return etree object representation"""
        result_etree = Result.etree_repr(self)
        table_etree = ET.SubElement(result_etree, "table")
        table_etree.attrib["name"] = self._name
        table_etree.attrib["style"] = self._style
        if self._separator is not None:
            table_etree.attrib["separator"] = self._separator
        if self._res_filter is not None:
            table_etree.attrib["filter"] = self._res_filter
        table_etree.attrib["transpose"] = str(self._transpose)
        if len(self._sort_names) > 0:
            table_etree.attrib["sort"] = \
                jube2.conf.DEFAULT_SEPARATOR.join(self._sort_names)
        for column in self._keys:
            table_etree.append(column.etree_repr())
        return result_etree
