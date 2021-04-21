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
import ast, os

from jube2.result_types.keyvaluesresult import KeyValuesResult
from jube2.result import Result
import xml.etree.ElementTree as ET
import jube2.log

LOGGER = jube2.log.get_logger(__name__)


class Database(KeyValuesResult):

    """A database result"""

    class DatabaseData(KeyValuesResult.KeyValuesData):

        """Database data"""

        def __init__(self, name_or_other, primekeys, db_file):
            if type(name_or_other) is KeyValuesResult.KeyValuesData:
                self._name = name_or_other.name
                self._keys = name_or_other.keys
                self._data = name_or_other.data
                self._benchmark_ids = name_or_other.benchmark_ids
            else:
                KeyValuesResult.KeyValuesData.__init__(self, name_or_other)
            self._primekeys = primekeys
            self._db_file = db_file

        def get_datatype(self, key):
                try:
                    key_type = ast.literal_eval(key)
                except ValueError:
                    return 'TEXT'
                except SyntaxError:
                    return 'TEXT'

                else:
                    if type(key_type) is int:
                        return 'INT'
                    elif type(key_type) is float:
                        return 'FLOAT'
                    else:
                        return 'TEXT'

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
            print("primekeys: ", self._primekeys)
            print("db_file: ", self._db_file)
            print('filename: {}'.format(filename))

            # check if all primekeys are in keys
            if not set(self._primekeys).issubset(set(col_names)):
                raise ValueError("primekeys are not in keys!")

            # define database file
            if self._db_file is not None and filename is not None:
                file_handle = open(filename, "w")
                file_handle.write(self._db_file)
                file_handle.close()
                # create directory path to db file, if it does not exist
                file_path_ind = self._db_file.rfind('/')
                if file_path_ind != -1:
                    if not os.path.exists(os.path.expanduser(self._db_file[:file_path_ind])):
                        os.makedirs(os.path.expanduser(self._db_file[:file_path_ind]))
                db_file = os.path.expanduser(self._db_file)
            elif filename is not None:
                db_file = filename
            else:
                return None

            # create database and insert the data
            con = sqlite3.connect(db_file)
            cur = con.cursor()

            # create a string of keys and their data type to create the database table
            key_dtypes = {key: self.get_datatype(data) for key,data in zip(col_names, self.data[0])}
            print("key_dtypes: ", key_dtypes)
            db_col_insert_types = str(key_dtypes).replace('{', '(').replace('}', ')').replace("'", '').replace(':', '')

            if len(self._primekeys) > 0:
                db_col_insert_types = db_col_insert_types[:-1] + ", PRIMARY KEY {})".format(tuple(self._primekeys))
            # create new table with a name of stored in variable self.name if it does not exists
            print("CREATE TABLE IF NOT EXISTS {} {};".format(self.name, db_col_insert_types))
            cur.execute("CREATE TABLE IF NOT EXISTS {} {};".format(self.name, db_col_insert_types))

            # check for primary keys in database table
            cur.execute('PRAGMA TABLE_INFO({})'.format(self.name))
            db_primary_keys = [i[1] for i in cur.fetchall() if i[5] != 0]
            if not set(self._primekeys)==set(db_primary_keys):
                raise ValueError("Modification of primary values is not supported. " +
                                 "Primary keys of table {} are {}".format(self.name, db_primary_keys))

            # compare self._keys with columns in db and exit on mismatch
            cur.execute("SELECT * FROM {}".format(self.name))
            col_name_list = [tup[0] for tup in cur.description]
            difference = set(col_name_list).symmetric_difference(set(col_names))
            list_difference = list(difference)
            if len(list_difference) != 0:
                print("diff list: ", list_difference)
                raise ValueError("key and db col mismatch")

            # insert or replace self.data in database
            #print([tuple(d) for d in self.data])
            replace_query = "REPLACE INTO {} {} VALUES (".format(self.name, tuple(col_names)) + "{}".format('?,'*len(col_names))[:-1] + ");"
            print(replace_query)
            cur.executemany(replace_query, [tuple(d) for d in self.data])

            con.commit()
            con.close()


    def __init__(self, name, res_filter=None, primekeys=None, db_file=None):
        KeyValuesResult.__init__(self, name, None, res_filter)
        self._primekeys = primekeys
        self._db_file = db_file

    def create_result_data(self, style=None):
        """Create result data"""
        result_data = KeyValuesResult.create_result_data(self)
        return Database.DatabaseData(result_data, self._primekeys, self._db_file)

    def etree_repr(self):
        """Return etree object representation"""
        result_etree = Result.etree_repr(self)
        database_etree = ET.SubElement(result_etree, "database")
        database_etree.attrib["name"] = self._name
        if self._res_filter is not None:
            database_etree.attrib["filter"] = self._res_filter
        for key in self._keys:
            database_etree.append(key.etree_repr())
        database_etree.attrib["primekeys"] = str(self._primekeys)
        database_etree.attrib["file"] = str(self._db_file)
        return result_etree
