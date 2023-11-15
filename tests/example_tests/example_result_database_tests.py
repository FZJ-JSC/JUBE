#!/usr/bin/env python3
# JUBE Benchmarking Environment
# Copyright (C) 2008-2023
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
"""Test the cycle example"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import sqlite3
import os
from examples_tests import TestCase

class TestResultDatabaseExample(TestCase.TestExample):

    """Class for testing the result_database example"""

    @classmethod
    def setUpClass(cls):
        '''
        Automatically called method before tests in the class are run.

        Create the necessary variables and paths for the specific example
        '''
        cls._name = "result_database"
        cls._stdout = ["Number: "+ number for number in ["1", "2", "4"]]
        cls._stdout = [cls._stdout, cls._stdout]
        super(TestResultDatabaseExample, cls).setUpClass()
        super(TestResultDatabaseExample, cls)._execute_commands(["-r"])

    def test_for_equal_result_data(self):
        '''
        Overwrites the original test (TestExample.test_for_equal_result_data())
        for the result output to allow an example specific test.
        '''
        key_names = ["number", "number_pat"]
        keys = [[1, 2, 4], [1, 2, 4]]
        for run_path, command_wps in self._wp_paths.items():
            #Get database file
            database_path = os.path.join(run_path, "result",
                                           "results.dat")

            #Check existence of database file
            self.assertTrue(os.path.exists(database_path))
    
            #Get column names and database table content of database file
            con = sqlite3.connect(database_path)
            cur = con.cursor()
            cur.execute("SELECT * FROM {}".format("results"))
            db_col_names = [tup[0] for tup in cur.description]
            db_content = cur.fetchall()
            db_content = [list(i) for i in db_content]
            db_content = list(map(list, zip(*db_content)))
            con.close()
    
            #Get column names and database table content of database file
            self.assertEqual(db_col_names, key_names, "Error: Database in file {0}"
                             "contains the wrong keys".format(database_path))
            self.assertEqual(db_content, keys, "Error: Database in file {0}"
                             "has the wrong content".format(database_path))

if __name__ == "__main__":
    unittest.main()
