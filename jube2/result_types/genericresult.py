# JUBE Benchmarking Environment
# Copyright (C) 2008-2022
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
"""GernicResultType definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

from jube2.result import Result
import jube2.log
import xml.etree.ElementTree as ET
import operator
import jube2.util.util
import jube2.util.output

LOGGER = jube2.log.get_logger(__name__)


class GenericResult(Result):

    """A generic result type"""

    class KeyValuesData(Result.ResultData):

        """Generic key value data"""

        def __init__(self, other_or_name):
            if type(other_or_name) is str:
                Result.ResultData.__init__(self, other_or_name)
            elif type(other_or_name) is Result.ResultData:
                self._name = other_or_name.name
            self._data = dict()
            self._benchmark_ids = list()

        @property
        def keys(self):
            """Return keys"""
            return self._data.keys()

        @property
        def data(self):
            """Return data"""
            return self._data

        @property
        def data_dict(self):
            """Return unordered dictionary representation of data"""
            return self._data

        @property
        def benchmark_ids(self):
            """Return benchmark ids"""
            return self._benchmark_ids

        def add_key_value_data(self, data, benchmark_ids):
            """Add a list of additional rows to current result data"""
            # Add new keys to for old rows
            for key in data.keys():
                if key not in self._data.keys():
                    if len(self._benchmark_ids) > 0:
                        self._data[key] = [None] * len(self._benchmark_ids)
                    else:
                        self._data[key] = list()

            number_of_new_values = len(list(data.values())[0])
            # Add new rows
            for key in self._data.keys():
                if key in data.keys():
                    self._data[key] += data[key]
                else:
                    self._data[key] += [None] * number_of_new_values

            if type(benchmark_ids) is int:
                self._benchmark_ids += [benchmark_ids] * number_of_new_values
            if type(benchmark_ids) is list:
                self._benchmark_ids += benchmark_ids

        def add_result_data(self, result_data):
            """Add additional result data"""
            if self.name != result_data.name:
                raise RuntimeError("Cannot combine to different result sets.")
            self.add_key_value_data(result_data.data,
                                    result_data.benchmark_ids)

        def create_result(self, show=True, filename=None, **kwargs):
            """Create result representation"""
            raise NotImplementedError("")

    class DataKey(object):
        """Class represents one data key """

        def __init__(self, name, title=None, unit=None):
            self._name = name
            self._title = title
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
            if self._title is not None:
                key_etree.attrib["title"] = self._title
            return key_etree

        def __eq__(self, other):
            return self.resulting_name == other.resulting_name

        def __hash__(self):
            return hash(self.resulting_name)

    def __init__(self, name, res_filter=None):
        Result.__init__(self, name, res_filter)
        self._keys = list()

    def add_key(self, name, title=None, unit=None):
        """Add an additional key to the dataset"""
        self._keys.append(GenericResult.DataKey(name, title, unit))

    def create_result_data(self, select, exclude):
        """Create result data"""
        result_data = GenericResult.KeyValuesData(self._name)

        if select is None:
            select = [key.name for key in self._keys]

        if exclude is None:
            exclude = []

        # Read pattern/parameter units if available
        units = self._load_units([key.name for key in self._keys])
        for key in self._keys:
            if key.name in units:
                key.unit = units[key.name]

        # Check if given names to select or exclude exist
        key_names = [key.name for key in self._keys]
        for select_name in select:
            if select_name not in key_names:
                LOGGER.warning("The result output does not contain a pattern "
                               "or parameter with the name '{0}'. This "
                               "name is ignored when selecting output."
                               .format(select_name))
        for exclude_name in exclude:
            if exclude_name not in key_names:
                LOGGER.warning("The result output does not contain a pattern "
                               "or parameter with the name '{0}'. This "
                               "name is ignored when excluding output."
                               .format(exclude_name))

        # Select and exclude table columns
        self._keys = [key for key in self._keys if key.name in select and \
                                                   key.name not in exclude]

        # Create result data
        data = dict()
        for dataset in self._analyse_data():
            new_data = dict()
            cnt = 0
            for key in self._keys:
                if key.name in dataset:
                    # Cnt number of final entries to avoid complete empty
                    # result entries
                    cnt += 1
                    new_data[key] = dataset[key.name]
                else:
                    new_data[key] = None
            if cnt > 0:
                for key in new_data:
                    if key not in data:
                        data[key] = list()
                    data[key].append(new_data[key])

        # Add data to the result set
        result_data.add_key_value_data(data, self._benchmark.id)

        return result_data
