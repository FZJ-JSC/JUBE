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
import re
import tarfile

_global_parameterset_name = "jube_convert_parameter"


class JubeXMLConverter(object):
    _global_counter = 0
    _dummy_check_set = set()
    _global_calc_counter = 0

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

#         The global parameterset is needed in each benchmark and therefore needs
#         to be included
        self._global_parameterset = self._init_global_parameterset()

#         Needed to gather perl expressions of corresponding substituteset
        self._calc_parameterset_node = None
        self._calc_parameterset_name = ""

    def _init_global_parameterset(self):
        global_parameterset = ET.Element('parameterset')
        global_parameterset.set('name', _global_parameterset_name)
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

        return global_parameterset

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

#       Add platform as needed in jube version 1
        if(name == self._global_platform_name):
            parameter = ET.SubElement(
                parameterset, 'parameter', {'name': 'platform'})
            parameter.text = self._global_platform_name

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

    def _create_calc_parameter(self, expression, step):
        matches = re.findall("`(.*?)`+", expression)

        for match in matches:
            if (self._calc_parameterset_node is None):
                self._calc_parameterset_node = ET.Element('parameterset')
                set_name = step._name + "_calc_" + \
                    str(self._global_counter)
                self._calc_parameterset_node.set('name', set_name)
                self._calc_parameterset_name = set_name
                step._use_list.add(set_name)

            parameter_name = "jube_calc_" + str(self._global_calc_counter)
#             self._global_calc_counter += 1

            parameter = ET.SubElement(
                self._calc_parameterset_node, 'parameter', {'name': parameter_name,
                                                            'mode': 'perl'})
            parameter.text = match
            pattern = "`" + match + "`"
            repl = "$" + parameter_name

            expression = expression.replace(pattern, repl)
            self._global_calc_counter += 1
        return expression

    def _has_perl_expression(self, expression):
        if (re.findall("`(.*?)`+", expression)):
            return True
        else:
            return False

    def _create_compile_fileset_node(self, xml_file, jube_step, benchmark):
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step._name
        if (tag != "compile"):
            return

        for item in xml_root.iter(tag):
            prefix_name = item.get('cname')
            if (prefix_name != jube_step._cname):
                continue
            src_node = item.find('src')
            fileset_node = ET.Element('fileset')
            fileset_name = jube_step._name + \
                '_files_' + str(self._global_counter)
            fileset_node.set('name', fileset_name)
        
            copy_node = ET.SubElement(
                fileset_node, 'copy', {'directory': src_node.attrib["directory"],
                                       'separator': ' '})
            copy_node.text = src_node.attrib["files"]

            tar_command = self._create_tar_command_for_compile(
                src_node.attrib["files"])
            prepare_node = ET.SubElement(fileset_node, 'prepare')
            prepare_node.text = tar_command

            jube_step._use_list.add(fileset_name)
            benchmark._fileset_node.add(fileset_node)

    def _create_tar_command_for_compile(self, files):
        command = "for i in"
        file_list = files.split(" ")
        tarfile_list = []
        for filename in file_list:
            if tarfile.is_tarfile(filename):
                tarfile_list.append(filename)

        if not tarfile_list:
            return ""
        for filename in tarfile_list:
            command = command + " " + filename
        command = command + "; do tar xf $i; done"
        return command

    def _create_fileset_node(self, xml_file, jube_step, benchmark):
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step._name
#       check necessary execution (main file) but execute in execute.xml
        if (jube_step._name == "execution"):
            tag = "execute"

        for item in xml_root.iter(tag):
            prefix_name = item.get('cname')
            if (prefix_name != jube_step._cname):
                continue
            input_node = item.find('input')
            fileset_node = ET.Element('fileset')
            fileset_name = jube_step._name + \
                '_files_' + str(self._global_counter)
            fileset_node.set('name', fileset_name)
            copy_node = ET.SubElement(fileset_node, 'copy', {"separator": " "})
            copy_node.text = input_node.attrib['files']
            if(tag == "execute"):
                copy_node = ET.SubElement(
                    fileset_node, 'copy', {'rel_path_ref': 'internal'})
                copy_node.text = "prepare/*"
                link_node = ET.SubElement(
                    fileset_node, 'link', {'rel_path_ref': 'internal'})
                link_node.text = "compile/$execname"
            jube_step._use_list.add(fileset_name)
            benchmark._fileset_node.add(fileset_node)

    def extract_substitutes_and_convert(self, xml_file, jube_step):
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step._name
#       check necessary execution (main file) but execute in execute.xml
        if (jube_step._name == "execution"):
            tag = "execute"

#            Substitution of perl expressions are also done in this loop.
#            calc_parameterset needs to be emptied for each step to fill
# in only those expressions which are relevant for the underlying step
#         self._calc_parameterset_name = ""
        self._calc_parameterset_node = None
        for item in xml_root.iter(tag):
            self._global_counter = 0
            for substitute in item.findall('substitute'):

                prefix_name = item.get('cname')
#               check if substituteset is relevant for current benchmark
                if (prefix_name != jube_step._cname):
                    continue
#                     jube_step._use_list.add(substituteset_name)

                substituteset_name = prefix_name + "_" + \
                    tag + "_" + str(self._global_counter)
                substituteset = ET.Element('substituteset')
                substituteset.set('name', substituteset_name)

#               Build iofile tag
                iofile_dict = {
                    "in": substitute.attrib['infile'],
                    "out": substitute.attrib['outfile']}
                iofile = ET.SubElement(substituteset, 'iofile', iofile_dict)

                for subs in substitute.findall('sub'):
                    attribs_for_sub = {}
                    for k, v in subs.attrib.items():
                        if(k == "from"):
                            attribs_for_sub["source"] = v
                        else:
                            if(self._has_perl_expression(v)):
                                attribs_for_sub["dest"] = self._create_calc_parameter(
                                    v, jube_step)
                            else:
                                attribs_for_sub["dest"] = v
#
                    sub = ET.SubElement(substituteset, 'sub', attribs_for_sub)

                    jube_step._use_list.add(substituteset_name)

                if(substituteset_name not in self._dummy_check_set):
                    self._main_element.append(substituteset)
                    self._dummy_check_set.add(substituteset_name)
#                     jube_step._use_list.add(substituteset_name)
#                     add calc set to main node if existent
                    if((self._calc_parameterset_node is not None) and (self._calc_parameterset_name not in self._dummy_check_set)):
                        self._dummy_check_set.add(self._calc_parameterset_name)
                        self._main_element.append(self._calc_parameterset_node)

#                         self._calc_parameterset_node = None
                self._global_counter += 1
#

    def _main_comment(self):
        text = """ Hint for the user!
        Jube version 2 provides some help variables which are not necessarily available in jube version 2. 
        These variables are as follows:
            benchxmlfile
            pwd
            benchhome
            tmpdir
            rundir
            tmplogdir
            configdir
            bstartdate
            benchname
            name
            platform
            cmpdir
            benddate
            
            Have a look at the "do" tags of this file and check whether some of these variables are used.
            Not all of them make sense in the context of jube version 2 and might be removed.
            Furthermore type "jube help jube_variables" to get a list of variables available in jube version 2.
            
            In the case you used "lastcommand" in jube version 1 you need to give a value for $shared_dir given in the corresponding execution step (just grep for "$shared_dir")."""

        comment = ET.Comment(text)
        self._main_element.append(comment)

    def convert_main_file(self):
        self._main_element = ET.Element('jube')
        main_tree = ET.parse(self._main_xml_file)
        main_root = main_tree.getroot()
        self._main_comment()
        self._main_element.append(self._global_parameterset)

        for benchmark in main_root.iter('benchmark'):
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
            if (benchmark_name not in self._benchmark_dict):
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

    def _benchmark_init(self, benchmark_obj, pset, compile_dict,
                        execution_dict, prepare_dict,
                        verify_dict, analyse_dict):
        #       Compile
        compile_step = _JubeStep("compile")
        compile_step._use_list.add(pset)
        compile_step._cname = self._check_and_sub_platform_var(
            compile_dict.attrib["cname"])
        self.extract_substitutes_and_convert(
            self._compile_xml_file, compile_step)
        self._extract_commands(self._compile_xml_file, compile_step)
        self._create_compile_fileset_node(
            self._compile_xml_file, compile_step, benchmark_obj)
        benchmark_obj._compile_step = compile_step
        compile_step._build_step_element()

#       Execute
        execution_step = _JubeStep("execution")
        execution_step._use_list.add(pset)
        execution_step._cname = self._check_and_sub_platform_var(
            execution_dict.attrib["cname"])
        self.extract_substitutes_and_convert(
            self._execute_xml_file, execution_step)
        self._extract_commands(self._execute_xml_file, execution_step)
        self._extract_environment(self._execute_xml_file, execution_step)
        self._create_fileset_node(
            self._execute_xml_file, execution_step, benchmark_obj)
        benchmark_obj._execution_step = execution_step
#         execution_step._build_step_element()

#       Prepare
        prepare_step = _JubeStep("prepare")
        prepare_step._use_list.add(pset)
        prepare_step._cname = self._check_and_sub_platform_var(
            prepare_dict.attrib["cname"])
        self.extract_substitutes_and_convert(
            self._prepare_xml_file, prepare_step)
        self._extract_commands(self._prepare_xml_file, prepare_step)
        self._create_fileset_node(
            self._prepare_xml_file, prepare_step, benchmark_obj)
        benchmark_obj._prepare_step = prepare_step
        prepare_step._build_step_element()

#       Verify
        verify_step = _JubeStep("verify")
        verify_step._use_list.add(pset)
        verify_step._cname = self._check_and_sub_platform_var(
            verify_dict.attrib["cname"])
        self.extract_substitutes_and_convert(
            self._verify_xml_file, verify_step)
        self._extract_commands(self._verify_xml_file, verify_step)

#         verify command(s) are added to execute commands. In fact these two steps
#        are merged and verify wont't exists as a step
        for verify_do in verify_step._do_list:
            execution_step._do_list.append(verify_do)
#             print (verify_do)
        for verify_use in verify_step._use_list:
#             print (verify_use)
            execution_step._use_list.add(verify_use)
        execution_step._build_step_element()

        benchmark_obj._verify_step = verify_step
        verify_step._build_step_element()

#       Analyse
        analyse_cname = self._check_and_sub_platform_var(
            analyse_dict.attrib["cname"])
        analyzer = _JubeAnalyzer(
            "analyse", analyse_cname, self._main_dir, self._analyse_xml_file)
#         analyzer._extract_includepattern(self._analyse_xml_file)
        benchmark_obj._analyzer = analyzer

#        Finally, build benchmark node
        benchmark_obj._build_benchmark_element()

    def _extract_commands(self, xml_file, jube_step):
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step._name
#       check necessary execution (main file) but execute in execute.xml
        if (jube_step._name == "execution"):
            tag = "execute"

        for item in xml_root.iter(tag):
            for command in item.findall('command'):
                prefix_name = item.get('cname')
                if (prefix_name == jube_step._cname):
                    jube_step._do_list.append(
                        self._beautify_command(command.text))
                else:
                    continue

        for item in xml_root.iter(tag):
            for lastcommand in item.findall('lastcommand'):
                prefix_name = item.get('cname')
                if (prefix_name == jube_step._cname):
                    jube_step._last_command = self._beautify_command(
                        lastcommand.text)
                else:
                    continue

    def _beautify_command(self, command_text):
        newline = "\n"
        tab = "\t"
        command_text = re.sub(newline, "", command_text)
        command_text = re.sub(tab, "", command_text)
        command_text = command_text.strip()
        return command_text

    def _extract_environment(self, xml_file, jube_step):
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = jube_step._name
#       check necessary execution (main file) but execute in execute.xml
        if (jube_step._name == "execution"):
            tag = "execute"

        for item in xml_root.iter(tag):
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
                if (prefix_name == jube_step._cname):
                    jube_step._use_list.add(envset_name)
                else:
                    continue

                if(envset_name not in self._dummy_check_set):
                    self._main_element.append(envset)
                    self._dummy_check_set.add(envset_name)
                self._global_counter += 1

    def write_main_file(self, output="benchmarks_jube2_new.xml"):
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

        for k, v in self._benchmark_dict.items():
            self._main_element.append(v._benchmark_element)

        self.write_platformfile(self._main_dir + "platform_jube2_new.xml")
        self.write_main_file(self._main_dir + "benchmarks_jube2_new.xml")

        message = """            Don't forget to have a look at 
            benchmarks_jube2.xml and platform_jube2.xml 
            and check whether you get what you  expect.
            In particular, notice the comments in 
            benchmarks_jube2.xml."""
        print (message)
#         self._print_struct()

    def _print_struct(self):
        for k, v in self._benchmark_dict.items():
            print("")
            v._print_benchmark()

    def _check_and_sub_platform_var(self, cname):
        if (cname == "$platform"):
            return self._global_platform_name
        else:
            return cname


class _JubeAnalyzer(object):

    def __init__(self, name, cname, main_dir, xml_file):
        self._name = name
        self._cname = cname
        self._main_dir = main_dir
        self._pattern_file_list = []
        self._use_list = set()
        self._result_node = None
        self._extract_includepattern(xml_file)

#       Needed for result table
        self._pattern_name_set = set()

        self._patternset_node_list = []
        self._create_patternset_node_list()

        self._analyzer_node = None
        self._create_analyzer_node()

        self_result_node = None
        self._create_result_node()

    def _create_analyzer_node(self):
        self._analyzer_node = ET.Element("analyzer")
        self._analyzer_node.set('name', 'analyze')
        for use in self._use_list:
            use_tag = ET.SubElement(self._analyzer_node, "use")
            use_tag.text = use

        analyse_tag = ET.SubElement(
            self._analyzer_node, "analyse", {"step": "execution"})
        file_tag = ET.SubElement(analyse_tag, "file")
        file_tag.text = "stdout"

    def _create_patternset_node_list(self):
        for patternfile in self._pattern_file_list:
            root = self._create_root(patternfile)
            patternset = ET.Element('patternset')
            usename = os.path.basename(patternfile)
            patternset.set('name', usename)
            self._use_list.add(usename)
            for parm in root.findall('parm'):
                parm_dict = parm.attrib

#     Adaption to jube2 attributes
                if re.search('line', parm_dict['mode']):
                    parm_dict['mode'] = 'pattern'

                if parm_dict['mode'] == 'derived':
                    parm_dict['mode'] = 'perl'

                self._pattern_name_set.add(parm_dict['name'])
                subelement = ET.SubElement(patternset, 'pattern', parm_dict)
                subelement.text = self._substitute_jube_pattern(parm.text)

            self._patternset_node_list.append(patternset)

    def _create_result_node(self):
        self._result_node = ET.Element('result')
        text = """All pattern names appear in the table. This might be more than you need. Remove accordingly"""
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

    def _substitute_jube_pattern(self, regexp):
        jube1pat1 = "\$patint"
        jube2pat1 = "jube_pat_int"

        jube1pat2 = "\$patfp"
        jube2pat2 = "$jube_pat_fp"

        jube1pat3 = "\$patwrd"
        jube2pat3 = "$jube_pat_wrd"

        jube1pat4 = "\$patnint"
        jube2pat4 = "$jube_pat_nint"

        jube1pat5 = "\$patnfp"
        jube2pat5 = "$jube_pat_nfp"

        jube1pat6 = "\$patnwrd"
        jube2pat6 = "$jube_pat_nwrd"

        jube1pat7 = "\$patbl"
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
        tree = ET.parse(self._main_dir + "/" + filename)
        try:
            xml = ET.tostringlist(tree.getroot(), encoding="UTF-8")
            for line in xml:
                line.decode("UTF-8").encode(sys.getfilesystemencoding())
        except UnicodeEncodeError as uee:
            raise ValueError("Your terminal only allow '{0}' encoding. {1}"
                             .format(sys.getfilesystemencoding(), str(uee)))

        return tree.getroot()

    def _extract_includepattern(self, xml_file):
        xml_tree = ET.parse(xml_file)
        xml_root = xml_tree.getroot()

        tag = self._name
        for item in xml_root.iter(tag):
            for pattern in item.findall('includepattern'):
                prefix_name = item.get('cname')
                if (prefix_name == self._cname):
                    self._pattern_file_list.append(pattern.attrib["file"])
                else:
                    continue

    def _print_analyzer(self):
        print("\t\tAnalyzer:\t\t", self._name)
        print("\t\tcname:\t\t", self._cname)
        print("\t\tpattern file list:\t\t", self._pattern_file_list)
        print("-------------------------------------------")


class _JubeStep(object):

    def __init__(self, step_name):
        self._name = step_name
        self._cname = ""
        self._use_list = set()
        self._do_list = []
        self._last_command = None
        self._step_element = None

# Init: each step needs global parameterset
        self._use_list.add(_global_parameterset_name)

    def _build_step_element(self):
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
            do = ET.SubElement(step, 'do')
            if(self._name == 'execution'):
                do.set('done_file', 'end_info.xml')
            do.text = item

        if self._last_command is not None:
            do = ET.SubElement(step, 'do', {"shared": "True"})

        self._step_element = step

    def _print_step(self):
        print("\t\tStep:\t\t", self._name)
        print("\t\tcname:\t\t", self._cname)
        print("\t\tuse:\t\t", self._use_list)
        print("\t\tdo:\t\t", self._do_list)
        print("\t\tlast_command:\t\t", self._last_command)
        print("-------------------------------------------")


class _JubeBenchmark(object):

    def __init__(self, benchmark_name):
        self._name = benchmark_name
        self._compile_step = None
        self._execution_step = None
        self._prepare_step = None
        self._analyzer = None
        self._benchmark_element = None
        self._fileset_node = set()

    def _build_benchmark_element(self):
        benchmark = ET.Element('benchmark')
        benchmark.set("name", self._name)
        benchmark.append(self._prepare_step._step_element)
        benchmark.append(self._compile_step._step_element)
        benchmark.append(self._execution_step._step_element)
#         verify stuff is included in execution step
#         benchmark.append(self._verify_step._step_element)

#       Integrate filsets in benchmark
        for fileset in self._fileset_node:
            benchmark.append(fileset)
#       Integrate pattern stuff in main XML
        for patternnode in self._analyzer._patternset_node_list:
            benchmark.append(patternnode)
        benchmark.append(self._analyzer._analyzer_node)

#       integrate result stuff
        benchmark.append(self._analyzer._result_node)

        self._benchmark_element = benchmark

    def _print_benchmark(self):
        print("Benchmark:\t", self._name)
        print("####################################")
        if self._compile_step is not None:
            self._compile_step._print_step()
        if self._execution_step is not None:
            self._execution_step._print_step()
        if self._prepare_step is not None:
            self._prepare_step._print_step()
        if self._verify_step is not None:
            self._verify_step._print_step()
        if self._analyzer is not None:
            self._analyzer._print_analyzer()

if __name__ == "__main__":
    pass
