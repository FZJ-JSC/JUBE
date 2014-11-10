"""Basic I/O module"""

# #############################################################################
# #  JUBE Benchmarking Environment                                           ##
# #  http://www.fz-juelich.de/jsc/jube                                       ##
# #############################################################################
# #  Copyright (c) 2008-2014                                                 ##
# #  Forschungszentrum Juelich, Juelich Supercomputing Centre                ##
# #                                                                          ##
# #  See the file LICENSE in the package base directory for details          ##
# #############################################################################

from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as ET
import os
try:
    import queue
except ImportError:
    import Queue as queue
import jube2.benchmark
import jube2.substitute
import jube2.parameter
import jube2.fileset
import jube2.pattern
import jube2.workpackage
import jube2.analyzer
import jube2.step
import jube2.util
import jube2.conf
import jube2.result
import sys
import re
import jube2.log
import collections

INCLUDE_PATH = list()
LOGGER = jube2.log.get_logger(__name__)


def benchmarks_from_xml(filename, tags=None):
    """Return a dict of benchmarks

    Here parametersets are global and accessible to all benchmarks defined
    in the corresponding XML file.
    """
    benchmarks = dict()
    LOGGER.debug("Parsing {}".format(filename))

    if not os.path.isfile(filename):
        raise IOError("Benchmark configuration file not found: \"{}\""
                      .format(filename))
    try:
        tree = ET.parse(filename)
    except ET.ParseError as parseerror:
        raise ET.ParseError(("XML parse error in \"{0}\": {1}\n" +
                             "XML is not valid, use validation tool.")
                            .format(filename, str(parseerror)))

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

    valid_tags = ["selection", "include-path", "parameterset", "benchmark",
                  "substituteset", "fileset", "include", "patternset"]

    # Preprocess xml-tree (using tags-attribute)
    LOGGER.debug("  Remove invalid tags using tags-attribute")
    if tags is None:
        tags = set()
    LOGGER.debug("    Available tags: {}"
                 .format(jube2.conf.DEFAULT_SEPARATOR.join(tags)))
    _remove_invalid_tags(tree.getroot(), tags)

    # Read selection area
    selection = tree.findall("selection")
    if len(selection) > 1:
        raise ValueError("Only one <selection> tag allowed")
    elif len(selection) == 1:
        only_bench, not_bench, new_tags = _extract_selection(selection[0])
    else:
        only_bench = list()
        not_bench = list()
        new_tags = set()

    # Read include-path
    include_path = tree.findall("include-path")
    if len(include_path) > 1:
        raise ValueError("Only one <include-path> tag allowed")
    elif len(include_path) == 1:
        _extract_include_path(include_path[0])

    # Preprocess xml-tree
    LOGGER.debug("  Preprocess xml tree")
    _preprocessor(tree.getroot())

    # Add file tags and rerun removing invalid tags
    tags.update(new_tags)
    _remove_invalid_tags(tree.getroot(), tags)

    # Check tags
    for element in tree.getroot():
        _check_tag(element, valid_tags)

    # Read all global parametersets
    global_parametersets = _extract_parametersets(tree, tags)
    # Read all global substitutesets
    global_substitutesets = _extract_substitutesets(tree, tags)
    # Read all global filesets
    global_filesets = _extract_filesets(tree, tags)
    # Read all global patternsets
    global_patternsets = _extract_patternsets(tree, tags)

    # At this stage we iterate over benchmarks
    benchmark_list = tree.findall("benchmark")
    for benchmark_tree in benchmark_list:
        _benchmark_preprocessor(benchmark_tree)
        benchmark = _create_benchmark(benchmark_tree,
                                      global_parametersets,
                                      global_substitutesets,
                                      global_filesets,
                                      global_patternsets,
                                      tags)
        benchmarks[benchmark.name] = benchmark
    return benchmarks, only_bench, not_bench


def _remove_invalid_tags(etree, tags=None):
    """Remove tags which contain an invalid tags-attribute"""
    if tags is None:
        tags = set()
    children = list(etree)
    for child in children:
        tag_tags_str = child.get("tag")
        if tag_tags_str is not None:
            tag_tags = set([tag.strip() for tag in
                            tag_tags_str.split(jube2.conf.DEFAULT_SEPARATOR)])
            valid_tags = set()
            invalid_tags = set()
            # Switch tags between valid and invalid tagnames
            for tag in tag_tags:
                if (len(tag) > 1) and (tag[0] == "!"):
                    invalid_tags.add(tag[1:])
                elif (len(tag) > 0) and (tag[0] != "!"):
                    valid_tags.add(tag)
            # Tag selection
            if (((len(valid_tags) > 0) and
                 (len(valid_tags.intersection(tags)) == 0)) or
                ((len(invalid_tags) > 0) and
                 (len(invalid_tags.intersection(tags)) > 0))):
                etree.remove(child)
                continue
        _remove_invalid_tags(child, tags)


def _preprocessor(etree):
    """Preprocess the xml-file by replacing include-tags"""
    children = list(etree)
    new_children = list()
    include_index = 0
    for child in children:
        # Replace include tags
        if child.tag == "include":
            filename = _attribute_from_element(child, "from")
            path = child.get("path", ".")
            if path == "":
                path = "."
            file_path = _find_include_file(filename)
            include_tree = ET.parse(file_path)
            # Remove include-node
            etree.remove(child)
            # Find external nodes
            includes = include_tree.findall(path)
            if len(includes) == 0:
                raise ValueError(("Found nothing to include when using "
                                  "xpath \"{0}\" in file \"{1}\"")
                                 .format(path, filename))
            # Insert external nodes
            for include in includes:
                etree.insert(include_index, include)
                include_index += 1
                new_children.append(include)
            include_index -= 1
        else:
            new_children.append(child)
        include_index += 1
    for child in new_children:
        _preprocessor(child)


def _benchmark_preprocessor(benchmark_etree):
    """Preprocess the xml-tree of given benchmark."""
    LOGGER.debug("  Preprocess benchmark xml tree")
    sets = dict()
    # Search for <use from=""></use> and load external set
    uses = benchmark_etree.findall(".//use")
    for use in uses:
        filename = use.get("from", "")
        if (use.text is not None) and (use.text.strip() != "") and \
           (filename.strip() != ""):
            new_use_str = ""
            for name in use.text.split(jube2.conf.DEFAULT_SEPARATOR):
                name = name.strip()
                if name not in sets:
                    sets[name] = [filename]
                    name = "jube_{0}_{1}".format(name, 0)
                else:
                    if filename in sets[name]:
                        index = sets[name].index(filename)
                    else:
                        sets[name].append(filename)
                        index = len(sets[name] - 1)
                    name = "jube_{0}_{1}".format(name, index)
                if len(new_use_str) > 0:
                    new_use_str += jube2.conf.DEFAULT_SEPARATOR
                # Replace set-name with a internal one
                new_use_str += name
            use.text = new_use_str

    # Create new xml elments
    for name, filenames in sets.items():
        for i, filename in enumerate(filenames):
            set_type = _find_set_type(filename, name)
            set_etree = ET.SubElement(benchmark_etree, set_type)
            set_etree.attrib["name"] = "jube_{0}_{1}".format(name, i)
            set_etree.attrib["init_with"] = "{0}:{1}".format(filename, name)


def _find_include_file(filename):
    """Search for filename in include-pathes and return resulting path"""
    for path in ["."] + INCLUDE_PATH:
        file_path = os.path.join(path, filename)
        if os.path.exists(file_path):
            break
    else:
        raise ValueError(("\"{}\" not found in possible " +
                          "include pathes").format(filename))
    return file_path


def _find_set_type(filename, name):
    """Search for the set-type inside given file"""
    LOGGER.debug(
        "    Searching for type of \"{0}\" in {1}".format(name, filename))
    file_path = _find_include_file(filename)
    etree = ET.parse(file_path)
    found_set = etree.findall(".//*[@name='{0}']".format(name))
    if len(found_set) > 1:
        raise ValueError(("name=\"{0}\" can be found multible times inside " +
                          "\"{1}\"").format(name, file_path))
    elif len(found_set) == 0:
        raise ValueError(("name=\"{0}\" not found inside " +
                          "\"{1}\"").format(name, file_path))
    else:
        if found_set[0].tag in ("parameterset", "substituteset", "fileset",
                                "patternset"):
            return found_set[0].tag
        else:
            raise ValueError(("name=\"{0}\" is not used for a parameterset, " +
                              "substituteset or fileset inside " +
                              "\"{1}\"").format(name, file_path))


def benchmark_info_from_xml(filename):
    """Return name, comment and available tags of first benchmark
    found in file"""
    tree = ET.parse(filename)
    tags = set()
    for tag_etree in tree.findall(".//selection/tag"):
        if tag_etree.text is not None:
            tags.update(set([tag.strip() for tag in
                             tag_etree.text.split(
                                 jube2.conf.DEFAULT_SEPARATOR)]))
    benchmark_etree = tree.find(".//benchmark")
    if benchmark_etree is None:
        raise ValueError("benchmark-tag not found in \"{}\"".format(filename))
    name = _attribute_from_element(benchmark_etree, "name").strip()
    comment_element = benchmark_etree.find("comment")
    if comment_element is not None:
        comment = comment_element.text
        if comment is None:
            comment = ""
    else:
        comment = ""
    comment = re.sub(r"\s+", " ", comment).strip()
    return name, comment, tags


def analyse_result_from_xml(filename):
    """Read existing analyse out of xml-file"""
    LOGGER.debug("Parsing {}".format(filename))
    tree = ET.parse(filename)
    analyse_result = dict()
    analyzer = tree.findall(".//analyzer")
    for analyzer_etree in analyzer:
        analyzer_name = _attribute_from_element(analyzer_etree, "name")
        analyse_result[analyzer_name] = dict()
        for step_etree in analyzer_etree:
            _check_tag(step_etree, ["step"])
            step_name = _attribute_from_element(step_etree, "name")
            analyse_result[analyzer_name][step_name] = dict()
            for workpackage_etree in step_etree:
                _check_tag(workpackage_etree, ["workpackage"])
                wp_id = int(_attribute_from_element(workpackage_etree, "id"))
                analyse_result[analyzer_name][step_name][wp_id] = dict()
                for file_etree in workpackage_etree:
                    _check_tag(file_etree, ["file"])
                    filename = _attribute_from_element(file_etree, "name")
                    analyse_result[analyzer_name][step_name][wp_id][
                        filename] = dict()
                    for pattern_etree in file_etree:
                        _check_tag(pattern_etree, ["pattern"])
                        pattern_name = _attribute_from_element(pattern_etree,
                                                               "name")
                        pattern_type = _attribute_from_element(pattern_etree,
                                                               "type")
                        value = pattern_etree.text
                        value = jube2.util.convert_type(pattern_type, value)
                        analyse_result[analyzer_name][step_name][
                            wp_id][filename][pattern_name] = value
    return analyse_result


def workpackages_from_xml(filename, benchmark):
    """Read existing workpackage data out of a xml-file"""
    workpackages = dict()
    # tmp: Dict workpackage_id => workpackage
    tmp = dict()
    # parents_tmp: Dict workpackage_id => list of parent_workpackage_ids
    parents_tmp = dict()
    work_list = queue.Queue()
    LOGGER.debug("Parsing {}".format(filename))
    if not os.path.isfile(filename):
        raise IOError("Workpackage configuration file not found: \"{}\""
                      .format(filename))
    tree = ET.parse(filename)
    for element in tree.getroot():
        _check_tag(element, ["workpackage"])
        # Read XML-data
        workpackage_id, step_name, parameterset, parents, iteration = \
            _extract_workpackage_data(element)
        # Search for step
        step = benchmark.steps[step_name]
        tmp[workpackage_id] = \
            jube2.workpackage.Workpackage(benchmark, step, parameterset,
                                          jube2.parameter.Parameterset(),
                                          workpackage_id, iteration)
        parents_tmp[workpackage_id] = parents
        if len(parents) == 0:
            work_list.put(tmp[workpackage_id])

    # Rebuild graph structure
    for workpackage_id in parents_tmp:
        for parent_id in parents_tmp[workpackage_id]:
            tmp[workpackage_id].add_parent(tmp[parent_id])
            tmp[parent_id].add_children(tmp[workpackage_id])

    # Rebuild history
    done_list = list()
    while not work_list.empty():
        workpackage = work_list.get_nowait()
        if workpackage.id in parents_tmp:
            for parent_id in parents_tmp[workpackage.id]:
                workpackage.history.add_parameterset(
                    tmp[parent_id].history)
        done_list.append(workpackage)
        for child in workpackage.children:
            all_done = True
            for parent in child.parents:
                all_done = all_done and (parent in done_list)
            if all_done and (child not in done_list):
                work_list.put(child)
        # Add personal parameterset to personal history
        workpackage.history.add_parameterset(workpackage.parameterset)

    # Store workpackage data
    work_list = queue.Queue()
    for step_name in benchmark.steps:
        workpackages[step_name] = list()
    for workpackage in tmp.values():
        if len(workpackage.parents) == 0:
            workpackage.queued = True
            work_list.put(workpackage)
        workpackages[workpackage.step.name].append(workpackage)

    return workpackages, work_list


def _extract_workpackage_data(workpackage_etree):
    """Extract workpackage information from etree

    Return workpackage id, name of step, local parameterset and list of
    parent ids
    """
    valid_tags = ["step", "parameterset", "parents"]
    for element in workpackage_etree:
        _check_tag(element, valid_tags)
    workpackage_id = int(_attribute_from_element(workpackage_etree, "id"))
    step_etree = workpackage_etree.find("step")
    iteration = int(step_etree.get("iteration", "0").strip())
    step_name = step_etree.text.strip()
    parameterset_etree = workpackage_etree.find("parameterset")
    if parameterset_etree is not None:
        parameters = _extract_parameters(parameterset_etree)
    else:
        parameters = list()
    parameterset = jube2.parameter.Parameterset()
    for parameter in parameters:
        parameterset.add_parameter(parameter)
    parents_etree = workpackage_etree.find("parents")
    if parents_etree is not None:
        parents = [int(parent) for parent in
                   parents_etree.text.split(jube2.conf.DEFAULT_SEPARATOR)]
    else:
        parents = list()
    return workpackage_id, step_name, parameterset, parents, iteration


def _extract_selection(selection_etree):
    """Extract selction information from etree

    Return names of benchmarks ([only,...],[not,...])
    """
    LOGGER.debug("  Parsing <selection>")
    valid_tags = ["only", "not", "tag"]
    only_bench = list()
    not_bench = list()
    tags = set()
    for element in selection_etree:
        _check_tag(element, valid_tags)
        separator = jube2.conf.DEFAULT_SEPARATOR
        if element.text is not None:
            if element.tag == "only":
                only_bench = only_bench + element.text.split(separator)
            elif element.tag == "not":
                not_bench = not_bench + element.text.split(separator)
            elif element.tag == "tag":
                tags.update(set([tag.strip() for tag in
                                 element.text.split(separator)]))
    only_bench = [bench.strip() for bench in only_bench]
    not_bench = [bench.strip() for bench in not_bench]
    return only_bench, not_bench, tags


def _extract_include_path(include_path_etree):
    """Extract include-path pathes from etree"""
    LOGGER.debug("Parsing <include-path>")
    valid_tags = ["path"]
    for element in include_path_etree:
        _check_tag(element, valid_tags)
        path = element.text
        if path is None:
            raise ValueError("Empty \"<path>\" found")
        path = path.strip()
        if len(path) == 0:
            raise ValueError("Empty \"<path>\" found")
        path = os.path.expandvars(os.path.expanduser(path))
        jube2.jubeio.INCLUDE_PATH += [path]


def _create_benchmark(benchmark_etree, global_parametersets,
                      global_substitutesets, global_filesets,
                      global_patternsets, tags=None):
    """Create benchmark from etree

    Return a benchmark
    """
    name = _attribute_from_element(benchmark_etree, "name").strip()

    valid_tags = ["parameterset", "substituteset", "fileset", "step",
                  "comment", "patternset", "analyzer", "result"]
    for element in benchmark_etree:
        _check_tag(element, valid_tags)

    comment_element = benchmark_etree.find("comment")
    if comment_element is not None:
        comment = comment_element.text
        if comment is None:
            comment = ""
    else:
        comment = ""
    comment = re.sub(r"\s+", " ", comment).strip()
    outpath = _attribute_from_element(benchmark_etree, "outpath").strip()
    outpath = os.path.expandvars(os.path.expanduser(outpath))
    file_path_ref = benchmark_etree.get("file_path_ref")

    # Combine global and local sets
    parametersets = \
        _combine_global_and_local_sets(global_parametersets,
                                       _extract_parametersets(benchmark_etree,
                                                              tags))

    substitutesets = \
        _combine_global_and_local_sets(global_substitutesets,
                                       _extract_substitutesets(
                                           benchmark_etree, tags))

    filesets = \
        _combine_global_and_local_sets(global_filesets,
                                       _extract_filesets(benchmark_etree,
                                                         tags))

    patternsets = \
        _combine_global_and_local_sets(global_patternsets,
                                       _extract_patternsets(benchmark_etree,
                                                            tags))

    # dict of local steps
    steps = _extract_steps(benchmark_etree)

    # dict of local analyzers
    analyzer = _extract_analyzers(benchmark_etree)

    # dict of local results
    results = _extract_results(benchmark_etree)

    benchmark = jube2.benchmark.Benchmark(name, outpath,
                                          parametersets, substitutesets,
                                          filesets, patternsets, steps,
                                          analyzer, results, comment, tags)

    # Change file path reference for relative file location
    if file_path_ref is not None:
        file_path_ref = file_path_ref.strip()
        file_path_ref = os.path.expandvars(os.path.expanduser(file_path_ref))
        benchmark.file_path_ref = file_path_ref

    return benchmark


def _combine_global_and_local_sets(global_sets, local_sets):
    """Combine global and local sets """
    result_sets = dict(global_sets)
    if set(result_sets) & set(local_sets):
        raise ValueError("\"{}\" not unique"
                         .format(",".join([name for name in
                                           (set(result_sets) &
                                            set(local_sets))])))
    result_sets.update(local_sets)
    return result_sets


def _extract_steps(etree):
    """Extract all steps from benchmark

    Return a dict of steps, e.g. {"compile": Step(...), ...}
    """
    steps = dict()
    for element in etree.findall("step"):
        step = _extract_step(element)
        if step.name in steps:
            raise ValueError("\"{}\" not unique".format(step.name))
        steps[step.name] = step
    return steps


def _extract_step(etree_step):
    """Extract a step from etree

    Return name, list of contents (dicts), depend (list of strings).
    """
    valid_tags = ["use", "do"]

    name = _attribute_from_element(etree_step, "name").strip()
    LOGGER.debug("  Parsing <step name=\"{}\">".format(name))
    tmp = etree_step.get("depend", "").strip()
    iterations = int(etree_step.get("iterations", "1").strip())
    alt_work_dir = etree_step.get("work_dir")
    if alt_work_dir is not None:
        alt_work_dir = alt_work_dir.strip()
    shared_name = etree_step.get("shared")
    if shared_name is not None:
        shared_name = shared_name.strip()
        if shared_name == "":
            raise ValueError("Empty \"shared\" attribute in " +
                             "<step> found.")
    depend = set(val.strip() for val in
                 tmp.split(jube2.conf.DEFAULT_SEPARATOR) if val.strip())

    step = jube2.step.Step(name, depend, iterations, alt_work_dir, shared_name)
    for element in etree_step:
        _check_tag(element, valid_tags)
        if element.tag == "do":
            async_filename = element.get("done_file")
            if async_filename is not None:
                async_filename = async_filename.strip()
            stdout_filename = element.get("stdout")
            if stdout_filename is not None:
                stdout_filename = stdout_filename.strip()
            stderr_filename = element.get("stderr")
            if stderr_filename is not None:
                stderr_filename = stderr_filename.strip()
            active = element.get("active", "true").strip()
            shared_str = element.get("shared", "false").strip()
            if shared_str.lower() == "true":
                if shared_name is None:
                    raise ValueError("<do shared=\"true\"> only allowed "
                                     "inside a <step> which has a shared "
                                     "region")
                shared = True
            elif shared_str == "false":
                shared = False
            else:
                raise ValueError("shared=\"{}\" not allowed. Must be " +
                                 "\"true\" or \"false\"".format(shared_str))
            cmd = element.text
            if cmd is None:
                cmd = ""
            operation = jube2.step.Operation(cmd.strip(),
                                             async_filename,
                                             stdout_filename,
                                             stderr_filename,
                                             active,
                                             shared)
            step.add_operation(operation)
        elif element.tag == "use":
            step.add_uses(_extract_use(element))
    return step


def _extract_analyzers(etree):
    """Extract all analyzer from etree"""
    analyzers = dict()
    for element in etree.findall("analyzer"):
        analyzer = _extract_analyzer(element)
        if analyzer.name in analyzers:
            raise ValueError("\"{}\" not unique".format(analyzer.name))
        analyzers[analyzer.name] = analyzer
    return analyzers


def _extract_analyzer(etree_analyzer):
    """Extract an analyzer from etree"""
    valid_tags = ["use", "analyse"]
    name = _attribute_from_element(etree_analyzer, "name").strip()
    analyzer = jube2.analyzer.Analyzer(name)
    LOGGER.debug("  Parsing <analyzer name=\"{}\">".format(name))
    for element in etree_analyzer:
        _check_tag(element, valid_tags)
        if element.tag == "analyse":
            step_name = _attribute_from_element(element, "step").strip()
            for filename in element:
                if (filename.text is None) or (filename.text.strip() == ""):
                    raise ValueError("Empty <file> found")
                else:
                    analyzer.add_analyse(step_name, filename.text.strip())
        elif element.tag == "use":
            analyzer.add_uses(_extract_use(element))
    return analyzer


def _extract_results(etree):
    """Extract all results from etree"""
    results = collections.OrderedDict()
    valid_tags = ["use", "table"]
    for result_etree in etree.findall("result"):
        result_dir = result_etree.get("result_dir")
        if result_dir is not None:
            result_dir = \
                os.path.expandvars(os.path.expanduser(result_dir.strip()))
        sub_results = collections.OrderedDict()
        uses = list()
        for element in result_etree:
            _check_tag(element, valid_tags)
            if element.tag == "use":
                uses.append(_extract_use(element))
            elif element.tag == "table":
                result = _extract_table(element)
                result.result_dir = result_dir
                sub_results[result.name] = result
        for result in sub_results.values():
            for use in uses:
                result.add_uses(use)
        results.update(sub_results)
    return results


def _extract_table(etree_table):
    """Extract a table from etree"""
    name = _attribute_from_element(etree_table, "name").strip()
    separator = \
        etree_table.get("separator", jube2.conf.DEFAULT_SEPARATOR)
    style = etree_table.get("style", "csv").strip()
    if style not in ["csv", "pretty"]:
        raise ValueError("Not allowed style-type \"{0}\" "
                         "in <table name=\"{1}\">".format(name, style))
    sort_names = etree_table.get("sort", "").split(
        jube2.conf.DEFAULT_SEPARATOR)
    sort_names = [sort_name.strip() for sort_name in sort_names]
    sort_names = [sort_name for sort_name in sort_names if len(sort_name) > 0]
    table = jube2.result.Table(name, style, separator, sort_names)
    for element in etree_table:
        _check_tag(element, ["column"])
        column_name = element.text
        if column_name is None:
            column_name = ""
        column_name = column_name.strip()
        if column_name == "":
            raise ValueError("Empty <column> not allowed")
        colw = element.get("colw")
        if colw is not None:
            colw = int(colw)
        title = element.get("title")
        format_string = element.get("format")
        if format_string is not None:
            format_string = format_string.strip()
        table.add_column(column_name, colw, format_string, title)
    return table


def _extract_use(etree_use):
    """Extract a use from etree"""
    if etree_use.text is not None:
        use_names = [use_name.strip() for use_name in
                     etree_use.text.split(jube2.conf.DEFAULT_SEPARATOR)]
        for use_name in use_names:
            if use_names.count(use_name) > 1:
                raise ValueError(("Can't use element \"{0}\" two times")
                                 .format(use_name))
        return use_names
    else:
        raise ValueError("Empty <use> found")


def _extract_extern_set(filename, set_type, name, search_name=None, tags=None):
    """Load a parameter-/file-/substitutionset from a given file"""
    if search_name is None:
        search_name = name
    LOGGER.debug("    Searching for <{0} name=\"{1}\"> in {2}"
                 .format(set_type, search_name, filename))
    file_path = _find_include_file(filename)
    etree = ET.parse(file_path)
    _remove_invalid_tags(etree.getroot(), tags)
    result_set = None

    # Find element in XML-tree
    elements = etree.findall(".//{0}[@name='{1}']".format(set_type,
                                                          search_name))
    if elements is not None:
        if len(elements) > 1:
            raise ValueError("\"{0}\" found multiple times in \"{1}\""
                             .format(search_name, file_path))
        elif len(elements) == 0:
            raise ValueError("\"{0}\" not found in \"{1}\""
                             .format(search_name, file_path))
        init_with = elements[0].get("init_with")

        # recursive external file open
        if init_with is not None:
            parts = init_with.strip().split(":")
            new_filename = parts[0]
            if len(parts) > 1:
                new_search_name = parts[1]
            else:
                new_search_name = search_name
            if (new_filename == filename) and (new_search_name == search_name):
                raise ValueError(("Can't init <{0} name=\"{1}\"> by itself "
                                  "inside \"{2}\"").format(set_type,
                                                           search_name,
                                                           file_path))
            result_set = _extract_extern_set(new_filename,
                                             set_type, name,
                                             new_search_name)

        if set_type == "parameterset":
            if result_set is None:
                result_set = jube2.parameter.Parameterset(name)
            for parameter in _extract_parameters(elements[0]):
                result_set.add_parameter(parameter)
        elif set_type == "substituteset":
            files, subs = _extract_subs(elements[0])
            if result_set is None:
                result_set = jube2.substitute.Substituteset(name, files, subs)
            else:
                result_set.update_files(files)
                result_set.update_substitute(subs)
        elif set_type == "fileset":
            if result_set is None:
                result_set = jube2.fileset.Fileset(name)
                files = _extract_files(elements[0])
                for file_obj in files:
                    file_obj.file_path_ref = \
                        os.path.join(os.path.dirname(file_path),
                                     file_obj.file_path_ref)
                result_set += files
        elif set_type == "patternset":
            if result_set is None:
                result_set = jube2.pattern.Patternset(name)
            for pattern in _extract_pattern(elements[0]):
                result_set.add_pattern(pattern)
        return result_set
    else:
        raise ValueError("\"{0}\" not found in \"{1}\""
                         .format(name, file_path))


def _extract_parametersets(etree, tags=None):
    """Return parametersets from etree"""
    parametersets = dict()
    for element in etree.findall("parameterset"):
        name = _attribute_from_element(element, "name").strip()
        if name == "":
            raise ValueError("Empty \"name\" attribute in " +
                             "<parameterset> found.")
        LOGGER.debug("  Parsing <parameterset name=\"{}\">".format(name))
        init_with = element.get("init_with")
        if init_with is not None:
            parts = init_with.strip().split(":")
            if len(parts) > 1:
                search_name = parts[1]
            else:
                search_name = None
            parameterset = _extract_extern_set(parts[0],
                                               "parameterset", name,
                                               search_name,
                                               tags)
        else:
            parameterset = jube2.parameter.Parameterset(name)
        for parameter in _extract_parameters(element):
            parameterset.add_parameter(parameter)
        if parameterset.name in parametersets:
            raise ValueError("\"{}\" not unique".format(parameterset.name))
        parametersets[parameterset.name] = parameterset
    return parametersets


def _extract_parameters(etree_parameterset):
    """Extract parameters from parameterset

    Return a list of parameters. Parameters might also include lists"""
    parameters = list()
    for param in etree_parameterset:
        _check_tag(param, ["parameter"])
        name = _attribute_from_element(param, "name").strip()
        if name == "":
            raise ValueError("Empty \"name\" attribute in <parameter> found.")
        separator = param.get("separator",
                              default=jube2.conf.DEFAULT_SEPARATOR)
        parameter_type = param.get("type", default="string").strip()
        parameter_mode = param.get("mode", default="text").strip()
        export_str = param.get("export", default="false").strip()
        export = export_str.lower() == "true"
        if parameter_mode not in ["text"] + jube2.conf.ALLOWED_SCRIPTTYPES:
            raise ValueError(
                ("parameter-mode \"{0}\" not allowed in " +
                 "<parameter name=\"{1}\">").format(parameter_mode,
                                                    name))
        if param.text is None:
            value = ""
        else:
            value = param.text.strip()
        selected_value = param.get("selection")
        if selected_value is not None:
            selected_value = selected_value.strip()
        parameter = \
            jube2.parameter.Parameter.create_parameter(name, value, separator,
                                                       parameter_type,
                                                       selected_value,
                                                       parameter_mode,
                                                       export)
        parameters.append(parameter)
    return parameters


def _extract_patternsets(etree, tags=None):
    """Return patternset from etree"""
    patternsets = dict()
    for element in etree.findall("patternset"):
        name = _attribute_from_element(element, "name").strip()
        if name == "":
            raise ValueError("Empty \"name\" attribute in " +
                             "<patternset> found.")
        LOGGER.debug("  Parsing <patternset name=\"{}\">".format(name))
        init_with = element.get("init_with")
        if init_with is not None:
            parts = init_with.strip().split(":")
            if len(parts) > 1:
                search_name = parts[1]
            else:
                search_name = None
            patternset = _extract_extern_set(parts[0],
                                             "patternset", name,
                                             search_name,
                                             tags)
        else:
            patternset = jube2.pattern.Patternset(name)
        for pattern in _extract_pattern(element):
            patternset.add_pattern(pattern)
        if patternset.name in patternsets:
            raise ValueError("\"{}\" not unique".format(patternset.name))
        patternsets[patternset.name] = patternset
    return patternsets


def _extract_pattern(etree_patternset):
    """Extract pattern from patternset

    Return a list of pattern"""
    patternlist = list()
    for pattern in etree_patternset:
        _check_tag(pattern, ["pattern"])
        name = _attribute_from_element(pattern, "name").strip()
        if name == "":
            raise ValueError("Empty \"name\" attribute in <pattern> found.")
        pattern_mode = pattern.get("mode", default="pattern").strip()
        if pattern_mode not in ["pattern", "text"] + \
                jube2.conf.ALLOWED_SCRIPTTYPES:
            raise ValueError(("pattern-mdoe \"{0}\" not allowed in " +
                              "<pattern name=\"{1}\">").format(pattern_mode,
                                                               name))
        content_type = pattern.get("type", default="string").strip()
        unit = pattern.get("unit", "").strip()
        reduce_options_str = pattern.get("reduce", "first").strip()
        reduce_options = set([opt.strip() for opt in
                              reduce_options_str.split(
                                  jube2.conf.DEFAULT_SEPARATOR)])
        if reduce_options.difference(jube2.pattern.REDUCE_OPTIONS):
            raise ValueError(("unknown reduce option \"{0}\" in " +
                              "<pattern name=\"{1}\">")
                             .format(reduce_options_str, name))
        if pattern.text is None:
            value = ""
        else:
            value = pattern.text.strip()
        patternlist.append(jube2.pattern.Pattern(name, value, pattern_mode,
                                                 content_type, unit,
                                                 reduce_options))
    return patternlist


def _extract_filesets(etree, tags=None):
    """Return filesets from etree"""
    filesets = dict()
    for element in etree.findall("fileset"):
        name = _attribute_from_element(element, "name").strip()
        if name == "":
            raise ValueError("Empty \"name\" attribute in <fileset> found.")
        LOGGER.debug("  Parsing <fileset name=\"{}\">".format(name))
        init_with = element.get("init_with")
        filelist = _extract_files(element)
        if name in filesets:
            raise ValueError("\"{}\" not unique".format(name))
        if init_with is not None:
            parts = init_with.strip().split(":")
            if len(parts) > 1:
                search_name = parts[1]
            else:
                search_name = None
            filesets[name] = _extract_extern_set(parts[0],
                                                 "fileset", name,
                                                 search_name,
                                                 tags)
        else:
            filesets[name] = jube2.fileset.Fileset(name)
        filesets[name] += filelist
    return filesets


def _extract_files(etree_fileset):
    """Return filelist from fileset-etree"""
    filelist = list()
    valid_tags = ["copy", "link", "prepare"]
    for etree_file in etree_fileset:
        _check_tag(etree_file, valid_tags)
        if etree_file.tag in ["copy", "link"]:
            separator = etree_file.get(
                "separator", jube2.conf.DEFAULT_SEPARATOR)
            directory = etree_file.get("directory", default="").strip()
            file_path_ref = etree_file.get("file_path_ref")
            alt_name = etree_file.get("name")
            # Check if the filepath is relativly seen to working dir or the
            # position of the xml-input-file
            is_internal_ref = \
                etree_file.get(
                    "rel_path_ref", default="external").strip() == "internal"
            if etree_file.text is None:
                raise ValueError("Empty filelist in <{}> found."
                                 .format(etree_file.tag))
            files = etree_file.text.strip().split(separator)
            if alt_name is None:
                # Use the original filenames
                names = [os.path.basename(path.strip()) for path in files]
            else:
                # Use the new alternativ filenames
                names = [name.strip() for name in
                         alt_name.split(jube2.conf.DEFAULT_SEPARATOR)]
            if len(names) != len(files):
                raise ValueError("Namelist and filelist must have same " +
                                 "length in <{}>".format(etree_file.tag))
            for i, file_path in enumerate(files):
                path = os.path.join(directory, file_path.strip())
                if etree_file.tag == "copy":
                    file_obj = jube2.fileset.Copy(
                        path, names[i], is_internal_ref)
                elif etree_file.tag == "link":
                    file_obj = jube2.fileset.Link(
                        path, names[i], is_internal_ref)
                if file_path_ref is not None:
                    file_obj.file_path_ref = \
                        os.path.expandvars(os.path.expanduser(
                            file_path_ref.strip()))
                filelist.append(file_obj)
        elif etree_file.tag == "prepare":
            cmd = etree_file.text
            if cmd is None:
                cmd = ""
            cmd = cmd.strip()
            stdout_filename = etree_file.get("stdout")
            if stdout_filename is not None:
                stdout_filename = stdout_filename.strip()
            stderr_filename = etree_file.get("stderr")
            if stderr_filename is not None:
                stderr_filename = stderr_filename.strip()
            prepare_obj = jube2.fileset.Prepare(cmd, stdout_filename,
                                                stderr_filename)
            filelist.append(prepare_obj)
    return filelist


def _extract_substitutesets(etree, tags=None):
    """Extract substitutesets from benchmark

    Return a dict of substitute sets, e.g.
    {"compilesub": ([iofile0,...], [sub0,...])}"""
    substitutesets = dict()
    for element in etree.findall("substituteset"):
        name = _attribute_from_element(element, "name").strip()
        if name == "":
            raise ValueError("Empty \"name\" attribute in <substituteset> " +
                             "found.")
        LOGGER.debug("  Parsing <substituteset name=\"{}\">".format(name))
        init_with = element.get("init_with")
        files, subs = _extract_subs(element)
        if name in substitutesets:
            raise ValueError("\"{}\" not unique".format(name))
        if init_with is not None:
            parts = init_with.strip().split(":")
            if len(parts) > 1:
                search_name = parts[1]
            else:
                search_name = None
            substitutesets[name] = \
                _extract_extern_set(parts[0], "substituteset", name,
                                    search_name, tags)
            substitutesets[name].update_files(files)
            substitutesets[name].update_substitute(subs)
        else:
            substitutesets[name] = \
                jube2.substitute.Substituteset(name, files, subs)
    return substitutesets


def _extract_subs(etree_substituteset):
    """Extract files for substitution and subs from substituteset

    Return a files dict for substitute and a dict of subs
    """
    valid_tags = ["iofile", "sub"]
    files = dict()
    subs = dict()
    for sub in etree_substituteset:
        _check_tag(sub, valid_tags)
        if sub.tag == "iofile":
            in_file = _attribute_from_element(sub, "in").strip()
            out_file = _attribute_from_element(sub, "out").strip()
            in_file = os.path.expandvars(os.path.expanduser(in_file))
            out_file = os.path.expandvars(os.path.expanduser(out_file))
            if in_file == out_file:
                raise ValueError("Input- and outputfile must be different: " +
                                 "{}".format(in_file))
            files[out_file] = in_file
        elif sub.tag == "sub":
            source = _attribute_from_element(sub, "source").strip()
            if source == "":
                raise ValueError("Empty \"source\" attribute in <sub> found.")
            dest = _attribute_from_element(sub, "dest").strip()
            subs[source] = dest
    return (files, subs)


def _attribute_from_element(element, attribute):
    """Return attribute from element
    element -- etree.Element
    attribute -- string
    Raise a useful exception if value not found """
    value = element.get(attribute)
    if value is None:
        raise ValueError("Missing attribute '{0}' in <{1}>"
                         .format(attribute, element.tag))
    return value


def _check_tag(element, valid_tags):
    """Check tag and raise a useful exception if needed
    element -- etree.Element
    valid_tags -- list of valid strings
    """
    if element.tag not in valid_tags:
        raise ValueError("Unknown tag <{}>".format(element.tag))
