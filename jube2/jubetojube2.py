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
    _global_counter = 0
    _dummy_check_set = set()

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

# Variables to gather benchmark and step infos: benchmark_name -> benchmark
        self._benchmark_dict = {}

        self._global_platform_name = self._main_xml_file_root.attrib[
            "platform"]

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


# is used for platform file only, parameter from main file are not
# converted with this function
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

    def extract_substitutes_and_convert(self, xml_file, jube_step):
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()
        tag = jube_step._name
        for item in xml_root.iter(tag):
            self._global_counter = 0
            for substitute in item.findall('substitute'):

                prefix_name = item.get('cname')
                print (prefix_name, " --- ", jube_step._cname)

                substituteset_name = prefix_name + "_" + \
                    tag + "_" + str(self._global_counter)
                substituteset = ET.Element('substituteset')
                substituteset.set('name', substituteset_name)

                for subs in substitute.findall('sub'):
                    attribs_for_sub = {}
                    for k, v in subs.attrib.items():
                        if(k == "from"):
                            attribs_for_sub["source"] = v
                        else:
                            attribs_for_sub["dest"] = v
                    sub = ET.SubElement(substituteset, 'sub', attribs_for_sub)

    #           check if substituteset is relevant for current benchmark
                if (prefix_name == jube_step._cname):
                    jube_step._use_list.append(substituteset_name)
                else:
                    continue

                if(substituteset_name not in self._dummy_check_set):
                    print (
                        "@@---> ", substituteset_name, " --- ", self._dummy_check_set)
                    self._main_element.append(substituteset)
                    self._dummy_check_set.add(substituteset_name)
                self._global_counter += 1
#

    def convert_main_file(self):
        self._main_element = ET.Element('jube')
        main_tree = ET.parse(self._main_xml_file)
        main_root = main_tree.getroot()

        for benchmark in main_root.iter('benchmark'):
            benchmark_name = benchmark.get('name')

#           Gather attributes of all tags in main file
            parameter_dict = benchmark.find('params')
            tasks_dict = benchmark.find('tasks')
            execution_dict = benchmark.find('execution')
            compile_dict = benchmark.find('compile')

# check whether benchmark is already recognized
            if (benchmark_name not in self._benchmark_dict):
                pset = "pset_" + benchmark_name
#                 self._benchmark_list.append(pset)
                benchmark_obj = _JubeBenchmark(benchmark_name)
                self._benchmark_dict.update({benchmark_name: benchmark_obj})

                compile_step = _JubeStep("compile")
                compile_step._use_list.append(pset)
                compile_step._cname = self._check_and_sub_platform_var(
                    compile_dict.attrib["cname"])
                self.extract_substitutes_and_convert(
                    self._compile_xml_file, compile_step)
                benchmark_obj._compile_step = compile_step

                execution_step = _JubeStep("execution")
                execution_step._use_list.append(pset)
                execution_step._cname = self._check_and_sub_platform_var(
                    execution_dict.attrib["cname"])
                benchmark_obj._execution_step = execution_step

                self._benchmark_dict.update({benchmark_name: benchmark_obj})

            parameterset = ET.Element('parameterset')
            parameterset.set('name', "pset_" + benchmark_name)

#           scan params in main file
            for k, v in parameter_dict.items():
                parameter = ET.SubElement(
                    parameterset, 'parameter', {'name': k})
                parameter.text = v

#           scan tasks main file
            for k, v in tasks_dict.items():
                parameter = ET.SubElement(
                    parameterset, 'parameter', {'name': k})
                parameter.text = v

#           scan execution in main file
            for k, v in execution_dict.items():
                if k == 'cname':
                    continue
                parameter = ET.SubElement(
                    parameterset, 'parameter', {'name': k})
                parameter.text = v

            self._main_element.append(parameterset)

    def write_main_file(self, output="benchmarks_jube2.xml"):
        tree = ET.ElementTree(self._main_element)
        xml = ET.tostring(tree.getroot(), encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml)
        fout = open(output, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))

    def process_jube_main_file(self):
        self.convert_main_file()

    def convert_xml(self, jube_main_file):
        self.process_jube_main_file()
        self.convert_platformfile()
#         self.extract_substitutes_and_convert(self._execute_xml_file, "execute")
#         self.extract_substitutes_and_convert(self._compile_xml_file, "compile")
#         self.extract_substitutes_and_convert(self._prepare_xml_file, "prepare")
#         self.extract_substitutes_and_convert(self._verify_xml_file, "verify")

        self.write_platformfile(self._main_dir + "platform_jube2.xml")
        self.write_main_file(self._main_dir + "benchmarks_jube2.xml")

        self._print_struct()

    def _print_struct(self):
        for k, v in self._benchmark_dict.items():
            #             print(k)
            print("")
            v._print_benchmark()

    def _check_and_sub_platform_var(self, cname):
        if (cname == "$platform"):
            return self._global_platform_name
        else:
            return cname


class _JubeStep(object):

    def __init__(self, step_name):
        self._name = step_name
        self._cname = ""
        self._use_list = []

    def _print_step(self):
        print("\t\tStep:\t", self._name)
        print("\t\tcname:\t", self._cname)
        print("\t\t\t", self._use_list)
        print("-------------------------------------------")


class _JubeBenchmark(object):

    def __init__(self, benchmark_name):
        self._name = benchmark_name
        self._compile_step = None
        self._execution_step = None

    def _print_benchmark(self):
        print("Benchmark:\t", self._name)
        print("####################################")
        if self._compile_step is not None:
            self._compile_step._print_step()
        if self._execution_step is not None:
            self._execution_step._print_step()

if __name__ == "__main__":
    pass
