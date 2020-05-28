# JUBE Benchmarking Environment
# Copyright (C) 2008-2020
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
"""YAML to XML converter"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as etree
import xml.dom.minidom as DOM
try:
    import yaml
except ImportError:
    pass
import jube2.log
import jube2.util.output
import os
try:
    from StringIO import StringIO as IOStream
except ImportError:
    from io import BytesIO as IOStream

LOGGER = jube2.log.get_logger(__name__)


class YAML_Converter(object):

    """YAML to XML converter"""

    allowed_tags = \
        {"/": ["benchmark", "parameterset", "comment", "step",
               "fileset", "substituteset", "analyser", "result", "patternset",
               "selection", "include-path"],
         "/benchmark": ["benchmark", "parameterset", "fileset",
                        "substituteset", "patternset", "selection",
                        "include-path"],
         "benchmark": ["parameterset", "comment", "step", "fileset",
                       "substituteset", "analyser", "result", "patternset"],
         "analyse": ["file"], "analyser": ["use", "analyse"],
         "fileset": ["link", "copy", "prepare"],
         "include-path": ["path"], "parameterset": ["parameter"],
         "patternset": ["pattern"], "result": ["use", "table", "syslog"],
         "selection": ["not", "only"], "step": ["use", "do"],
         "substituteset": ["iofile", "sub"], "syslog": ["key"],
         "table": ["column"]}

    def __init__(self, path):
        try:
            self._path = path
            yaml.add_constructor("!include", self.__yaml_include)
            self._int_file = IOStream()
            self.__convert()
        except NameError:
            raise NameError("yaml module not available; either install it " +
                            "(https://pyyaml.org), or switch to .xml input " +
                            "files.")

    def __convert(self):
        """ Opens given file, make a Tree of it and print it """
        LOGGER.debug("  Start YAML to XML file conversion for file {0}".format(
            self._path))
        with open(self._path, "r") as file_handle:
            xmltree = etree.Element('jube')
            YAML_Converter.create_headtags(
                yaml.load(file_handle.read()), xmltree)
            xml = jube2.util.output.element_tree_tostring(
                xmltree, encoding="UTF-8")
            dom = DOM.parseString(xml.encode('UTF-8'))
            self._int_file.write(dom.toprettyxml(
                indent="  ", encoding="UTF-8"))
        LOGGER.debug("  YAML Conversion finalized")

    def read(self):
        """Read data of converted file"""
        return self._int_file.getvalue()

    def close(self):
        """Close converted file"""
        self._int_file.close()

    # adapted from
    # http://code.activestate.com/recipes/577613-yaml-include-support/
    def __yaml_include(self, loader, node):
        """ Constructor for the include tag"""
        _yaml_node_data = node.value.split(":")
        with open(os.path.join(os.path.dirname(self._path),
                               _yaml_node_data[0])) as inputfile:
            _ = yaml.load(inputfile.read(), Loader=yaml.Loader)
            inputfile.close()
            if len(_yaml_node_data) > 1:
                _ = eval("_" + _yaml_node_data[1])
                if len(_yaml_node_data) > 2:
                    _ = eval(_yaml_node_data[2])
            return _
    #              leave out the [0] if your include file drops the key ^^^

    @staticmethod
    def create_headtags(data, parent_node):
        """ Search for the headtags in given dictionary """
        for tag in data.keys():
            if type(data[tag]) is not list:
                data[tag] = [data[tag]]
            if "benchmark" in data and \
                    tag in YAML_Converter.allowed_tags["/benchmark"]:
                for attr_and_tags in data[tag]:
                    YAML_Converter.create_tag(tag, attr_and_tags, parent_node)
            elif "benchmark" not in data and \
                    tag in YAML_Converter.allowed_tags["/"]:
                if tag not in YAML_Converter.allowed_tags["benchmark"]:
                    for attr_and_tags in data[tag]:
                        YAML_Converter.create_tag(
                            tag, attr_and_tags, parent_node)
                    del(data[tag])
        if "benchmark" not in data:
            YAML_Converter.create_tag("benchmark", data, parent_node)

    @staticmethod
    def create_tag(new_node_name, data, parent_node):
        """ Create the Subtag name, search for known tags
            and set the given attributes"""
        LOGGER.debug("    Create XML tag <{0}>".format(new_node_name))
        new_node = etree.SubElement(parent_node, new_node_name)
        # Check if tag can have subtags
        if new_node_name in YAML_Converter.allowed_tags:
            allowed_tags = YAML_Converter.allowed_tags[new_node_name]
            if type(data) is str and len(allowed_tags) == 1:
                data = {allowed_tags[0]: data}
            for key, value in data.items():
                if (type(value) is not list):
                    value = [value]
                for val in value:
                    if key in allowed_tags:
                        # Create new subtag
                        YAML_Converter.create_tag(key, val, new_node)
                    else:
                        # Create attribute
                        new_node.set(key, str(val))
        else:
            #
            if type(data) is not dict:
                # standard tag value
                new_node.text = str(data)
            else:
                for key, value in data.items():
                    if key == "_":
                        # _ represents the standard tag value
                        new_node.text = str(value)
                    else:
                        # Create attribute
                        new_node.set(key, str(value))

    @staticmethod
    def is_parseable_yaml_file(filename):
        try:
            with open(filename, "r") as file_handle:
                if type(yaml.load(file_handle.read())) is str:
                    return False
                else:
                    return True
        except Exception as parseerror:
            return False
