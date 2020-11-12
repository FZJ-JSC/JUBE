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
import jube2.conf
import jube2.util.output
import os
import copy
import jube2.util.util
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
         "selection": ["not", "only", "tag"], "step": ["use", "do"],
         "substituteset": ["iofile", "sub"], "syslog": ["key"],
         "table": ["column"]}

    def __init__(self, path, include_path=None, tags=None):
        self._path = path
        if include_path is None:
            include_path = []
        if tags is None:
            tags = set()
        self._include_path = list(include_path)
        self._include_path += [os.path.dirname(self._path)]
        self._tags = set(tags)
        try:
            yaml.add_constructor("!include", self.__yaml_include)
        except NameError:
            raise NameError("yaml module not available; either install it " +
                            "(https://pyyaml.org), or switch to .xml input " +
                            "files.")
        self._ignore_search_errors = True
        self._tags.update(self.__search_for_tags())
        old_tags = set(self._tags)
        changed = True
        counter = 0
        # It is possible to add new tags by including external files into a
        # selection block therefore the input must be scanned multiple times
        # to gather all available tags
        while changed and counter < jube2.conf.PREPROCESS_MAX_ITERATION:
            self._include_path = list(include_path) + \
                self.__search_for_include_pathes() + \
                [os.path.dirname(self._path)]
            self._tags.update(self.__search_for_tags())
            changed = len(self._tags.difference(old_tags)) > 0
            old_tags = set(self._tags)
            counter += 1
        self._ignore_search_errors = False
        self._int_file = IOStream()
        self.__convert()

    def __convert(self):
        """ Opens given file, make a Tree of it and print it """
        LOGGER.debug("  Start YAML to XML file conversion for file {0}".format(
            self._path))
        with open(self._path, "r") as file_handle:
            xmltree = etree.Element('jube')
            YAML_Converter.create_headtags(
                yaml.load(file_handle.read(), Loader=yaml.Loader), xmltree)
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

    def __find_include_file(self, filename):
        """Search for filename in include-pathes and return resulting path"""
        for path in self._include_path:
            file_path = os.path.join(path, filename)
            if os.path.exists(file_path):
                break
        else:
            raise ValueError(("\"{0}\" not found in possible " +
                              "include pathes").format(filename))
        return file_path

    def __search_for_tags(self):
        """Search a YAML file for stored tag information"""
        tags = set()
        with open(self._path, "r") as file_handle:
            data = yaml.load(file_handle.read(), Loader=yaml.Loader)
            if "selection" in data and "tag" in data["selection"]:
                if type(data["selection"]["tag"]) is not list:
                    data["selection"]["tag"] = [data["selection"]["tag"]]
                for tag in data["selection"]["tag"]:
                    if not tag.startswith("!include "):
                        tags.update(
                            set(tag.split(jube2.conf.DEFAULT_SEPARATOR)))
        return tags

    def __search_for_include_pathes(self):
        """Search a YAML file for stored include-path information"""
        include_pathes = []
        with open(self._path, "r") as file_handle:
            data = yaml.load(file_handle.read(), Loader=yaml.Loader)
            # include-path is only allowed on the top level of the tree
            if "include-path" in data:
                if type(data["include-path"]) is not list:
                    data["include-path"] = [data["include-path"]]
                for path in data["include-path"]:
                    # path in include-path is optional
                    # verify tags
                    if type(path) is dict:
                        if "tag" in path and not \
                                jube2.util.util.valid_tags(path["tag"],
                                                           self._tags):
                            continue
                        value = path["path"] if "path" in path else path["_"]
                        if type(value) is not list:
                            value = [value]
                        for val in value:
                            if type(val) is dict:
                                if "tag" in val and not \
                                    jube2.util.util.valid_tags(val["tag"],
                                                               self._tags):
                                    continue
                                val = val["_"]
                            include_pathes.append(os.path.join(
                                os.path.dirname(self._path), val))
                    else:
                        include_pathes.append(os.path.join(
                            os.path.dirname(self._path), path))
        return include_pathes

    # adapted from
    # http://code.activestate.com/recipes/577613-yaml-include-support/
    def __yaml_include(self, loader, node):
        """ Constructor for the include tag"""
        yaml_node_data = node.value.split(":")
        try:
            file = self.__find_include_file(yaml_node_data[0])
            if os.path.normpath(file) == os.path.normpath(self._path):
                # Avoid recursive !include loops
                loader = yaml.BaseLoader
            else:
                loader = yaml.Loader
            with open(file) as inputfile:
                _ = yaml.load(inputfile.read(), Loader=loader)
                inputfile.close()
                if len(yaml_node_data) > 1:
                    _ = eval("_" + yaml_node_data[1])
                    if len(yaml_node_data) > 2:
                        _ = eval(yaml_node_data[2])
                return _
        except ValueError as ve:
            if self._ignore_search_errors:
                return "!include {0}".format(node.value)
            else:
                raise ve

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
        if new_node_name in YAML_Converter.allowed_tags and type(data) is dict:
            allowed_tags = YAML_Converter.allowed_tags[new_node_name]
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
            tag_value = ""
            if type(data) is not dict:
                # standard tag value
                tag_value = data
            else:
                for key, value in data.items():
                    if key == "_":
                        # _ represents the standard tag value
                        tag_value = value
                    else:
                        # Create attribute
                        new_node.set(key, str(value))
            if type(tag_value) is list:
                new_node.text = str(tag_value.pop(0))
                while len(tag_value) > 0:
                    new_node = copy.deepcopy(new_node)
                    parent_node.append(new_node)
                    new_node.text = str(tag_value.pop(0))
            else:
                new_node.text = str(tag_value)

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
