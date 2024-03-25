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
import jube2.benchmark
import jube2.parameter
import jube2.workpackage
import jube2.main
import subprocess

class TestStep(unittest.TestCase):

    """Step test class"""

    def setUp(self):
        self.para_cluster = \
            jube2.parameter.Parameter.create_parameter("cluster_module", "CM, DAM, ESB")
        self.paramset_cluster = jube2.parameter.Parameterset("cluster")
        self.paramset_cluster.add_parameter(self.para_cluster)

        self.para_acc = \
            jube2.parameter.Parameter.create_parameter("ACC",
                                                       "{'CM': '66', 'DAM': '77', 'ESB': '88'}"+
                                                       ".get('${cluster_module}', 0)",
                                                       parameter_mode="python")
        self.para_acc_step = \
            jube2.parameter.Parameter.create_parameter("ACC_STEP",
                                                       "{'sec': '${ACC}'}.get('$jube_step_name', 'NO_ACC')",
                                                       parameter_mode="python",
                                                       update_mode=jube2.parameter.STEP_MODE)
        self.parameterset = jube2.parameter.Parameterset("update_test")
        self.parameterset.add_parameter(self.para_acc)
        self.parameterset.add_parameter(self.para_acc_step)

        self.first_step = jube2.step.Step(name='first', depend=set())
        self.first_step.add_uses(['cluster', 'update_test'])
        operation = jube2.step.Operation('echo "${ACC}, ${ACC_STEP}"',
                                         stdout_filename='stdout',
                                         stderr_filename='stderr',
                                         work_dir='.', error_filename='error')
        self.first_step.add_operation(operation)

        self.second_step = jube2.step.Step(name='sec', depend={"first"})
        operation = jube2.step.Operation('echo "BEFORE ${ACC}, ${ACC_STEP}"',
                                         stdout_filename='stdout',
                                         stderr_filename='stderr',
                                         work_dir='.', error_filename='error')
        self.second_step.add_operation(operation)
        operation = jube2.step.Operation('', stdout_filename='stdout',
                                         stderr_filename='stderr',
                                         async_filename='ready',
                                         work_dir='.', error_filename='error')
        self.second_step.add_operation(operation)
        operation = jube2.step.Operation('echo "AFTER ${ACC}, ${ACC_STEP}"',
                                         stdout_filename='stdout',
                                         stderr_filename='stderr',
                                         work_dir='.', error_filename='error')
        self.second_step.add_operation(operation)
        self.bench_run_path = os.path.join(os.path.dirname(__file__), "bench_run")
        self.benchmark = jube2.benchmark.Benchmark(
            name='update_test',
            outpath=self.bench_run_path,
            parametersets={'update_test': self.parameterset,
                           "cluster": self.paramset_cluster},
            substitutesets={},
            filesets={},
            patternsets={},
            steps={'first': self.first_step, 'sec': self.second_step},
            analyser={},
            results={},
            results_order=[])

    def test_update_parameter(self):
        """Test update parameter"""
        if os.path.isdir(self.bench_run_path):
            shutil.rmtree(self.bench_run_path)
        self.benchmark.new_run()
        self.run_path = os.path.join(self.bench_run_path, "000000")

        # Test if first step was succesful
        output = ["66, NO_ACC\n", "77, NO_ACC\n", "88, NO_ACC\n"]
        for i, path in enumerate(["000000_first", "000001_first", "000002_first"]):
            # Check done file
            done_path = os.path.join(self.run_path, path, "done")
            self.assertTrue(os.path.isfile(done_path))
            # Check output
            stdout_path = os.path.join(self.run_path, path, "work", "stdout")
            f = open(stdout_path, "r")
            stdout = f.read()
            f.close()
            self.assertEqual(stdout, output[i])


        # Test if second step was succesful until done file
        output = ["BEFORE 66, 66\n", "BEFORE 77, 77\n", "BEFORE 88, 88\n"]
        for i, path in enumerate(["000003_sec", "000004_sec", "000005_sec"]):
            # Check wp_done file
            for wp in ['wp_done_00', 'wp_done_01']:
                wp_done_path = os.path.join(self.run_path, path, wp)
                self.assertTrue(os.path.isfile(wp_done_path))
            # Check output
            stdout_path = os.path.join(self.run_path, path, "work", "stdout")
            f = open(stdout_path, "r")
            stdout = f.read()
            f.close()
            self.assertEqual(stdout, output[i])
            # Set ready-file to continue run
            ready_path = os.path.join(self.run_path, path, "work", "ready")
            f = open(ready_path, "w")
            f.close()

        # Continue run
        jube2.main.main(["continue", self.bench_run_path])

        # Test if continue was succesful
        output = ["BEFORE 66, 66\nAFTER 66, 66\n", "BEFORE 77, 77\nAFTER 77, 77\n",
                  "BEFORE 88, 88\nAFTER 88, 88\n"]
        for i, path in enumerate(["000003_sec", "000004_sec", "000005_sec"]):
            # Check done file
            done_path = os.path.join(self.run_path, path, "done")
            self.assertTrue(os.path.isfile(done_path))
            # Check output
            stdout_path = os.path.join(self.run_path, path, "work", "stdout")
            f = open(stdout_path, "r")
            stdout = f.read()
            f.close()
            self.assertEqual(stdout, output[i])

    def tearDown(self)->None:
        shutil.rmtree(self.bench_run_path)


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

        if os.path.exists(os.path.join(self.currWorkDir, 'bench_run')):
            shutil.rmtree(os.path.join(self.currWorkDir, 'bench_run'))
        os.makedirs(os.path.join(self.currWorkDir,
                    'bench_run/000000/000000_execute/work'))

    def test_operation_execution(self):
        """Test operation execution"""
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

    def test_wait_for_done_file(self):
        """Test operation execution"""
        # Set done file to wait for
        self.operation._async_filename = 'ready'
        # First run (done file not existing -> not done)
        continue_op, continue_cycle = self.operation.execute(self.parameter_dict,
                                         self.work_dir, environment=self.environment)
        self.assertTrue(continue_cycle)
        self.assertFalse(continue_op)
        # Continue (done file not existing -> not done)
        continue_op, continue_cycle = self.operation.execute(self.parameter_dict,
                                         self.work_dir, environment=self.environment)
        self.assertTrue(continue_cycle)
        self.assertFalse(continue_op)
        # Create ready file
        open(os.path.join(self.currWorkDir, 'bench_run/000000/000000_execute/work',
                          'ready'), 'a').close()
        # Continue (done file existing -> done)
        continue_op, continue_cycle = self.operation.execute(self.parameter_dict,
                                         self.work_dir, environment=self.environment)
        self.assertTrue(continue_cycle)
        self.assertTrue(continue_op)

    def tearDown(self):
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
