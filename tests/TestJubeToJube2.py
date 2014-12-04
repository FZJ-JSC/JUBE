"""Nose-test routines"""

from __future__ import (print_function,
                        division)


import jube2.jubetojube2
import unittest

class TestJubeToJube2(unittest.TestCase):
    """Check _JubeStep class"""
    def setUp(self):
         self.step = jube2.jubetojube2._JubeStep("compile")
         self.step.cname = "compile_ref"
         
         
    def test_jube_step_prop(self):
        """Check properties and setter"""
        self.assertEqual(self.step.name, "compile")
        self.assertEqual(self.step.cname, "compile_ref")
        
    
if __name__ == "__main__":
    unittest.main()

