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
"""
    The JubeXMLConverter class provide support to convert jube XML files to the
    new XML format
"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as ET
import xml.dom.minidom as DOM
import sys
import os
import re
import tarfile
import glob
import jube2.util

GLOBAL_PARAMETERSET_NAME = "jube_convert_parameter"


class JubeXMLConverter(object):

    """Convert jube version 1 files in jube version 2 readable format"""
    _global_counter = 0
    _dummy_check_set = set()
    _global_calc_counter = 0

    def __init__(self, main_file, main_dir="./"):
        self._main_file = main_file
        self._main_dir = main_dir + "/"
        self._main_xml_file = os.path.join(self._main_dir, main_file)

        self._compile_xml_file = os.path.join(self._main_dir, "compile.xml")
        self.file_availability(self._compile_xml_file)

        self._execute_xml_file = os.path.join(self._main_dir, "execute.xml")
        self.file_availability(self._execute_xml_file)

        self._analyse_xml_file = os.path.join(self._main_dir, "analyse.xml")
        self.file_availability(self._analyse_xml_file)

        self._prepare_xml_file = os.path.join(self._main_dir, "prepare.xml")
        self.file_availability(self._prepare_xml_file)

        self._result_xml_file = os.path.join(self._main_dir, "result.xml")
        self.file_availability(self._result_xml_file)

        self._verify_xml_file = os.path.join(self._main_dir, "verify.xml")
        self.file_availability(self._verify_xml_file)

        self._platform_xml_file = os.path.join(self._main_dir, "platform.xml")
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

#       The global parameterset is needed in each benchmark and therefore needs
#       to be included
        self._global_parameterset = self._init_global_parameterset()

#         Needed to gather perl expressions of corresponding substituteset
        self._calc_parameterset_node = None
        self._calc_parameterset_name = ""
        self._root_platform_element = None
        self._main_element = None

    @staticmethod
    def _init_global_parameterset():
        """"Set jube version 1 specific variables to reasonable values"""
        global_parameterset = ET.Element('parameterset')
        global_parameterset.set('name', GLOBAL_PARAMETERSET_NAME)
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'outdir'})
        parameter.text = "."
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'executable'})
        parameter.text = "./jube_exe"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'execname'})
        parameter.text = "jube_exe"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'benchname'})
        parameter.text = "$jube_benchmark_name"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'subid'})
        parameter.text = "$jube_benchmark_id"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'env'})
        parameter.text = "$jube_wp_envstr"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'stderrlogfile'})
        parameter.text = "stderr"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'stdoutlogfile'})
        parameter.text = "stdout"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'benchhome'})
        parameter.text = "$jube_benchmark_home"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'pdir'})
        parameter.text = "../../../platform/"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'subdir'})
        parameter.text = "."
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'stdoutfile'})
        parameter.text = "stdout"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'stderrfile'})
        parameter.text = "stderr"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'execnamepath'})
        parameter.text = "$jube_wp_abspath"
        parameter = ET.SubElement(
            global_parameterset, 'parameter', {'name': 'rundir'})
        parameter.text = "$jube_wp_abspath"

        return global_parameterset

    def file_availability(self, filename):
        """Check whether all needed jube version 1 XML files are available"""
        if os.path.isfile(filename):
            return True
        elif os.path.basename(filename) == "platform.xml":
            self._platform_xml_file = self._main_dir + \
                "../../platform/platform.xml"
            if os.path.isfile(self._platform_xml_file):
                return True
            else:
                message = self._platform_xml_file + " doesn't exist"
                sys.exit(message)
        message = filename + " doesn't exist"
        sys.exit(message)
        return False

    @staticmethod
    def build_xml_tree(filename):
        """Build XML tree from corresponding jube version 1 XML file"""
        tree = ET.parse(filename)

        # Check compatible terminal encoding: In some cases, the terminal env.
        # only allow ascii based encoding, print and filesystem operation will
        # be broken if there is a special char inside the input file.
        # In such cases the encode will stop, using an UnicodeEncodeError
        try:
            xml = jube2.util.element_tree_tostring(tree.getroot(),
                                                   encoding="UTF-8")
            xml.encode(sys.getfilesystemencoding())
        except UnicodeEncodeError as uee:
            raise ValueError("Your terminal only allow '{0}' encoding. {1}"
                             .format(sys.getfilesystemencoding(), str(uee)))

        return tree.getroot()


# is used for platform file only, parameter from main file are not
# converted with this function
    def _convert_and_add_parameter(self, name, parameters):
        """Convert jube version 1 parameter and add it to parameterset"""
        parameterset = ET.Element('parameterset')
        parameterset.set('name', name)

        for key, val in parameters.attrib.items():
            parameter = ET.SubElement(parameterset, 'parameter', {'name': key})
            parameter.text = val

#       Add platform as needed in jube version 1
        if name == self._global_platform_name:
            parameter = ET.SubElement(
                parameterset, 'parameter', {'name': 'platform'})
            parameter.text = self._global_platform_name

        self._root_platform_element.append(parameterset)

    def convert_platformfile(self):
        """Convert jube version 1 platform.xml into parametersets"""
        self._root_platform_element = ET.Element('jube')
        platform_tree = ET.parse(self._platform_xml_file)
        platform_root = platform_tree.getroot()

        for platform in jube2.util.get_tree_elements(platform_root,
                                                     'platform'):
            parameterset_name = platform.get('name')
            parameter_dict = platform.find('params')
            self._convert_and_add_parameter(parameterset_name, parameter_dict)

    def write_platformfile(self, output="platform_converted.xml"):
        """Write out converted platform.xml"""
        tree = ET.ElementTree(self._root_platform_element)
        xml = jube2.util.element_tree_tostring(tree.getroot(),
                                               encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml.encode("UTF-8"))
        fout = open(output, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))

    def _create_calc_parameter(self, expression, step):
        """Convert perl expressions from sub tags into parameter"""
        matches = re.findall("`(.*?)`+", expression)

        for match in matches:
            if self._calc_parameterset_node is None:
                self._calc_parameterset_node = ET.Element('parameterset')
                set_name = step.name + "_calc_" + \
                    str(self._global_counter)
                self._calc_parameterset_node.set('name', set_name)
                self._calc_parameterset_name = set_name
                step.use_list.add(set_name)

            parameter_name = "jube_calc_" + str(self._global_calc_counter)

            parameter = ET.SubElement(
                self._calc_parameterset_node, 'parameter',
                {'name': parameter_name, 'mode': 'perl'})

            parameter.text = match
            pattern = "`" + match + "`"
            repl = "$" + parameter_name

            expression = expression.replace(pattern, repl)
            self._global_calc_counter += 1
        return expression

    @staticmethod
    def _has_perl_expression(expression):
        """Check whether jube version 1 tag includes perl expressions"""
        if re.findall("`(.*?)`+", expression):
            return True
        else:
            return False

    def _create_compile_fileset_node(self, xml_file, jube_step, benchmark):
        """Create a fileset node for compile step"""
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step.name
        if tag != "compile":
            return

        for item in jube2.util.get_tree_elements(xml_root, tag):
            prefix_name = item.get('cname')
            if prefix_name != jube_step.cname:
                continue
            src_node = item.find('src')
            fileset_node = ET.Element('fileset')
            fileset_name = jube_step.name + \
                '_files_' + str(self._global_counter)
            fileset_node.set('name', fileset_name)

            copy_node = ET.SubElement(
                fileset_node, 'copy',
                {'directory': src_node.attrib["directory"], 'separator': ' '})

            copy_node.text = src_node.attrib["files"]

#            create file list
            file_list = self._create_compile_file_list(
                src_node.attrib["files"], src_node.attrib["directory"])
            tar_command = self._create_tar_command_for_compile(file_list)

            prepare_node = ET.SubElement(fileset_node, 'prepare')
            prepare_node.text = tar_command

            jube_step.use_list.add(fileset_name)
            benchmark.fileset_node.add(fileset_node)

    @staticmethod
    def _create_compile_file_list(files, directory):
        """"Create file list of all files to be copied in compile step"""
        pwd = os.path.realpath(".")
        os.chdir(directory)
        list_for_glob = []
        full_list = []
        for filename in files:
            list_for_glob.append(os.path.join(directory, filename))

        for filename in list_for_glob:
            full_list.extend(glob.glob(filename))

        os.chdir(pwd)
        return full_list

    @staticmethod
    def _create_tar_command_for_compile(file_list):
        """Create shell command for tar if tar files exist for compile step"""
        command = "for i in"
        tarfile_list = []
        for filename in file_list:
            if os.path.isfile(filename):
                if tarfile.is_tarfile(filename):
                    tarfile_list.append(filename)

        if not tarfile_list:
            return ""
        for filename in tarfile_list:
            command = command + " " + filename
        command = command + "; do tar xf $i; done"
        return command

    def create_fileset_node(self, xml_file, jube_step, benchmark):
        """Create fileset for all steps but compile"""
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step.name
#       check necessary execution (main file) but execute in execute.xml
        if jube_step.name == "execution":
            tag = "execute"

        for item in jube2.util.get_tree_elements(xml_root, tag):
            prefix_name = item.get('cname')
            if prefix_name != jube_step.cname:
                continue
            input_node = item.find('input')
            fileset_node = ET.Element('fileset')
            fileset_name = jube_step.name + \
                '_files_' + str(self._global_counter)
            fileset_node.set('name', fileset_name)
            copy_node = ET.SubElement(fileset_node, 'copy', {"separator": " "})
            if input_node is not None:
                copy_node.text = input_node.attrib['files']
            if tag == "execute":
                copy_node = ET.SubElement(
                    fileset_node, 'copy', {'rel_path_ref': 'internal'})
                copy_node.text = "prepare/*"
                link_node = ET.SubElement(
                    fileset_node, 'link', {'rel_path_ref': 'internal'})
                link_node.text = "compile/$execname"

                link_node = ET.SubElement(
                    fileset_node, 'link')
                link_node.text = "$jube_benchmark_home/run"

            jube_step.use_list.add(fileset_name)

            benchmark.fileset_node.add(fileset_node)

    def extract_substitutes_and_convert(self, xml_file, jube_step):
        """Convert jube version 1 subs into jube version 2 substituteset"""
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step.name
#       check necessary execution (main file) but execute in execute.xml
        if jube_step.name == "execution":
            tag = "execute"

#            Substitution of perl expressions are also done in this loop.
#            calc_parameterset needs to be emptied for each step to fill
# in only those expressions which are relevant for the underlying step
#         self._calc_parameterset_name = ""
        self._calc_parameterset_node = None
        for item in jube2.util.get_tree_elements(xml_root, tag):
            self._global_counter = 0
            for substitute in item.findall('substitute'):

                prefix_name = item.get('cname')
#               check if substituteset is relevant for current benchmark
                if prefix_name != jube_step.cname:
                    continue

                substituteset_name = prefix_name + "_" + \
                    tag + "_" + str(self._global_counter)
                substituteset = ET.Element('substituteset')
                substituteset.set('name', substituteset_name)

#               Build iofile tag
                iofile_dict = {
                    "in": substitute.attrib['infile'],
                    "out": substitute.attrib['outfile']}
                ET.SubElement(substituteset, 'iofile', iofile_dict)

                for subs in substitute.findall('sub'):
                    attribs_for_sub = {}
                    for key, val in subs.attrib.items():
                        if key == "from":
                            attribs_for_sub["source"] = val
                        else:
                            if self._has_perl_expression(val):
                                attribs_for_sub["dest"] = \
                                    self._create_calc_parameter(val, jube_step)
                            else:
                                attribs_for_sub["dest"] = val
#
                    ET.SubElement(substituteset, 'sub', attribs_for_sub)

                    jube_step.use_list.add(substituteset_name)

                if substituteset_name not in self._dummy_check_set:
                    self._main_element.append(substituteset)
                    self._dummy_check_set.add(substituteset_name)

                    if ((self._calc_parameterset_node is not None) and
                        (self._calc_parameterset_name not in
                            self._dummy_check_set)):
                        self._dummy_check_set.add(self._calc_parameterset_name)
                        self._main_element.append(self._calc_parameterset_node)

                self._global_counter += 1

    def _main_comment(self):
        """Create user hint in resulting file"""
        text = """ Hint for the user!
        jube version 1 provides plenty of help variables which are not
        necessarily available in jube version 2. So it might be necessary to
        define suitable parameters.

        Have a look at the "do" tags of this file and check whether the used
        variables are actually defined. In some cases predefined jube
        variables might help. Type "jube help jube_variables" to get a list of
        them.

        In the case you used "lastcommand" in jube version 1 you need to
        give a value for $shared_dir given in the corresponding execution
        step (just grep for "$shared_dir").
        Please note that the commands in the "do" tags come straight from jube
        1 files. If you copy files to other places etc. jube 2 can't recognize
        it and you need to adapt the commands."""

        comment = ET.Comment(text)
        self._main_element.append(comment)

    def convert_main_file(self):
        """Convert parameters from main jube 1 file and gather step infos"""
        self._main_element = ET.Element('jube')
        main_tree = ET.parse(self._main_xml_file)
        main_root = main_tree.getroot()
        self._main_comment()
        self._main_element.append(self._global_parameterset)

        for benchmark in jube2.util.get_tree_elements(main_root, 'benchmark'):
            benchmark_name = benchmark.get('name')

#           Gather attributes of all tags in main file
            parameter_dict = benchmark.find('params')
            tasks_dict = benchmark.find('tasks')
            execution_dict = benchmark.find('execution')
            compile_dict = benchmark.find('compile')
            prepare_dict = benchmark.find('prepare')
            verify_dict = benchmark.find('verify')
            analyse_dict = benchmark.find('analyse')
# check whether benchmark is already recognized
            if benchmark_name not in self._benchmark_dict:
                pset = "pset_" + benchmark_name
#                 self._benchmark_list.append(pset)
                benchmark_obj = _JubeBenchmark(benchmark_name)
                self._benchmark_dict.update({benchmark_name: benchmark_obj})

#               benchmark setup
                self._benchmark_init(
                    benchmark_obj, pset, compile_dict, execution_dict,
                    prepare_dict, verify_dict, analyse_dict)

                self._benchmark_dict.update({benchmark_name: benchmark_obj})

            parameterset = ET.Element('parameterset')
            parameterset.set('name', "pset_" + benchmark_name)

            init_with_data = "platform_jube2.xml:" + self._global_platform_name
            parameterset.set('init_with', init_with_data)
#           scan params in main file
            for key, val in parameter_dict.items():
                parameter = ET.SubElement(
                    parameterset, 'parameter', {'name': key})
                parameter.text = val

#           scan tasks main file
            for key, val in tasks_dict.items():
                parameter = ET.SubElement(
                    parameterset, 'parameter', {'name': key})
                parameter.text = val

#           scan execution in main file
            for key, val in execution_dict.items():
                if key == 'cname':
                    continue
                parameter = ET.SubElement(
                    parameterset, 'parameter', {'name': key})
                parameter.text = val

            self._main_element.append(parameterset)

    def _benchmark_init(self, benchmark_obj, pset, compile_dict,
                        execution_dict, prepare_dict,
                        verify_dict, analyse_dict):
        """Create benchmark"""
        #       Compile
        compile_step = _JubeStep("compile")
        compile_step.use_list.add("jube_convert_parameter")
        compile_step.use_list.add(pset)
        compile_step.cname = self._check_and_sub_platform_var(
            compile_dict.attrib["cname"])
        self.extract_substitutes_and_convert(
            self._compile_xml_file, compile_step)
        self._extract_commands(self._compile_xml_file, compile_step)
        self._create_compile_fileset_node(
            self._compile_xml_file, compile_step, benchmark_obj)
        benchmark_obj.compile_step = compile_step
        compile_step.build_step_element()

#       Execute
        execution_step = _JubeStep("execution")
        execution_step.use_list.add("jube_convert_parameter")
        execution_step.use_list.add(pset)
        execution_step.cname = self._check_and_sub_platform_var(
            execution_dict.attrib["cname"])
        self.extract_substitutes_and_convert(
            self._execute_xml_file, execution_step)
        self._extract_commands(self._execute_xml_file, execution_step)
        self._extract_environment(self._execute_xml_file, execution_step)
        self.create_fileset_node(
            self._execute_xml_file, execution_step, benchmark_obj)
        benchmark_obj.execution_step = execution_step

#       Prepare
        prepare_step = _JubeStep("prepare")
        prepare_step.use_list.add("jube_convert_parameter")
        prepare_step.use_list.add(pset)
        prepare_step.cname = self._check_and_sub_platform_var(
            prepare_dict.attrib["cname"])
        self.extract_substitutes_and_convert(
            self._prepare_xml_file, prepare_step)
        self._extract_commands(self._prepare_xml_file, prepare_step)
        self.create_fileset_node(
            self._prepare_xml_file, prepare_step, benchmark_obj)
        benchmark_obj.prepare_step = prepare_step
        prepare_step.build_step_element()

#       Verify
        verify_step = _JubeStep("verify")
        verify_step.use_list.add(pset)
        verify_step.cname = self._check_and_sub_platform_var(
            verify_dict.attrib["cname"])
        self.extract_substitutes_and_convert(
            self._verify_xml_file, verify_step)
        self._extract_commands(self._verify_xml_file, verify_step)

#      verify command(s) are added to execute commands. In fact these two steps
#      are merged and verify wont't exists as a separate step.
        for verify_do in verify_step.do_list:
            execution_step.verify_do_list.append(verify_do)

        for verify_use in verify_step.use_list:
            execution_step.use_list.add(verify_use)
        execution_step.build_step_element()

        benchmark_obj.verify_step = verify_step
        verify_step.build_step_element()

#       Analyse
        analyse_cname = self._check_and_sub_platform_var(
            analyse_dict.attrib["cname"])
        analyser = _JubeAnalyser(
            "analyse", analyse_cname, self._main_dir, self._analyse_xml_file)
#         analyser._extract_includepattern(self._analyse_xml_file)
        benchmark_obj.analyser = analyser

#        Finally, build benchmark node
        benchmark_obj.build_benchmark_element()

    def _extract_commands(self, xml_file, jube_step):
        """Extract commands from jube 1 files"""
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step.name
#       check necessary execution (main file) but execute in execute.xml
        if jube_step.name == "execution":
            tag = "execute"

        for item in jube2.util.get_tree_elements(xml_root, tag):
            for command in item.findall('command'):
                prefix_name = item.get('cname')
                if prefix_name == jube_step.cname:
                    jube_step.do_list.append(
                        self.beautify_command(command.text))
                else:
                    continue

        for item in jube2.util.get_tree_elements(xml_root, tag):
            for lastcommand in item.findall('lastcommand'):
                prefix_name = item.get('cname')
                if prefix_name == jube_step.cname:
                    jube_step.last_command = self.beautify_command(
                        lastcommand.text)
                else:
                    continue

    @staticmethod
    def beautify_command(command_text):
        """Format extracted commands"""
        #         newline = "\n"
        tab = "\t"
#         command_text = re.sub(newline, "", command_text)
        command_text = re.sub(tab, " ", command_text)
        command_text = command_text.strip()
        return command_text

    def _extract_environment(self, xml_file, jube_step):
        """Extract environment tag from jube 1 execute.xml"""
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step.name
#       check necessary execution (main file) but execute in execute.xml
        if jube_step.name == "execution":
            tag = "execute"

        for item in jube2.util.get_tree_elements(xml_root, tag):
            self._global_counter = 0
            for environment in item.findall('environment'):

                prefix_name = item.get('cname')
                envset_name = "envset_" + prefix_name + "_" + \
                    tag + "_" + str(self._global_counter)
                envset = ET.Element('parameterset')
                envset.set('name', envset_name)

                for env in environment.findall('env'):
                    parameter = ET.SubElement(
                        envset, 'parameter', {'name': env.attrib["var"],
                                              'export': 'True'})
                    parameter.text = env.attrib["value"]

#             check if substituteset is relevant for current benchmark
                if prefix_name == jube_step.cname:
                    jube_step.use_list.add(envset_name)
                else:
                    continue

                if envset_name not in self._dummy_check_set:
                    self._main_element.append(envset)
                    self._dummy_check_set.add(envset_name)
                self._global_counter += 1

    def write_main_file(self, output="benchmarks_jube2.xml"):
        """Write file resulting from convertion"""
        tree = ET.ElementTree(self._main_element)
        xml = jube2.util.element_tree_tostring(tree.getroot(),
                                               encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml.encode("UTF-8"))
        fout = open(output, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))

    def process_jube_main_file(self):
        """Call function for main file conversion"""
        self.convert_main_file()

    def convert_xml(self):
        """Trigger convertion and put everything together"""
        self.process_jube_main_file()
        self.convert_platformfile()

        for val in self._benchmark_dict.values():
            self._main_element.append(val.benchmark_element)

        self.write_platformfile(self._main_dir + "platform_jube2.xml")
        self.write_main_file(self._main_dir + "benchmarks_jube2.xml")

        message = """            Don't forget to have a look at
            benchmarks_jube2.xml and platform_jube2.xml
            and check whether you get what you  expect.
            In particular, notice the comments in
            benchmarks_jube2.xml."""
        print(message)

    def _check_and_sub_platform_var(self, cname):
        """Define parameter for jube 1 $platform in converted platform file"""
        if cname == "$platform":
            return self._global_platform_name
        else:
            return cname


class _JubeAnalyser(object):

    """Handle analyse issues"""

    def __init__(self, name, cname, main_dir, xml_file):
        self._name = name
        self._cname = cname
        self._analyse_xml_file = xml_file
        self._main_dir = main_dir
        self._pattern_file_list = []
        self._use_list = set()
        self._result_node = None
        self._extract_includepattern(xml_file)


#       Needed for result table
        self._pattern_name_set = set()

        self._patternset_node_list = []
        self._create_patternset_node_list()

        self._analyser_node = None
        self._create_analyser_node()

        self._create_result_node()

    @property
    def patternset_node_list(self):
        """Get patternset node list"""
        return self._patternset_node_list

    @property
    def analyser_node(self):
        """Get analyser node"""
        return self._analyser_node

    @property
    def result_node(self):
        """Get result node"""
        return self._result_node

    def _create_analyser_node(self):
        """Create analyser node for benchmark"""
        self._analyser_node = ET.Element("analyser")
        self._analyser_node.set('name', 'analyze')
        for use in self._use_list:
            use_tag = ET.SubElement(self._analyser_node, "use")
            use_tag.text = use

        analyse_tag = ET.SubElement(
            self._analyser_node, "analyse", {"step": "execution"})
        file_tag = ET.SubElement(analyse_tag, "file")
        file_tag.text = "stdout"

    def exclude_pattern_from_analysexml(self, patternset):
        """Gather and convert regex from jube 1"""
        xml_tree = ET.parse(self._analyse_xml_file)
        xml_root = xml_tree.getroot()

        tag = "analyzer"

        for item in jube2.util.get_tree_elements(xml_root, tag):
            for analyse in item.findall('analyse'):
                prefix_name = analyse.get('cname')
                if prefix_name == self._cname:
                    for parm in analyse.findall('parm'):
                        parm_dict = parm.attrib

# prefix added to pattern names to avoid possible naming conflict with
# parameters
                        parm_dict['name'] = "pat_" + parm_dict['name']
#     Adaption to jube2 attributes
                        if re.search('line', parm_dict['mode']):
                            parm_dict['mode'] = 'pattern'

                        if parm_dict['mode'] == 'derived':
                            parm_dict['mode'] = 'perl'
                            parm.text = self.adapt_derived_pattern(parm.text)

                        self._pattern_name_set.add(parm_dict['name'])
                        subelement = ET.SubElement(
                            patternset, 'pattern', parm_dict)
                        subelement.text = self._substitute_jube_pattern(
                            parm.text)

                    self._patternset_node_list.append(patternset)

    def _create_patternset_node_list(self):
        """Create patternset from jube 1 regex"""

        for patternfile in self._pattern_file_list:

            root = self._create_root(patternfile)

            patternset = ET.Element('patternset')
            usename = os.path.basename(patternfile)
            patternset.set('name', usename)
            self._use_list.add(usename)
            if patternfile == "analyse.xml":
                self.exclude_pattern_from_analysexml(patternset)
                continue

            for parm in root.findall('parm'):
                parm_dict = parm.attrib

# prefix added to pattern names to avoid possible naming conflict with
# parameters
                parm_dict['name'] = "pat_" + parm_dict['name']
#     Adaption to jube2 attributes
                if re.search('line', parm_dict['mode']):
                    parm_dict['mode'] = 'pattern'

                if parm_dict['mode'] == 'derived':
                    parm_dict['mode'] = 'perl'
                    parm.text = self.adapt_derived_pattern(parm.text)

                self._pattern_name_set.add(parm_dict['name'])
                subelement = ET.SubElement(patternset, 'pattern', parm_dict)
                subelement.text = self._substitute_jube_pattern(parm.text)

            self._patternset_node_list.append(patternset)

    def adapt_derived_pattern(self, regex):
        """Check derived pattern and adapt accordingly"""
        for name in self._pattern_name_set:
            pat = r"\$" + name.split("pat_")[1]
            repl = "$" + name
            regex = re.sub(pat, repl, regex)

        return regex

    def _create_result_node(self):
        """Create result node for benchmark"""
        self._result_node = ET.Element('result')
        text = """All pattern names appear in the table. This might be more
        than you need. Remove accordingly"""
        comment = ET.Comment(text)
        self._result_node.append(comment)


#         Use part
        use_tag = ET.SubElement(self._result_node, "use")
        use_tag.text = 'analyze'

#       Table part
        table_tag = ET.SubElement(
            self._result_node, 'table', {'name': 'result', 'style': 'pretty'})
        for name in self._pattern_name_set:
            column_tag = ET.SubElement(table_tag, 'column')
            column_tag.text = name

    @staticmethod
    def _substitute_jube_pattern(regexp):
        """Convert standard jube 1 patterns into standard jube 2 patterns"""
        jube1pat1 = r"\$patint"
        jube2pat1 = "$jube_pat_int"

        jube1pat2 = r"\$patfp"
        jube2pat2 = "$jube_pat_fp"

        jube1pat3 = r"\$patwrd"
        jube2pat3 = "$jube_pat_wrd"

        jube1pat4 = r"\$patnint"
        jube2pat4 = "$jube_pat_nint"

        jube1pat5 = r"\$patnfp"
        jube2pat5 = "$jube_pat_nfp"

        jube1pat6 = r"\$patnwrd"
        jube2pat6 = "$jube_pat_nwrd"

        jube1pat7 = r"\$patbl"
        jube2pat7 = "$jube_pat_bl"

        new_regexp = regexp
        new_regexp = re.sub(jube1pat1, jube2pat1, new_regexp)
        new_regexp = re.sub(jube1pat2, jube2pat2, new_regexp)
        new_regexp = re.sub(jube1pat3, jube2pat3, new_regexp)
        new_regexp = re.sub(jube1pat4, jube2pat4, new_regexp)
        new_regexp = re.sub(jube1pat5, jube2pat5, new_regexp)
        new_regexp = re.sub(jube1pat6, jube2pat6, new_regexp)
        new_regexp = re.sub(jube1pat7, jube2pat7, new_regexp)

        return new_regexp

    def _create_root(self, filename):
        """Create main root for analyse.xml"""
        tree = ET.parse(self._main_dir + "/" + filename)
        try:
            xml = jube2.util.element_tree_tostring(tree.getroot(),
                                                   encoding="UTF-8")
            xml.encode(sys.getfilesystemencoding())
        except UnicodeEncodeError as uee:
            raise ValueError("Your terminal only allow '{0}' encoding. {1}"
                             .format(sys.getfilesystemencoding(), str(uee)))

        return tree.getroot()

    def _extract_includepattern(self, xml_file):
        """Gather files with patterns to be converted"""
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = self._name

#       search also in analyse.xml for patterns
        self._pattern_file_list.append("analyse.xml")
        for item in jube2.util.get_tree_elements(xml_root, tag):
            for pattern in item.findall('includepattern'):
                prefix_name = item.get('cname')
                if prefix_name == self._cname:
                    self._pattern_file_list.append(pattern.attrib["file"])
                else:
                    continue


class _JubeStep(object):

    """Represent jube 1 xml files as steps and combine input"""

    def __init__(self, step_name):
        self._name = step_name
        self._cname = ""
        self._use_list = set()
        self._do_list = []
        self._last_command = None
        self._step_element = None
        self._verify_do_list = []

# Init: each step needs the global parameterset
        self._use_list.add(GLOBAL_PARAMETERSET_NAME)

    @property
    def verify_do_list(self):
        """Get do list from verify step"""
        return self._verify_do_list

    @verify_do_list.setter
    def verify_do_list(self, value):
        """Set do list from verify step"""
        self._verify_do_list = value

    @property
    def step_element(self):
        """Get step element"""
        return self._step_element

    @property
    def name(self):
        """Return name"""
        return self._name

    @property
    def cname(self):
        """Return cname given in jube version 1"""
        return self._cname

    @cname.setter
    def cname(self, value):
        """Set cname from jube version 1 xml files"""
        self._cname = value

    @property
    def use_list(self):
        """Return use list"""
        return self._use_list

    @property
    def do_list(self):
        """Get do list"""
        return self._do_list

    @property
    def last_command(self):
        """Get last command"""
        return self._last_command

    @last_command.setter
    def last_command(self, value):
        """Set last command"""
        self._last_command = value

    def build_step_element(self):
        """Create step for benchmark"""
        step = ET.Element('step')
        step.set("name", self._name)

#       Dependencies
        if self._name == 'compile':
            step.set('depend', 'prepare')
        if self._name == 'execution':
            step.set('depend', 'prepare,compile')
        if self._name == 'verify':
            step.set('depend', 'execution')

        if self._last_command is not None:
            comment = ET.Comment(
                "$shared_dir in the line above isn't set yet.")
            step.append(comment)
            step.set("shared", "$shared_dir")
        for item in self._use_list:
            use = ET.SubElement(step, 'use')
            use.text = item

        for item in self._do_list:
            do_node = ET.SubElement(step, 'do')
            do_node.text = item

        if self._last_command is not None:
            do_node = ET.SubElement(step, 'do', {"shared": "True"})
            do_node.text = self._last_command

        if self._name == 'execution':
            ET.SubElement(step, 'do', {"done_file": "end_info.xml"})
            if self._verify_do_list:
                for item in self._verify_do_list:
                    do_node = ET.SubElement(step, 'do')
                    do_node.text = item

        self._step_element = step


class _JubeBenchmark(object):

    """Represent jube 1 benchmark as jube 2 benchmark and fill in steps"""

    def __init__(self, benchmark_name):
        self._name = benchmark_name
        self._compile_step = None
        self._execution_step = None
        self._prepare_step = None
        self._analyser = None
        self._verify_step = None
        self._benchmark_element = None
        self._fileset_node = set()

    @property
    def benchmark_element(self):
        """Get benchmark element"""
        return self._benchmark_element

    @property
    def fileset_node(self):
        """Get fileset node"""
        return self._fileset_node

    @property
    def compile_step(self):
        """Get compile step"""
        return self._compile_step

    @compile_step.setter
    def compile_step(self, value):
        """Set compile step"""
        self._compile_step = value

    @property
    def execution_step(self):
        """Get execution step"""
        return self._execution_step

    @execution_step.setter
    def execution_step(self, value):
        """Set execution step"""
        self._execution_step = value

    @property
    def prepare_step(self):
        """Get prepare step"""
        return self._prepare_step

    @prepare_step.setter
    def prepare_step(self, value):
        """Set prepare step"""
        self._prepare_step = value

    @property
    def verify_step(self):
        """Get verify step"""
        return self._verify_step

    @verify_step.setter
    def verify_step(self, value):
        """Set verify step"""
        self._verify_step = value

    @property
    def analyser(self):
        """Get analyser"""
        return self._analyser

    @analyser.setter
    def analyser(self, value):
        """Set jube analyser"""
        self._analyser = value

    def build_benchmark_element(self):
        """Build node for corresponding benchmark"""
        benchmark = ET.Element('benchmark')
        benchmark.set("name", self._name)
        benchmark.set("outpath", "benchmarks_jube1tojube2")
        benchmark.append(self._prepare_step.step_element)
        benchmark.append(self._compile_step.step_element)
        benchmark.append(self._execution_step.step_element)

#       Integrate filsets in benchmark
        for fileset in self._fileset_node:
            benchmark.append(fileset)
#       Integrate pattern stuff in main XML
        for patternnode in self._analyser.patternset_node_list:
            benchmark.append(patternnode)
        benchmark.append(self._analyser.analyser_node)

#       integrate result stuff
        benchmark.append(self._analyser.result_node)

        self._benchmark_element = benchmark


if __name__ == "__main__":
    pass
