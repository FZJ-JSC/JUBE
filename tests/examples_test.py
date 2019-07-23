#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
"""Test the examples"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import sys
import filecmp
import re
import glob
import unittest
import os.path
import jube2.main


EXAMPLES_PREFIX = os.path.join(os.path.dirname(__file__), "../examples")


class TestExamples(unittest.TestCase):

        
    
    """Class for testing the included examples"""
    def test_examples(self):
        """Main function"""
        examples_tasks = [
            ExampleChecker("environment", "environment.xml"),
            ExampleChecker("jobsystem", "jobsystem.xml", debug=True),
            ExampleChecker("result_creation", "result_creation.xml"),
            ExampleChecker("files_and_sub", "files_and_sub.xml"),
            ExampleChecker("dependencies", "dependencies.xml"),
            ExampleChecker("tagging", "tagging.xml"),
            ExampleChecker("parameterspace", "parameterspace.xml"),
            ExampleChecker("parameter_dependencies", "parameter_dependencies.xml"),
            ExampleChecker("scripting_parameter", "scripting_parameter.xml"),
            ExampleChecker("scripting_pattern", "scripting_pattern.xml"),
            ExampleChecker("statistic", "statistic.xml"),
            ExampleChecker("include", "main.xml"),
            ExampleChecker("shared", "shared.xml"),
            ExampleChecker("hello_world", "hello_world.xml"),
            ExampleChecker("iterations", "iterations.xml"),
            ExampleChecker("cycle", "cycle.xml"),
        ]

        for checker in examples_tasks:
            self.assertTrue(checker.run())

        


class ExampleChecker(object):
    """Class for checking examples"""
    
    #def _check_function():

        
    def __init__(self, bench_path, xml_file, bench_run_path=None,
                 check_function=True, debug=False):
        """Init instance.

        The check_function should return a bool value to indicate the
        success of failure of the test.

        """
        if str(sys.argv) == "-u":
            self._update = True
        else:
            self._update = False
        self._bench_name = bench_path
        self._xml_file = os.path.join(EXAMPLES_PREFIX, bench_path, xml_file)

        self._bench_run_path = bench_run_path or os.path.join(
            EXAMPLES_PREFIX, bench_path, "bench_run")
        

        self._check_function = check_function
        self._debug = debug

        

    def run(self):
        """Run example"""
        success = True
        debug = "--debug" if self._debug else ""
        jube2.main.main("{0} run {1} -r".format(debug, self._xml_file). split())

        if self._check_function:
            success = self._check()
        
        if not self._update:
            self._delete()
        else:
            self.update()
        return success


    #erstellt neue Check-Dateien
    def update(self):
        #Geht in jube/tests
        os.chdir(os.path.dirname(__file__))
        #erstellt neue Check-Datei
        check = file(os.path.join(os.path.abspath("."), "examples_output", "check_" + self._bench_name + ".txt"), 'w')
        #Oeffnet run.log des jeweilige Tests und kopiert Inhalt in Check-Datei
        if not self._debug:
            #sucht neuste Datei
            latest_file = max(glob.glob(os.path.join(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name,"bench_run")), '*/')), key=os.path.getmtime) 
            f = open(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name,"bench_run") , latest_file , "run.log"))
            for line in f.readlines():
                check.write(line)
            f.close()
        check.close()
        self._delete()

    #vergleicht zeilenweise Ausgabe mit Check-Datei 
    def _check(self):
        success = True
        if not self._debug:
            latest_file = max(glob.glob(os.path.join(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name,"bench_run")), '*/')), key=os.path.getmtime)
            ausgabe = open(os.path.join(EXAMPLES_PREFIX, os.path.join(self._bench_name,"bench_run") , latest_file , "run.log"), 'r')
            check = open(os.path.join(os.path.abspath("."), "examples_output", "check_" + self._bench_name + ".txt"), 'r')
            success = ExampleChecker._tabfinder(ausgabe, check)
            for l1, l2 in zip(ausgabe, check):
                if not re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l1):
                    ausgabeMatcher = re.match('^(?:.+?:){4}(.*?)(?:stdout.*?)?(?:stderr.*?)?$', l1)
                    checkMatcher = re.match('^(?:.+?:){4}(.*?)(?:stdout.*?)?(?:stderr.*?)?$', l2)
                    if ausgabeMatcher.group(1) != checkMatcher.group(1):
                        return False
        return success
    
    @staticmethod
    def _tabfinder(file1, file2):
        success = False
        ignore = ["_home", "_id", "_padid", "_rundir", "_start", "_abspath", "_relpath"]
        vergleichbar = True
        ausgabe = ""
        ausgabeDic = {}
        check = ""
        checkDic = {}
        
        for l1,l2 in zip(file1, file2):
            if re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l1):
                ausgabe += l1
            if re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l2):
                check += l2

        for l1,l2 in zip(ausgabe.split("\n"), check.split("\n")):
            ausgabeTab = re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l1)
            checkTab = re.match('^(?:.+?:){4}(?:\s){10}(.*)(?:.*?\||\+)(.*)', l2)
            if ausgabeTab:
                ausgabeDic[ausgabeTab.group(1).replace(" ", "")] = ausgabeTab.group(2).replace(" ", "")
            if checkTab:
                checkDic[checkTab.group(1).replace(" ", "")] = checkTab.group(2).replace(" ", "")

           
        for key in ausgabeDic:
            for elem in ignore:
                if elem in key:
                    vergleichbar = False
            if vergleichbar:
                if key in checkDic:
                    if ausgabeDic[key] == checkDic[key]:
                        success = True
                if success == False:
                    return False

        return success
                

    #loescht
    def _delete(self):
        print(self._bench_run_path)
        if not self._debug:
            jube2.main.main("remove -f {0}".format(self._bench_run_path).
                            split())
        




if __name__ == "__main__":
    unittest.main()

