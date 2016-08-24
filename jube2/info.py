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
"""Gives benchmark related info"""

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
        raise OSError("Not a directory: \"{0}\"".format(path))
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
                parser = jube2.jubeio.XMLParser(configuration_file)
                name_str, comment_str, tags = parser.benchmark_info_from_xml()
                tags_str = jube2.conf.DEFAULT_SEPARATOR.join(tags)

                # Read timestamps from timestamps file
                timestamps = \
                    jube2.util.read_timestamps(
                        os.path.join(dir_path, jube2.conf.TIMESTAMPS_INFO))
                if "start" in timestamps:
                    time_start = timestamps["start"]
                else:
                    time_start = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(os.path.getctime(configuration_file)))
                if "change" in timestamps:
                    time_change = timestamps["change"]
                else:
                    time_change = time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(os.path.getmtime(dir_path)))

                benchmark_info.append([id_number, name_str, time_start,
                                       time_change, comment_str, tags_str])
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
        infostr = (jube2.util.text_boxed("Benchmarks found in \"{0}\":".
                                         format(path)) + "\n" +
                   jube2.util.text_table(benchmark_info, use_header_line=True))
        print(infostr)
    else:
        print("No Benchmarks found in \"{0}\"".format(path))


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

    print("  Directory: {0}"
          .format(os.path.abspath(benchmark.bench_dir)))

    # Read timestamps from timestamps file
    timestamps = jube2.util.read_timestamps(
        os.path.join(benchmark.bench_dir, jube2.conf.TIMESTAMPS_INFO))

    if "start" in timestamps:
        time_start = timestamps["start"]
    else:
        # Starttime is workpackage.xml creation time
        time_start = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(os.path.getctime(os.path.join(
                benchmark.bench_dir, jube2.conf.CONFIGURATION_FILENAME))))
    if "change" in timestamps:
        time_change = timestamps["change"]
    else:
        time_change = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(os.path.getmtime(benchmark.bench_dir)))

    print("\n    Started: {0}".format(time_start))
    print("Last change: {0}".format(time_change))

    # Create step overview
    step_info = [("step name", "depends", "#work", "#error", "#done",
                  "last finished")]
    for step_name, workpackages in benchmark.workpackages.items():
        cnt_done = 0
        cnt_error = 0
        last_finish = time.localtime(0)
        depends = jube2.conf.DEFAULT_SEPARATOR.join(
            benchmark.steps[step_name].depend)
        for workpackage in workpackages:
            if workpackage.done:
                cnt_done += 1

                # Read timestamp from done_file if it is available otherwise
                # use mtime
                done_file = os.path.join(workpackage.workpackage_dir,
                                         jube2.conf.WORKPACKAGE_DONE_FILENAME)
                done_file_f = open(done_file, "r")
                done_str = done_file_f.read().strip()
                done_file_f.close()
                try:
                    done_time = time.strptime(done_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    done_time = time.localtime(os.path.getmtime(done_file))
                last_finish = max(last_finish, done_time)
            if workpackage.error:
                cnt_error += 1

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

        step_info.append((step_name, depends, cnt, str(cnt_error),
                          str(cnt_done), last_finish_str))

    print(
        "\n" + jube2.util.text_table(step_info, use_header_line=True,
                                     indent=1))

    if continue_possible:
        print("\n--- Benchmark not finished! ---\n")
    else:
        print("\n--- Benchmark finished ---\n")

    print(jube2.util.text_line())


def print_step_info(benchmark, step_name, parametrization_only=False,
                    parametrization_only_csv=False):
    """Print information concerning a single step in a specific benchmark"""
    if step_name not in benchmark.workpackages:
        print("Step \"{0}\" not found in benchmark \"{1}\"."
              .format(step_name, benchmark.name))
        return

    if parametrization_only_csv:
        parametrization_only = True

    if not parametrization_only:
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

    wp_info = [("id", "started?", "error?", "done?", "work_dir")]
    error_dict = dict()
    parameter_list = list()
    useable_parameter = None
    for workpackage in benchmark.workpackages[step_name]:

        # Parameter substitution to use alt_work_dir
        workpackage.add_jube_parameter(workpackage.parameterset)
        parameter = \
            dict([[par.name, par.value] for par in
                  workpackage.parameterset.constant_parameter_dict.values()])

        # Save available parameter names
        if useable_parameter is None:
            useable_parameter = [name for name in parameter.keys()]
            useable_parameter.sort()

        id_str = str(workpackage.id)
        started_str = str(workpackage.started).lower()
        error_str = str(workpackage.error).lower()
        done_str = str(workpackage.done).lower()
        work_dir = workpackage.work_dir
        if step.alt_work_dir is not None:
            work_dir = jube2.util.substitution(step.alt_work_dir, parameter)

        # collect parameterization
        parameter_list.append(dict())
        parameter_list[-1]["id"] = str(workpackage.id)
        for parameter in workpackage.history:
            parameter_list[-1][parameter.name] = parameter.value

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
            (id_str, started_str, error_str, done_str,
             os.path.abspath(work_dir)))

    if not parametrization_only:
        print("Workpackages:")
        print(jube2.util.text_table(wp_info, use_header_line=True, indent=1,
                                    auto_linebreak=False))

    if (useable_parameter is not None) and (not parametrization_only):
        print("Available parameter:")
        wraps = textwrap.wrap(", ".join(useable_parameter), 80)
        for wrap in wraps:
            print(wrap)
        print("")

    if not parametrization_only:
        print("Parameterization:")
        for parameter_dict in parameter_list:
            print(" ID: {0}".format(parameter_dict["id"]))
            for name, value in parameter_dict.items():
                if name != "id":
                    print("  {0}: {1}".format(name, value))
            print()
    else:
        # Create parameterization table
        table_data = list()
        table_data.append(list())
        table_data[0].append("id")
        if len(parameter_list) > 0:
            for name in parameter_list[0]:
                if name != "id":
                    table_data[0].append(name)
            for parameter_dict in parameter_list:
                table_data.append(list())
                for name in table_data[0]:
                    table_data[-1].append(parameter_dict[name])
        print(jube2.util.text_table(table_data, use_header_line=True,
                                    indent=1, align_right=True,
                                    auto_linebreak=False,
                                    pretty=not parametrization_only_csv))

    if not parametrization_only:
        if len(error_dict) > 0:
            print("!!! Errors found !!!:")
        for error_file in error_dict:
            print(">>> {0}:".format(error_file))
            try:
                print("{0}\n".format(error_dict[error_file]))
            except UnicodeDecodeError:
                print("\n")


def print_benchmark_status(benchmark):
    """Print FINISHED or "RUNNING" dependign on the workpackage status"""
    all_done = True
    for step_name in benchmark.workpackages:
        for workpackage in benchmark.workpackages[step_name]:
            all_done = workpackage.done and all_done
    if all_done:
        print("FINISHED")
    else:
        print("RUNNING")
