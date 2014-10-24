"""
    The JubeXMLConverter class provide support to convert jube XML files to the
    new XML format
"""


from __future__ import (print_function,
                        unicode_literals,
                        division,
                        )

import xml.etree.ElementTree as ET
import xml.dom.minidom as DOM
import sys
import os


class JubeXMLConverter(object):
    valid_tags = ["bench", "benchmark", "prepare", "compile",
                  "execution", "tasks", "params", "verify", "analyse"]
    valid_files = ["compile.xml", "execute.xml", "analyse.xml",
                   "prepare.xml", "result.xml", "verify.xml", "platform.xml"]
    specifier = {"platform_specifier": "", "compile_specifier": "",
                 "execute_specifier": "",
                 "prepare_specifier": "", "verify_specifier": "",
                 "analyse_specifier": "", "result_specifier": ""}

    def __init__(self, main_file, main_dir="./"):
        self._main_file = main_file
        self._main_dir = main_dir
        self._main_xml_file = self._main_dir + main_file

        self._compile_xml_file = self._main_dir + "compile.xml"
        self.file_availability(self._compile_xml_file)

        self._execute_xml_file = self._main_dir + "execute.xml"
        self.file_availability(self._execute_xml_file)

        self._analyse_xml_file = self._main_dir + "analyse.xml"
        self.file_availability(self._analyse_xml_file)

        self._prepare_xml_file = self._main_dir + "prepare.xml"
        self.file_availability(self._prepare_xml_file)

        self._result_xml_file = self._main_dir + "result.xml"
        self.file_availability(self._result_xml_file)

        self._verify_xml_file = self._main_dir + "verify.xml"
        self.file_availability(self._verify_xml_file)

        self._platform_xml_file = self._main_dir + "platform.xml"
        self.file_availability(self._platform_xml_file)

# Setup XML trees
        self._platform_xml_root = self.build_xml_tree(self._platform_xml_file)
        self._main_xml_file_root = self.build_xml_tree(self._main_xml_file)
        self._compile_xml_root = self.build_xml_tree(self._compile_xml_file)
        self._execute_xml_root = self.build_xml_tree(self._execute_xml_file)
        self._analyse_xml_root = self.build_xml_tree(self._analyse_xml_file)
        self._prepare_xml_root = self.build_xml_tree(self._prepare_xml_file)
        self._verify_xml_root = self.build_xml_tree(self._verify_xml_file)
        self._result_xml_root = self.build_xml_tree(self._result_xml_file)

    def file_availability(self, filename):
        if(os.path.isfile(filename)):
            return True
        elif(os.path.basename(filename) == "platform.xml"):
            self._platform_xml_file = self._main_dir + \
                "../../platform/platform.xml"
            if (os.path.isfile(self._platform_xml_file)):
                return True
            else:
                message = self._platform_xml_file + " doesn't exist"
                sys.exit(message)
        message = filename + " doesn't exist"
        sys.exit(message)
        return False

    def build_xml_tree(self, filename):
        tree = ET.parse(filename)

        # Check compatible terminal encoding: In some cases, the terminal env.
        # only allow ascii based encoding, print and filesystem operation will
        # be broken if there is a special char inside the input file.
        # In such cases the encode will stop, using an UnicodeEncodeError
        try:
            xml = ET.tostringlist(tree.getroot(), encoding="UTF-8")
            for line in xml:
                line.decode("UTF-8").encode(sys.getfilesystemencoding())
        except UnicodeEncodeError as uee:
            raise ValueError("Your terminal only allow '{0}' encoding. {1}"
                             .format(sys.getfilesystemencoding(), str(uee)))

        return tree.getroot()

    def gather_benchmarks(self):
        gathered_benchmarks = []
        for child in self._main_xml_file_root:
            gathered_benchmarks.append(child)
        return gathered_benchmarks

    def extract_input_elements(self, tag, xml_tree, store_content_here):
        for element in xml_tree.iter(tag):
            dictionary = element.attrib
            if(dictionary["cname"] == self.specifier[element]):
                for child in element.findall():
                    print (child.text)

    def get_platform(self):
        return self.specifier["platform_specifier"]

    def get_specifier(self):
        return self.specifier
# return self.specifier["platform_specifier"],
# self.specifier["prepare_specifier"], self.specifier["compile_specifier"]

    def _convert_and_add_parameter(self, name, parameters):
        parameterset = ET.Element('parameterset')
        parameterset.set('name', name)
        for k, v in parameters.attrib.items():
            parameter = ET.SubElement(parameterset, 'parameter', {'name': k})
            parameter.text = v

        self._root_platform_element.append(parameterset)

    def convert_platformfile(self):
        self._root_platform_element = ET.Element('jube')
        platform_tree = ET.parse(self._platform_xml_file)
        platform_root = platform_tree.getroot()

        for platform in platform_root.iter('platform'):
            parameterset_name = platform.get('name')
            parameter_dict = platform.find('params')
            self._convert_and_add_parameter(parameterset_name, parameter_dict)

    def write_platformfile(self, output="platform_converted.xml"):
        tree = ET.ElementTree(self._root_platform_element)
        xml = ET.tostring(tree.getroot(), encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml)
        fout = open(output, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))

    def _convert_and_add_substitute(self, name, subs):
        substituteset = ET.Element('substituteset')
        substituteset.set('name', name)

        for k, v in subs.attrib.items():
            sub = ET.SubElement(substituteset, 'sub', {'source': k, 'dest': v})
        self._root_platform_element.append(substituteset)

    def extract_substitutes_and_convert(self, xml_file, tag):
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        for item in xml_root.iter(tag):
            substituteset_name = item.get('cname') + "-" + tag
            substituteset = ET.Element('substituteset')
            substituteset.set('name', substituteset_name)
            for substitute in item.findall('substitute'):
                #                print (substituteset_name, " --- ", substitute)
                for subs in substitute.findall('sub'):
                    attribs_for_sub = {}
                    for k, v in subs.attrib.items():
                        if(k == "from"):
                            attribs_for_sub["source"] = v
                        else:
                            attribs_for_sub["dest"] = v
                    sub = ET.SubElement(substituteset, 'sub', attribs_for_sub)
            self._root_platform_element.append(substituteset)
#

    def convert_xml(self, xml_input_file=""):
        self.extract_substitutes_and_convert(self._execute_xml_file, "execute")
        self.extract_substitutes_and_convert(self._compile_xml_file, "compile")

if __name__ == "__main__":
    pass
