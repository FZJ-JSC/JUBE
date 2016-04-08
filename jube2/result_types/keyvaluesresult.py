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
"""KeyValuesResulttype definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

from jube2.result import Result
import jube2.log
import xml.etree.ElementTree as ET
import operator

LOGGER = jube2.log.get_logger(__name__)


class KeyValuesResult(Result):

    """A generic key value result type"""

    class KeyValuesData(Result.ResultData):

        """Key value data"""

        def __init__(self, other_or_name):
            if type(other_or_name) is str:
                Result.ResultData.__init__(self, other_or_name)
            elif type(other_or_name) is Result.ResultData:
                self._name = other_or_name.name
            self._data = list()
            self._keys = list()
            self._benchmark_ids = list()

        @property
        def keys(self):
            """Return keys"""
            return self._keys

        @property
        def data(self):
            """Return table data"""
            return self._data

        @property
        def data_dict(self):
            """Return unordered dictionary representation of data"""
            result_dict = dict()
            for i, key in enumerate(self._keys):
                result_dict[key] = list()
                for data in self._data:
                    result_dict[key].append(data[i])
            return result_dict

        @property
        def benchmark_ids(self):
            """Return benchmark ids"""
            return self._benchmark_ids

        def add_key_value_data(self, keys, data, benchmark_ids):
            """Add a list of additional rows to current result data"""
            order = list()
            last_index = len(self._keys)
            # Find matching rows
            for key in keys:
                if key in self._keys:
                    index = self._keys.index(key)
                    # Check weather key occurs multiple times
                    while index in order:
                        try:
                            index = self._keys.index(key, index + 1)
                        except ValueError:
                            index = len(self._keys)
                            self._keys.append(key)
                else:
                    index = len(self._keys)
                    self._keys.append(key)
                order.append(index)
            # Fill up existing rows
            if last_index != len(self._keys):
                for row in self._data:
                    row += [key.null_value
                            for key in self._keys[last_index:]]
            # Add new rows
            for row in data:
                new_row = [key.null_value for key in self._keys]
                for i, index in enumerate(order):
                    new_row[index] = row[i]
                self._data.append(new_row)
                if type(benchmark_ids) is int:
                    self._benchmark_ids.append(benchmark_ids)
            if type(benchmark_ids) is list:
                self._benchmark_ids += benchmark_ids

        def add_id_information(self, reverse=False):
            """Add additional id key to table data."""
            id_key = KeyValuesResult.DataKey("id")
            if id_key not in self._keys:
                # Add key at the beginning of keys list
                self._keys.insert(0, id_key)
                for i, data in enumerate(self._data):
                    data.insert(0, self._benchmark_ids[i])
                # Sort data by using new id key (stable sort)
                self._data.sort(key=operator.itemgetter(0), reverse=reverse)
                for i, data in enumerate(self._data):
                    self._data[i][0] = str(data[0])

        def add_result_data(self, result_data):
            """Add additional result data"""
            if self.name != result_data.name:
                raise RuntimeError("Cannot combine to different result sets.")
            self.add_key_value_data(result_data.keys, result_data.data,
                                    result_data.benchmark_ids)

        def create_result(self, show=True, filename=None, **kwargs):
            """Create result representation"""
            raise NotImplementedError("")

    class DataKey(object):
        """Class represents one data key """

        def __init__(self, name, title=None, format_string=None,
                     null_value="", unit=None):
            self._name = name
            self._title = title
            self._format_string = format_string
            self._null_value = null_value
            self._unit = unit

        @property
        def title(self):
            """Key title"""
            return self._title

        @property
        def name(self):
            """Key name"""
            return self._name

        @property
        def null_value(self):
            """Key data null value"""
            return self._null_value

        @property
        def format(self):
            """Key data format"""
            return self._format_string

        @property
        def unit(self):
            """Key data unit"""
            return self._unit

        @unit.setter
        def unit(self, unit):
            """Set key data unit"""
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
            key_etree = ET.Element("key")
            key_etree.text = self._name
            if self._format_string is not None:
                key_etree.attrib["format"] = self._format_string
            if self._title is not None:
                key_etree.attrib["title"] = self._title
            if self._null_value != "":
                key_etree.attrib["null_value"] = self._null_value
            return key_etree

        def __eq__(self, other):
            return self.resulting_name == other.resulting_name

        def __hash__(self):
            return hash(self.resulting_name)

    def __init__(self, name, sort_names=None, res_filter=None):
        Result.__init__(self, name, res_filter)
        self._keys = list()
        if sort_names is None:
            self._sort_names = list()
        else:
            self._sort_names = sort_names

    def add_key(self, name, format_string=None, title=None, null_value="",
                unit=None):
        """Add an additional key to the dataset"""
        self._keys.append(KeyValuesResult.DataKey(name, title, format_string,
                                                  null_value, unit))

    def create_result_data(self):
        """Create result data"""
        result_data = KeyValuesResult.KeyValuesData(self._name)

        # Read pattern/parameter units if available
        units = self._load_units([key.name for key in self._keys])
        for key in self._keys:
            if key.name in units:
                key.unit = units[key.name]

        sort_data = list()
        for dataset in self._analyse_data():
            # Add additional data if needed
            for sort_name in self._sort_names:
                if sort_name not in dataset:
                    dataset[sort_name] = None
            sort_data.append(dataset)

        # Sort the resultset
        if len(self._sort_names) > 0:
            LOGGER.debug("sort using: {0}".format(",".join(self._sort_names)))
            sort_data = sorted(sort_data,
                               key=operator.itemgetter(*self._sort_names))

        # Create table data
        table_data = list()
        for dataset in sort_data:
            row = list()
            cnt = 0
            for key in self._keys:
                if key.name in dataset:
                    # Cnt number of final entries to avoid complete empty
                    # result entires
                    cnt += 1
                    # Set null value
                    if dataset[key.name] is None:
                        value = key.null_value
                    else:
                        # Format data values to create string representation
                        if key.format is not None:
                            value = jube2.util.format_value(key.format,
                                                            dataset[key.name])
                        else:
                            value = str(dataset[key.name])
                    row.append(value)
                else:
                    row.append(key.null_value)

            if cnt > 0:
                table_data.append(row)

        # Add data to toe result set
        result_data.add_key_value_data(self._keys, table_data,
                                       self._benchmark.id)

        return result_data
