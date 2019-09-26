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
"""Step related tests"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import unittest
import jube2.step
import jube2.parameter
import jube2.benchmark


class TestStep(unittest.TestCase):

    """Step test class"""

    def setUp(self):
        self.std_step = jube2.step.Step("std", set())
        self.shared_step = jube2.step.Step("std", set(), shared_name = "shared")
        etree_set = set()
        etree_set.add("test")
        self.etree_step = jube2.step.Step("etree", etree_set, iterations = 2, 
                                          alt_work_dir = "/test", max_wps="1",
                                          shared_name = "etree", export = True,
                                          active="false", suffix="te", cycles=2)

    def test_std(self):
        #Test getter
        self.assertEqual(self.std_step.name, "std")
        self.assertEqual(self.std_step.active, "true")
        self.assertFalse(self.std_step.export)
        self.assertEqual(self.std_step.iterations, 1)
        self.assertEqual(self.std_step.cycles, 1)
        self.assertIsNone(self.std_step.shared_link_name)
        self.assertEqual(self.std_step.max_wps, "0")
        self.assertIsNone(self.std_step.alt_work_dir)
        self.assertEqual(self.std_step.use, [])
        self.assertEqual(self.std_step.suffix, "")
        self.assertEqual(self.std_step.operations, [])
        self.assertEqual(self.std_step.depend, set())
        
        #test represent
        self.same_step = jube2.step.Step("std", set())
        self.assertEqual(str(self.std_step), str(self.same_step))
        
        #test add functions
        self.test_operation = jube2.step.Operation("pwd")
        self.std_step.add_operation(self.test_operation)
        self.assertEqual(str(self.std_step.operations), "[pwd]")
        
        test_paraset = jube2.parameter.Parameterset("test")
        self.std_step.add_uses([test_paraset.name])
        self.assertEqual(self.std_step.use, [[test_paraset.name]])
        with self.assertRaises(ValueError): 
            self.std_step.add_uses([test_paraset.name])
            
        #test get_used_sets
        available_sets = set()
        available_sets.add(test_paraset.name)
        self.assertEqual(self.std_step.get_used_sets(available_sets), ["test"])
        
        
    def test_shared_folder_path(self):
        self.assertEqual(self.std_step.shared_folder_path(None), "")
        self.assertEqual(self.shared_step.shared_folder_path("dir"),
                         "dir/std_shared")
        self.assertEqual(self.shared_step.shared_folder_path("dir", dict()),
                         "dir/std_shared")
        
    def test_etree(self):
        self.test_operation = jube2.step.Operation("pwd")
        self.etree_step.add_operation(self.test_operation)
        self.etree_step.add_uses(["any_fileset"])
        etree_repr = self.etree_step.etree_repr() 
        
        self.assertEqual(etree_repr.attrib["name"], "etree")
        self.assertEqual(etree_repr.attrib["depend"], "test")
        self.assertEqual(etree_repr.attrib["work_dir"], "/test")
        self.assertEqual(etree_repr.attrib["shared"], "etree")
        self.assertEqual(etree_repr.attrib["active"], "false")
        self.assertEqual(etree_repr.attrib["suffix"], "te")
        self.assertEqual(etree_repr.attrib["export"], "true")
        self.assertEqual(etree_repr.attrib["max_async"], "1")
        self.assertEqual(etree_repr.attrib["iterations"], "2")
        self.assertEqual(etree_repr.attrib["cycles"], "2")
        self.assertIsNone(etree_repr.text)
    
    def test_get_jube_parameterset(self):
        paraset = jube2.parameter.Parameterset()
        paraset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_step_name", self.std_step.name,
                             update_mode=jube2.parameter.JUBE_MODE))
        paraset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_step_iterations",
                             str(self.std_step.iterations), 
                             parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))
        paraset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_step_cycles", str(self.std_step.cycles),
                             parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))
        paraset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_cycle", "0", parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))
        
        self.assertEqual(str(self.std_step.get_jube_parameterset()),
                        str(paraset))
        
    def test_create_workpackages(self):
        pass
        #bench = jube2.benchmark.Benchmark("Test", "/test", None, None, None,
        #                                  None, {}, {}, {}, "/test")
        #paraset = jube2.parameter.Parameterset()
        #paraset.add_parameter(
        #    jube2.parameter.Parameter.
        #    create_parameter("jube_step_name", self.std_step.name))
        #    
        #self.std_step.create_workpackages(bench, paraset)
    
class TestOperation(unittest.TestCase):
    
    """Operation test class"""
    
    def setUp(self):
        self.std_oper = jube2.step.Operation("pwd")
        self.etree_oper = jube2.step.Operation("ll", "/test", "/test", "/test",
                                               "false", True, "/test", "/test")
        self.execute_oper = jube2.step.Operation("pwd", stdout_filename="test",
                                                 stderr_filename="test", 
                                                 work_dir="test2")
        self.notactive_oper = jube2.step.Operation("pwd", active="false")
    
    def test_std(self):
        #test getter
        self.assertIsNone(self.std_oper.stdout_filename)
        self.assertIsNone(self.std_oper.stderr_filename)
        self.assertIsNone(self.std_oper.async_filename)
        self.assertFalse(self.std_oper.shared)
        self.assertEqual(str(self.std_oper), "pwd")
        self.assertIsNone(self.std_oper.stdout_filename)
        self.assertIsNone(self.std_oper.stdout_filename)
        self.assertIsNone(self.std_oper.stdout_filename)
        param_dict = {"test": 5}
        self.assertTrue(self.std_oper.active(param_dict))
        
    
    def test_etree(self):
        etree = self.etree_oper.etree_repr()
        self.assertEqual(etree.text, "ll")
        self.assertEqual(etree.attrib["done_file"], "/test")
        self.assertEqual(etree.attrib["break_file"], "/test")
        self.assertEqual(etree.attrib["stdout"], "/test")
        self.assertEqual(etree.attrib["stderr"], "/test")
        self.assertEqual(etree.attrib["active"], "false")
        self.assertTrue(etree.attrib["shared"])
        self.assertEqual(etree.attrib["work_dir"], "/test")
    
    

if __name__ == "__main__":
    unittest.main()
