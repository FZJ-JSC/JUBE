from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as etree
import xml.dom.minidom as DOM
import yaml
import jube2.util.output
import os
import StringIO


def is_parseable_yaml_file(filename):
    try:
        with open(filename, "r") as file_handle:
            if type(yaml.load(file_handle.read())) is str:
                return False
            else:
                return True
    except Exception as parseerror:
        return False


class Conv(object):
    def __init__(self, path):
        self._path = path
        yaml.add_constructor("!include", self.__yaml_include)
        self._int_file = StringIO.StringIO()
        self.__convert()

    def __convert(self):
        """ Opens given file, make a Tree of it and print it """
        with open(self._path, "r") as file_handle:
            xmltree = XMLTree(yaml.load(file_handle.read()))
            xml = jube2.util.output.element_tree_tostring(
                xmltree.tree, encoding="UTF-8")
            dom = DOM.parseString(xml.encode('UTF-8'))
            self._int_file.write(dom.toprettyxml(
                indent="  ", encoding="UTF-8"))

    def read(self):
        return self._int_file.getvalue()

    def close(self):
        self._int_file.close()

    # adapted from
    # http://code.activestate.com/recipes/577613-yaml-include-support/
    def __yaml_include(self, loader, node):
        """ Constructor for the include tag"""
        _yaml_node_data = node.value.split(":")
        with open(os.path.join(os.path.dirname(self._path), _yaml_node_data[0])) as inputfile:
            _ = yaml.load(inputfile.read(), Loader=yaml.Loader)
            inputfile.close()
            if len(_yaml_node_data) > 1:
                _ = eval("_" + _yaml_node_data[1])
                if len(_yaml_node_data) > 2:
                    _ = eval(_yaml_node_data[2])
            return _
    #              leave out the [0] if your include file drops the key ^^^


class XMLTree():
    allowed = {"/": ["benchmark", "parameterset", "comment", "step", "fileset",
                     "substituteset", "analyser", "result", "patternset",
                     "selection", "include-path"],
               "/benchmark": ["benchmark", "parameterset", "fileset",
                              "substituteset", "patternset", "selection", "include-path"],
               "benchmark": ["parameterset", "comment", "step", "fileset",
                             "substituteset", "analyser", "result", "patternset"],
               "analyse": ["file"], "analyser": ["use", "analyse"],
               "fileset": ["link", "copy", "prepare"],
               "include-path": ["path"], "parameterset": ["parameter"],
               "patternset": ["pattern"], "result": ["use", "table", "syslog"],
               "selection": ["not", "only"], "step": ["use", "do"],
               "substituteset": ["iofile", "sub"], "syslog": ["key"],
               "table": ["column"]}

    def __init__(self, dict):
        """ Create the Treeelement Jube """
        self.dict = dict
        self.tree = etree.Element('jube')
        self.create_headtags(self.dict, self.tree)

    def create_headtags(self, dict, current_sub):
        """ Search for the headtags in given dictionary """
        for key in dict.keys():
            if "benchmark" in dict and key in XMLTree.allowed["/benchmark"]:
                for attr_and_tags in dict[key]:
                    self.create_tag(key, attr_and_tags, current_sub)
            elif "benchmark" not in dict and key in XMLTree.allowed["/"]:
                if key not in XMLTree.allowed["benchmark"]:
                    for attr_and_tags in dict[key]:
                        self.create_tag(key, attr_and_tags, current_sub)
                    del(dict[key])
        if "benchmark" not in dict:
            self.create_tag("benchmark", dict, current_sub)

    def create_tag(self, name, attr_and_tags, current_sub):
        """ Create the Subtag name, search for known tags
            and set the given attributes"""
        local_sub = etree.SubElement(current_sub, name)
        if name in self.allowed:
            allowed_tags = self.allowed[name]
            if type(attr_and_tags) is str and len(allowed_tags) == 1:
                attr_and_tags = {allowed_tags[0]: attr_and_tags}
            for key, value in attr_and_tags.items():
                if (type(value) is not list):
                    value = [value]
                for val in value:
                    if key in allowed_tags:
                        self.create_tag(key, val, local_sub)
                    else:
                        local_sub.set(key, str(val))
        else:
            if type(attr_and_tags) is not dict:
                local_sub.text = str(attr_and_tags)
            else:
                for key, value in attr_and_tags.items():
                    if key == "_":
                        local_sub.text = str(value)
                    else:
                        local_sub.set(key, str(value))
