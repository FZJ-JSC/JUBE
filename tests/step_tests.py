#!/usr/bin/env python3
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
"""Step related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import re
import unittest
import shutil
import os
import sys
import jube2.step
import subprocess


class TestOperation(unittest.TestCase):

    """Operation test class"""

    def setUp(self):
        self.echoPath = subprocess.check_output(['which', 'echo']).decode(
            sys.stdout.encoding)
        self.echoPath = self.echoPath.replace('\n', '')
        self.currWorkDir = os.getcwd()
        self.operation = jube2.step.Operation(self.echoPath+' Test', stdout_filename='stdout',
                                              stderr_filename='stderr', work_dir='.', error_filename='error')
        self.parameter_dict = {
            'param': 'p1',
            'jube_benchmark_id': '0',
            'jube_benchmark_padid': '000000',
            'jube_benchmark_name': 'do_log_test',
            'jube_benchmark_home': self.currWorkDir,
            'jube_benchmark_rundir': self.currWorkDir+'/bench_run/000000',
            'jube_benchmark_start': '2022-07-12T16:23:32',
            'jube_step_name': 'execute',
            'jube_step_iterations': '1',
            'jube_step_cycles': '1',
            'jube_wp_cycle': '0',
            'jube_wp_id': '0',
            'jube_wp_padid': '000000',
            'jube_wp_iteration': '0',
            'jube_wp_relpath': 'bench_run/000000/000000_execute/work',
            'jube_wp_abspath': self.currWorkDir+'/bench_run/000000/000000_execute/work',
            'jube_wp_envstr': '',
            'jube_wp_envlist': ''}
        self.work_dir = "bench_run/000000/000000_execute/work"
        self.environment = {'TEST': 'test'}

    def test_operation_execution(self):
        """Test operation execution"""
        if os.path.exists(os.path.join(self.currWorkDir, 'bench_run')):
            shutil.rmtree(os.path.join(self.currWorkDir, 'bench_run'))
        os.makedirs(os.path.join(self.currWorkDir,
                    'bench_run/000000/000000_execute/work'))

        self.operation.execute(self.parameter_dict,
                               self.work_dir, environment=self.environment)

        self.assertTrue(os.path.exists(os.path.join(
            self.currWorkDir, 'bench_run/000000/000000_execute/work/stdout')))
        self.assertTrue(os.path.exists(os.path.join(
            self.currWorkDir, 'bench_run/000000/000000_execute/work/stderr')))
        self.assertTrue(os.stat(os.path.join(
            self.currWorkDir, 'bench_run/000000/000000_execute/work/stderr')).st_size == 0)

        # check the content of the stdout file
        stdoutFileHandle = open(os.path.join(
            self.currWorkDir, 'bench_run/000000/000000_execute/work/stdout'), mode='r')
        line = stdoutFileHandle.readline()
        self.assertTrue(line == 'Test\n')
        line = stdoutFileHandle.readline()
        self.assertTrue(line == '')
        stdoutFileHandle.close()

        shutil.rmtree(os.path.join(self.currWorkDir, 'bench_run'))


class TestDoLog(unittest.TestCase):

    """DoLog test class"""

    def setUp(self):
        self.currWorkDir = os.getcwd()
        self.environment = {'TEST': 'test'}
        self.dolog = jube2.step.DoLog(
            log_dir=self.currWorkDir, log_file='do_log', initial_env=self.environment)
        self.dolog_variable_path = jube2.step.DoLog(
            log_dir=self.currWorkDir, log_file='${path_variable}/do_log', initial_env=self.environment)
        self.echoPath = subprocess.check_output(['which', 'echo']).decode(
            sys.stdout.encoding)
        self.echoPath = self.echoPath.replace('\n', '')

    def test_do_log_content(self):
        """Test do log creation"""
        if os.path.exists(os.path.join(self.currWorkDir, 'do_log')):
            os.remove(os.path.join(self.currWorkDir, 'do_log'))

        self.dolog.store_do(do=self.echoPath+' Test1', shell='/bin/sh', work_dir=os.path.join(
            self.currWorkDir, 'work'))
        self.dolog.store_do(do=self.echoPath+' $TEST', shell='/bin/sh', work_dir=os.path.join(
            self.currWorkDir, 'work'))
        self.dolog.store_do(do=self.echoPath+' Test2', shell='/bin/sh', work_dir=os.path.join(
            self.currWorkDir, 'misc'))

        self.assertTrue(os.path.exists(
            os.path.join(self.currWorkDir, 'do_log')))

        # Check the content of the do_log file
        dologFileHandle = open(os.path.join(
            self.currWorkDir, 'do_log'), mode='r')
        line = dologFileHandle.readline()
        self.assertTrue(line == '#!/bin/sh\n')
        line = dologFileHandle.readline()
        self.assertTrue(line == '\n')
        line = dologFileHandle.readline()
        self.assertTrue(line == "set TEST='test'\n")
        line = dologFileHandle.readline()
        self.assertTrue(line == "\n")
        line = dologFileHandle.readline()
        self.assertTrue(line == 'cd '+os.path.join(
            self.currWorkDir, 'work')+'\n')
        line = dologFileHandle.readline()
        self.assertTrue(line == self.echoPath+' Test1\n')
        line = dologFileHandle.readline()
        self.assertTrue(line == self.echoPath+' $TEST\n')
        line = dologFileHandle.readline()
        self.assertTrue(line == 'cd '+os.path.join(
            self.currWorkDir, 'misc')+'\n')
        line = dologFileHandle.readline()
        self.assertTrue(line == self.echoPath+' Test2\n')
        line = dologFileHandle.readline()
        self.assertTrue(line == '')
        dologFileHandle.close()

        os.remove(os.path.join(self.currWorkDir, 'do_log'))

    def test_do_log_path_subsitution(self):
        """Test do log creation"""
        if os.path.exists(os.path.join(self.currWorkDir, 'path/do_log')):
            os.remove(os.path.join(self.currWorkDir, 'path/do_log'))

        if os.path.exists(os.path.join(self.currWorkDir, 'path')):
            os.rmdir(os.path.join(self.currWorkDir, 'path'))

        self.dolog_variable_path.store_do(do=self.echoPath+' Test1', shell='/bin/sh', work_dir=os.path.join(
            self.currWorkDir, 'work'), parameter_dict={'path_variable': 'path'})

        self.assertTrue(os.path.exists(
            os.path.join(self.currWorkDir, 'path/do_log')))

        os.remove(os.path.join(self.currWorkDir, 'path/do_log'))
        os.rmdir(os.path.join(self.currWorkDir, 'path'))


if __name__ == "__main__":
    unittest.main()
