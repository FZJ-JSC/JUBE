"""Gives benchmark related info"""

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

import jube2.util
import jube2.conf
import jube2.jubeio
import os
import time
import textwrap
import operator


def print_benchmarks_info(path):
    """Print list of all benchmarks, found in given directory"""
    # Get list of all files and directories in given path
    if not os.path.isdir(path):
        raise OSError("Not a directory: \"{}\"".format(path))
    dir_list = os.listdir(path)
    benchmark_info = list()
    # Search for possible benchmark dirs
    for dir_name in dir_list:
        dir_path = os.path.join(path, dir_name)
        configuration_file = \
            os.path.join(dir_path, jube2.conf.CONFIGURATION_FILENAME)
        if os.path.isdir(dir_path) and os.path.exists(configuration_file):
            try:
                id_number = int(dir_name)
                name_str, comment_str, tags = \
                    jube2.jubeio.benchmark_info_from_xml(configuration_file)
                tags_str = jube2.conf.DEFAULT_SEPARATOR.join(tags)
                time_cstr = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(os.path.getctime(configuration_file)))
                time_mstr = time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(os.path.getmtime(dir_path)))

                benchmark_info.append([id_number, name_str, time_cstr,
                                       time_mstr, comment_str, tags_str])
            except ValueError:
                pass
    # sort using id
    benchmark_info = sorted(benchmark_info, key=operator.itemgetter(0))
    # convert id to string
    for info in benchmark_info:
        info[0] = str(info[0])
    # add header
    benchmark_info = [("id", "name", "started", "last change",
                       "comment", "tags")] + benchmark_info
    if len(benchmark_info) > 1:
        infostr = (jube2.util.text_boxed("Benchmarks found in \"{}\":".
                                         format(path)) + "\n" +
                   jube2.util.text_table(benchmark_info, use_header_line=True))
        print(infostr)
    else:
        print("No Benchmarks found in \"{}\"".format(path))


def print_benchmark_info(benchmark):
    """Print information concerning a single benchmark"""
    infostr = \
        jube2.util.text_boxed("{0} id:{1} tags:{2}\n\n{3}"
                              .format(benchmark.name,
                                      benchmark.id,
                                      jube2.conf.DEFAULT_SEPARATOR.join(
                                          benchmark.tags),
                                      benchmark.comment))
    print(infostr)
    continue_possible = False

    print("  Directory: {}"
          .format(os.path.abspath(benchmark.bench_dir)))

    # Starttime is workpackage.xml creation time
    start_time = \
        time.strftime("%Y-%m-%d %H:%M:%S",
                      time.localtime(os.path.getctime(
                          os.path.join(benchmark.bench_dir,
                                       jube2.conf.CONFIGURATION_FILENAME))))
    print("\n    Started: {}".format(start_time))
    last_change = time.localtime(os.path.getmtime(benchmark.bench_dir))

    # Create step overview
    step_info = [("step name", "depends", "#work", "#done", "last finished")]
    for step_name, workpackages in benchmark.workpackages.items():
        cnt_done = 0
        last_finish = time.localtime(0)
        depends = jube2.conf.DEFAULT_SEPARATOR.join(
            benchmark.steps[step_name].depend)
        for workpackage in workpackages:
            if workpackage.done:
                cnt_done += 1
                last_finish = max(last_finish, time.localtime(
                    os.path.getmtime(os.path.join(
                        workpackage.workpackage_dir,
                        jube2.conf.WORKPACKAGE_DONE_FILENAME))))
                last_change = max(last_change, last_finish)
        if last_finish > time.localtime(0):
            last_finish_str = time.strftime("%Y-%m-%d %H:%M:%S", last_finish)
        else:
            last_finish_str = ""
        continue_possible = continue_possible or \
            (len(workpackages) != cnt_done)

        # Create #workpackages string
        iterations = benchmark.steps[step_name].iterations
        if benchmark.steps[step_name].iterations > 1:
            cnt = "{0}*{1}".format(len(workpackages) // iterations, iterations)
        else:
            cnt = str(len(workpackages))

        step_info.append((step_name, depends, cnt,
                          str(cnt_done), last_finish_str))
    print("Last change: {}"
          .format(time.strftime("%Y-%m-%d %H:%M:%S", last_change)))
    print(
        "\n" + jube2.util.text_table(step_info, use_header_line=True,
                                     indent=1))

    if continue_possible:
        print("\n--- Benchmark not finished! ---")
    else:
        print("\n--- Benchmark finished ---")

    # Create list of used external files
    print("\nUsed files and directories:")
    for fileset in benchmark.filesets.values():
        for file_obj in fileset:
            if not file_obj.is_internal_ref:
                print("  {}".format(os.path.abspath(file_obj.path)))

    print(jube2.util.text_line())


def print_step_info(benchmark, step_name):
    """Print information concerning a single step in a specific benchmark"""
    if step_name not in benchmark.workpackages:
        print("Step \"{0}\" not found in benchmark \"{1}\"."
              .format(step_name, benchmark.name))
        return
    print(jube2.util.text_boxed("{0} Step: {1}".format(benchmark.name,
                                                       step_name)))

    step = benchmark.steps[step_name]

    # Get all possible error filenames
    error_file_names = set()
    for operation in step.operations:
        if operation.stderr_filename is not None:
            error_file_names.add(operation.stderr_filename)
        else:
            error_file_names.add("stderr")

    wp_info = [("id", "started?", "done?", "work_dir")]
    error_dict = dict()
    useable_parameter = None
    for workpackage in benchmark.workpackages[step_name]:

        if useable_parameter is None or step.alt_work_dir is not None:
            # Parameter substitution to use alt_work_dir
            workpackage.parameterset.add_parameterset(
                benchmark.get_jube_parameterset())
            workpackage.parameterset.add_parameterset(
                step.get_jube_parameterset())
            workpackage.parameterset.add_parameterset(
                workpackage.get_jube_parameterset())
            workpackage.parameterset.parameter_substitution(final_sub=True)
            parameter = \
                dict([[par.name, par.value] for par in
                      workpackage.parameterset
                      .constant_parameter_dict.values()])
            # Save available parameter names
            if useable_parameter is None:
                useable_parameter = [name for name in parameter.keys()]
                useable_parameter.sort()

        id_str = str(workpackage.id)
        started_str = str(workpackage.started).lower()
        done_str = str(workpackage.done).lower()
        work_dir = workpackage.work_dir
        if step.alt_work_dir is not None:
            work_dir = jube2.util.substitution(step.alt_work_dir, parameter)

        # Read error-files
        for error_file_name in error_file_names:
            if os.path.exists(os.path.join(work_dir, error_file_name)):
                error_file = open(os.path.join(work_dir, error_file_name), "r")
                error_string = error_file.read().strip()
                if len(error_string) > 0:
                    error_dict[os.path.abspath(os.path.join(
                        work_dir, error_file_name))] = error_string
                error_file.close()

        # Store info data
        wp_info.append(
            (id_str, started_str, done_str, os.path.abspath(work_dir)))

    print("Workpackages:")
    print(jube2.util.text_table(wp_info, use_header_line=True, indent=1,
                                auto_linebreak=False))

    if useable_parameter is not None:
        print("Available parameter:")
        wraps = textwrap.wrap(", ".join(useable_parameter), 80)
        for wrap in wraps:
            print(wrap)
        print("")

    if len(error_dict) > 0:
        print("!!! Errors found !!!:")
    for error_file in error_dict:
        print(">>> {}:".format(error_file))
        print("{}\n".format(error_dict[error_file]))
