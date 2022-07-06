#!/usr/bin/env python
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
"""Multiprocessing related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import re

import unittest
import shutil
import jube2.step
import jube2.parameter
import jube2.benchmark
import jube2.workpackage


class TestMultiprocessing(unittest.TestCase):

    """Multiprocessing test class"""

    def setUp(self):
        self.parallelParameter=jube2.parameter.StaticParameter(
            name='i',
            value= '",".join(str(i) for i in range(4))',
            separator=',',
            parameter_type='int',
            parameter_mode='python')
        self.parallelParameterset=jube2.parameter.Parameterset(name='paramet_set')
        self.parallelParameterset.add_parameter(self.parallelParameter)
        self.parallelStep=jube2.step.Step(name='parallel_execution', depend=set(), procs=2)
        self.parallelStep.add_uses(['param_set'])
        self.parallelOperation=jube2.step.Operation('echo "$i"', stdout_filename='stdout',
            stderr_filename='stderr',
            work_dir='.', error_filename='error')
        self.parallelStep.add_operation(self.parallelOperation)
        self.parallelBenchmark=jube2.benchmark.Benchmark(
            name='parallel_workpackages',
            outpath='bench_run',
            parametersets={'param_set': self.parallelParameterset},
            substitutesets={},
            filesets={},
            patternsets={},
            steps={'parallel_execution': self.parallelStep},
            analyser={},
            results={},
            results_order=[])

    def test_multiprocessing(self):
        """Test multiprocessing execution"""
        self.parallelBenchmark.new_run()
        shutil.rmtree('bench_run')


if __name__ == "__main__":
    unittest.main()
