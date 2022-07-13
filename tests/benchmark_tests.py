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
"""Benchmark related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import re
import unittest
import shutil
import os
import jube2.step
import jube2.parameter
import jube2.benchmark
import jube2.workpackage


class TestBenchmark(unittest.TestCase):

    """Benchmark test class"""

    def setUp(self):
        self.parameter = jube2.parameter.StaticParameter(
            name='i',
            value='",".join(str(i) for i in range(4))',
            separator=',',
            parameter_type='int',
            parameter_mode='python')
        self.parameterset = jube2.parameter.Parameterset(name='param_set')
        self.parameterset.add_parameter(self.parameter)
        self.step = jube2.step.Step(name='execution', depend=set())
        self.step.add_uses(['param_set'])
        self.operation = jube2.step.Operation('echo "$i"', stdout_filename='stdout',
                                              stderr_filename='stderr',
                                              work_dir='.', error_filename='error')
        self.step.add_operation(self.operation)
        self.benchmark = jube2.benchmark.Benchmark(
            name='workpackages',
            outpath='bench_run',
            parametersets={'param_set': self.parameterset},
            substitutesets={},
            filesets={},
            patternsets={},
            steps={'execution': self.step},
            analyser={},
            results={},
            results_order=[])

    def test_benchmark_execution(self):
        """Test benchmark execution"""
        if os.path.isdir("bench_run"):
            shutil.rmtree('bench_run')
        self.benchmark.new_run()
        for i in ["000000", "000001", "000002", "000003"]:
            for j in ["stdout", "stderr"]:
                self.assertTrue(os.path.isfile(
                    "bench_run/000000/"+i+"_execution/work/"+j))
        shutil.rmtree('bench_run')


if __name__ == "__main__":
    unittest.main()
