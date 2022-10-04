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
"""Databasetype definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)
import sqlite3
import ast
import os

from jube2.result_types.genericresult import GenericResult
from jube2.result import Result
import xml.etree.ElementTree as ET
import jube2.log

LOGGER = jube2.log.get_logger(__name__)


class Database(GenericResult):

    """A database result"""

    class DatabaseData(GenericResult.KeyValuesData):

        """Database data"""

        def __init__(self, name_or_other, primekeys, db_file):
            if type(name_or_other) is GenericResult.KeyValuesData:
                self._name = name_or_other.name
                #self._keys = name_or_other.keys
                self._data = name_or_other.data
                self._benchmark_ids = name_or_other.benchmark_ids
            else:
                GenericResult.KeyValuesData.__init__(self, name_or_other)
            self._primekeys = primekeys
            self._db_file = None if db_file == "None" else db_file

        def create_result(self, show=True, filename=None, **kwargs):
            # Place for the magic #
            # show = If False do not show something on screen (result
            # only into file)
            # filename = name of standard output/datbase file
            # All keys: print([key.name for key in self._keys])
            #col_names = [key.name for key in self._keys]
            # All data: print(self.data)
            keys = [k.name for k in self._data.keys()]

            # check if all primekeys are in keys
            if not set(self._primekeys).issubset(set(keys)):
                raise ValueError("primekeys are not included in <key>!")

            # define database file
            if self._db_file is not None and filename is not None:
                file_handle = open(filename, "w")
                file_handle.write(self._db_file)
                file_handle.close()
                # create directory path to db file, if it does not exist
                file_path_ind = self._db_file.rfind('/')
                if file_path_ind != -1:
                    # modify when Python2.7 support is dropped (potential race condition)
                    if not os.path.exists(os.path.expanduser(self._db_file[:file_path_ind])):
                        os.makedirs(os.path.expanduser(
                            self._db_file[:file_path_ind]))
                db_file = os.path.expanduser(self._db_file)
            elif filename is not None:
                db_file = filename
            else:
                return None

            # create database and insert the data
            con = sqlite3.connect(db_file)
            cur = con.cursor()

            # create a string of keys and their data type to create the database table
            key_dtypes = {k.name: type(v[0]).__name__.replace(
                'str', 'text') for (k, v) in self._data.items()}
            db_col_insert_types = str(key_dtypes).replace(
                '{', '(').replace('}', ')').replace("'", '').replace(':', '')

            if len(self._primekeys) > 0:
                db_col_insert_types = db_col_insert_types[:-1] + \
                    ", PRIMARY KEY ({}))".format(', '.join(map(repr, self._primekeys)))
            # create new table with a name of stored in variable self.name if it does not exists
            LOGGER.debug("CREATE TABLE IF NOT EXISTS {} {};".format(
                self.name, db_col_insert_types))
            cur.execute("CREATE TABLE IF NOT EXISTS {} {};".format(
                self.name, db_col_insert_types))

            # check for primary keys in database table
            cur.execute('PRAGMA TABLE_INFO({})'.format(self.name))
            db_primary_keys = [i[1] for i in cur.fetchall() if i[5] != 0]
            if not set(self._primekeys) == set(db_primary_keys):
                raise ValueError("Modification of primary values is not supported. " +
                                 "Primary keys of table {} are {}".format(self.name, db_primary_keys))

            # compare self._keys with columns in db and add new column in the database if it does not exist
            cur.execute("SELECT * FROM {}".format(self.name))
            db_col_names = [tup[0] for tup in cur.description]

            # delete columns, which were removed as keys in this execution
            diff_col_list = list(set(db_col_names).difference(keys))
            if len(diff_col_list) != 0:
                for col in diff_col_list:
                    LOGGER.debug(
                        "ALTER TABLE {} DROP COLUMN {}".format(self.name, col))
                    cur.execute(
                        "ALTER TABLE {} DROP COLUMN {}".format(self.name, col))

            # add columns, which were added as keys in this execution
            diff_col_list = list(set(keys).difference(db_col_names))
            if len(diff_col_list) != 0:
                for col in diff_col_list:
                    LOGGER.debug("ALTER TABLE {} ADD COLUMN {} {}".format(
                        self.name, col, type(col).__name__.replace('str', 'text')))
                    cur.execute("ALTER TABLE {} ADD COLUMN {} {}".format(
                        self.name, col, type(col).__name__.replace('str', 'text')))

            # insert or replace self.data in database
            replace_query = "REPLACE INTO {} {} VALUES (".format(
                self.name, tuple(keys)) + "{}".format('?,'*len(keys))[:-1] + ");"
            LOGGER.debug(replace_query)
            cur.executemany(
                replace_query, [d for d in list(zip(*self._data.values()))])

            con.commit()
            con.close()

            # Print database location to screen and result.log
            LOGGER.info("Database location of id {}: {}".format(
                self._benchmark_ids[0], db_file))

    def __init__(self, name, res_filter=None, primekeys=None, db_file=None):
        GenericResult.__init__(self, name, res_filter)
        self._primekeys = primekeys
        self._db_file = db_file

    def create_result_data(self, style=None):
        """Create result data"""
        result_data = GenericResult.create_result_data(self)
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
