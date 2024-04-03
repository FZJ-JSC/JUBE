#!/usr/bin/env python3
# JUBE Benchmarking Environment
# Copyright (C) 2008-2024
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
"""Result database related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import re
import unittest
import sqlite3
import os
import jube2.result_types.database
import jube2.result_types.keyvaluesresult


class TestResultDatabase(unittest.TestCase):

    """Result database test class"""

    def setUp(self):
        self.databaseFileName = "database.dat"
        self.dataKeyNames = ["dataKeyName1", "dataKeyName2"]
        self.dataKeys = [[2, 4], [8, 4]]
        self.dataBaseTableName = "databaseKeyValuesData"
        keyValuesDataInstance = jube2.result_types.keyvaluesresult.KeyValuesResult.KeyValuesData(
            self.dataBaseTableName)
        databaseDataInstance = jube2.result_types.database.Database.DatabaseData(
            keyValuesDataInstance, [], None)
        datakey1 = jube2.result_types.keyvaluesresult.KeyValuesResult.DataKey(
            self.dataKeyNames[0], None, None)
        datakey2 = jube2.result_types.keyvaluesresult.KeyValuesResult.DataKey(
            self.dataKeyNames[1], None, None)
        databaseDataInstance._keys = [datakey1, datakey2]
        databaseDataInstance._data = [d for d in list(zip(*self.dataKeys))]
        databaseDataInstance._benchmark_ids = [0]
        databaseDataInstance.create_result(
            True, self.databaseFileName)

    def test_database(self):
        """Test database"""
        # check existence of database file
        self.assertTrue(os.path.exists(self.databaseFileName))

        # check column names and database table content of database file
        con = sqlite3.connect(self.databaseFileName)
        cur = con.cursor()
        cur.execute("SELECT * FROM {}".format(self.dataBaseTableName))
        db_col_names = [tup[0] for tup in cur.description]
        db_content = cur.fetchall()
        db_content = [list(i) for i in db_content]
        db_content = list(map(list, zip(*db_content)))
        con.close()
        self.assertEqual(db_col_names, self.dataKeyNames)
        self.assertEqual(db_content, self.dataKeys)

        # delete database file
        os.remove(self.databaseFileName)


if __name__ == "__main__":
    unittest.main()
