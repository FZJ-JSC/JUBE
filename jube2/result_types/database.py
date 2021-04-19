# JUBE Benchmarking Environment
# Copyright (C) 2008-2021
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
"""Databasetype definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)
import sqlite3

from jube2.result_types.keyvaluesresult import KeyValuesResult
from jube2.result import Result
import xml.etree.ElementTree as ET
import jube2.log

LOGGER = jube2.log.get_logger(__name__)


class Database(KeyValuesResult):

    """A database result"""

    class DatabaseData(KeyValuesResult.KeyValuesData):

        """Database data"""

        def __init__(self, name_or_other):
            if type(name_or_other) is KeyValuesResult.KeyValuesData:
                self._name = name_or_other.name
                self._keys = name_or_other.keys
                self._data = name_or_other.data
                self._benchmark_ids = name_or_other.benchmark_ids
            else:
                KeyValuesResult.KeyValuesData.__init__(self, name_or_other)

        def create_result(self, show=True, filename=None, **kwargs):
            # Place for the magic #
            # show = If False do not show something on screen (result
            # only into file)
            # filename = name of standard output/datbase file
            # All keys: print([key.name for key in self._keys])
            print('create_result')
            col_names = [key.name for key in self._keys]
            print(tuple(col_names))
            # All data: print(self.data)
            print('ALL DATA:', self.data)
            print('self.name:', self.name)

            # create database and insert the data
            if filename is not None:
                print('filename: {}'.format(filename))

                con = sqlite3.connect(filename)
                cur = con.cursor()
                # create new table with a name of stored in variable self.name if it does not exists
                cur.execute("CREATE TABLE IF NOT EXISTS {} {};".format(self.name, tuple(col_names)))   #(my_val, my_txt)

                # compare self._keys with columns in db and exit on mismatch
                cur.execute("SELECT * FROM {}".format(self.name))
                col_name_list = [tup[0] for tup in cur.description]
                difference = set(col_name_list).symmetric_difference(set(col_names))
                list_difference = list(difference)
                if len(list_difference) != 0:
                    print("diff list: ", list_difference)
                    print("key and db col mismatch")
                    exit(1)

                # insert self.data in database
                #print([tuple(d) for d in self.data])
                print("INSERT INTO {} VALUES (".format(self.name) + "{}".format('?,'*len(col_names))[:-1] + ");")
                cur.executemany("INSERT INTO {} VALUES (".format(self.name) + "{}".format('?,'*len(col_names))[:-1] + ");", [tuple(d) for d in self.data])

                con.commit()
                con.close()


    def __init__(self, name, res_filter=None):
        KeyValuesResult.__init__(self, name, None, res_filter)

    def create_result_data(self, style=None):
        """Create result data"""
        result_data = KeyValuesResult.create_result_data(self)
        return Database.DatabaseData(result_data)

    def etree_repr(self):
        """Return etree object representation"""
        result_etree = Result.etree_repr(self)
        database_etree = ET.SubElement(result_etree, "database")
        database_etree.attrib["name"] = self._name
        if self._res_filter is not None:
            database_etree.attrib["filter"] = self._res_filter
        for key in self._keys:
            database_etree.append(key.etree_repr())
        return result_etree
