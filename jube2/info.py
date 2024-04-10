## JUBE Benchmarking Environment
# Copyright (C) 2008-2024
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

import jube2.util.util
import jube2.util.output
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
                parser = jube2.jubeio.Parser(configuration_file)
                name_str, comment_str, tags = parser.benchmark_info_from_xml()
                tags_str = jube2.conf.DEFAULT_SEPARATOR.join(tags)

                # Read timestamps from timestamps file
                timestamps = \
                    jube2.util.util.read_timestamps(
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
        infostr = (jube2.util.output.text_boxed("Benchmarks found in \"{0}\":".
                                                format(path)) + "\n" +
                   jube2.util.output.text_table(benchmark_info,
                                                use_header_line=True))
        print(infostr)
    else:
        print("No Benchmarks found in \"{0}\"".format(path))


def print_benchmark_info(benchmark):
    """Print information concerning a single benchmark"""
    infostr = \
        jube2.util.output.text_boxed("{0} id:{1} tags:{2}\n\n{3}"
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
    timestamps = jube2.util.util.read_timestamps(
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
    print(jube2.util.output.text_line("="))

    # Create parameter overview
    if benchmark.parametersets:
        print(jube2.util.output.text_line("="))
        print("\nParametersets info:")
        for parameterset_name, parameterset in benchmark.parametersets.items():
            print("\n   Parameterset name: " + parameterset_name)
            print("   Duplicate: " + parameterset.duplicate)
            parameter_info = [("name", "mode", "type", "seperator", "export", "unit",
                            "update_mode", "duplicate", "value")]
            for parameter in parameterset.all_parameters:
                parameter_info.append((parameter.name, parameter.mode, parameter.parameter_type,
                                    parameter.separator, str(parameter.export), parameter.unit,
                                    parameter.update_mode, parameter.duplicate,
                                    parameter.value))
            print("   Parameter:")
            print("\n" + jube2.util.output.text_table(parameter_info, use_header_line=True,
                                                    indent=2))


    # Create substitute overview
    if benchmark.substitutesets:
        print(jube2.util.output.text_line("="))
        print("\nSubstitutesets info:")
        for substituteset_name, substituteset in benchmark.substitutesets.items():
            print("\n   Substituteset name: " + substituteset_name)
            file_info = [("in", "out", "out_mode")]
            for file in substituteset.files:
                file_info.append((file[1], file[0], file[2]))
            print("   IOFiles:")
            print("\n" + jube2.util.output.text_table(file_info, use_header_line=True,
                                                    indent=2))
            sub_info = [("source", "dest", "mode")]
            for name, sub in substituteset.subs.items():
                sub_info.append((sub.source, sub.dest, sub.mode))
            print("   Subs:")
            print("\n" + jube2.util.output.text_table(sub_info, use_header_line=True,
                                                    indent=2))


    # Create file overview
    if benchmark.filesets:
        print(jube2.util.output.text_line("="))
        print("\nFilesets info:")
        for fileset_name, fileset in benchmark.filesets.items():
            print("\n   Fileset name: " + fileset_name)
            file_info = [("type", "name", "path", "source_dir", "target_dir",
                          "rel_path_ref", "active")]
            for file in fileset:
                name = file._name if file._name else ""
                rel_path_ref = "internal" if file._is_internal_ref else "external"
                file_info.append((file.file_type, name, file.path, file.source_dir,
                                  file.target_dir, rel_path_ref, str(file.active)))
            print("   Files:")
            print("\n" + jube2.util.output.text_table(file_info, use_header_line=True,
                                                    indent=2))

    # Create pattern overview
    if benchmark.patternsets:
        print(jube2.util.output.text_line("="))
        print("\nPatternsets info:")
        for patternset_name, patternset in benchmark.patternsets.items():
            print("\n   Patternset name: " + patternset_name)
            pattern_info = [("name", "value", "default", "unit", "mode", "type", "dotall")]
            for pattern in patternset.pattern_storage:
                default = pattern.default_value if pattern.default_value else ""
                pattern_info.append((pattern.name, pattern.value, default, pattern.unit,
                                     pattern.mode, pattern.parameter_type, str(pattern.dotall)))
            for pattern in patternset.derived_pattern_storage:
                default = pattern.default_value if pattern.default_value else ""
                pattern_info.append((pattern.name, pattern.value, default, pattern.unit,
                                     pattern.mode, pattern.parameter_type, str(pattern.dotall)))
            print("   Pattern:")
            print("\n" + jube2.util.output.text_table(pattern_info, use_header_line=True,
                                                    indent=2))

    # Create step overview
    if benchmark.steps:
        status_info = [("step_name", "#work", "#error", "#done", "last finished")]
        print(jube2.util.output.text_line("="))
        print("\nSteps info:")
        for step_name, workpackages in benchmark.workpackages.items():
            print("\n   Step name: " + step_name)
            step_info = [("depends", "work_dir", "suffix", "shared", "active", "export",
                        "max_async", "iterations", "cycles", "procs", "do_log_file", )]
            step = benchmark.steps[step_name]
            # Get used sets and print out
            used_paramsets = step.get_used_sets(benchmark.parametersets)
            if used_paramsets:
                print("   Used Parametersets: " + ", ".join(used_paramsets))
            used_patternsets = step.get_used_sets(benchmark.patternsets)
            if used_patternsets:
                print("   Used Patternsets: " + ", ".join(used_patternsets))
            used_filesets = step.get_used_sets(benchmark.filesets)
            if used_filesets:
                print("   Used Filesets: " + ", ".join(used_filesets))
            used_substitutesets = step.get_used_sets(benchmark.substitutesets)
            if used_substitutesets:
                print("   Used Substitutesets: " + ", ".join(used_substitutesets))
            # Get attributes and print out
            depends = jube2.conf.DEFAULT_SEPARATOR.join(step.depend)
            iterations = step.iterations
            work_dir = step.work_dir if step.work_dir else ""
            shared = step.shared_link_name if step.shared_link_name else ""
            do_log_file = step.do_log_file if step.do_log_file else ""
            step_info.append((depends, work_dir, step.suffix, shared, step.active,
                            str(step.export), step.max_wps, str(iterations),
                            str(step.cycles), str(step.procs), do_log_file))

            print(
                "\n" + jube2.util.output.text_table(step_info, use_header_line=True,
                                                    indent=2))

            # Get operation attributes and print out
            print("   Operations:")
            operation_info = [("do", "stdout", "stderr", "active", "done_file",
                            "error_file", "break_file", "shared", "work_dir")]
            for operation in step.operations:
                stdout = operation.stdout_filename if operation.stdout_filename else ""
                stderr = operation.stderr_filename if operation.stderr_filename else ""
                async_file = operation.async_filename if operation.async_filename else ""
                error = operation.error_filename if operation.error_filename else ""
                break_file = operation.break_filename if operation.break_filename else ""
                work_dir = operation.work_dir if operation.work_dir else ""
                operation_info.append((operation.do, stdout, stderr, operation.active_string,
                                    async_file, error, break_file, str(operation.shared),
                                    work_dir))
            print(
                "\n" + jube2.util.output.text_table(operation_info, use_header_line=True,
                                                    indent=2))

            # Get status and print out
            cnt_done = 0
            cnt_error = 0
            last_finish = time.localtime(0)
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
            if iterations > 1:
                cnt = "{0}*{1}".format(len(workpackages) // iterations, iterations)
            else:
                cnt = str(len(workpackages))

            status_info.append((step_name, cnt, str(cnt_error), str(cnt_done),
                                last_finish_str))

    # Create analyse overview
    if benchmark.analyser:
        print(jube2.util.output.text_line("="))
        print("\nAnalyser info:")
        for analyser_name, analyser in benchmark.analyser.items():
            print("\n   Analyser name: " + analyser_name)
            print("   Reduce: " + str(analyser.reduce))
            print("   Used Patternsets: " + ", ".join(analyser.use))
            for step_name, analyse in analyser.analyser.items():
                print("   Analyse Files for Step " + step_name + ":")
                analyse_info = [("path", "use")]
                for file in analyse:
                    analyse_info.append((file.path, ", ".join(file.use)))
                print("\n" + jube2.util.output.text_table(analyse_info, use_header_line=True,
                                                        indent=3))

    # Create Result overview
    if benchmark.results:
        print(jube2.util.output.text_line("="))
        print("\nResult info:")
        for result_name, result in benchmark.results.items():
            print("\n   Result name: " + result_name)
            print("   Used Analyser: " + ", ".join(result.use))
            result_type = result.result_type
            if result_type == "Table":
                table_info = [("name", "style", "sort", "seperator", "transpose", "filter")]
                column_info = [("column", "colw", "format", "title")]
                res_filter = result.res_filter if result.res_filter else ""
                table_info.append((result.name, result.style, ", ".join(result.sort),
                                result.separator, str(result.transpose), res_filter))
                print("   Table Info:")
                print("\n" + jube2.util.output.text_table(table_info, use_header_line=True,
                                                        indent=3))
                for column in result._keys:
                    colw = column.colw if column.colw else ""
                    col_format = column.format if column.format else ""
                    title = column.title if column.title else ""
                    column_info.append((column.name, colw, col_format, title))
                print("   Column Info:")
                print("\n" + jube2.util.output.text_table(column_info, use_header_line=True,
                                                        indent=3))
            elif result_type == "Database":
                database_info = [("name", "primekeys", "file", "filter")]
                key_info = [("key", "title")]
                res_filter = result.res_filter if result.res_filter else ""
                database_info.append((result.name, ", ".join(result.primekeys), result.file, res_filter))

                print("   Database Info:")
                print("\n" + jube2.util.output.text_table(database_info, use_header_line=True,
                                                        indent=3))
                for key in result._keys:
                    title = key.title if key.title else ""
                    key_info.append((key.name, title))
                print("   Key Info:")
                print("\n" + jube2.util.output.text_table(key_info, use_header_line=True,
                                                        indent=3))
            elif result_type == "SysloggedResult":
                syslog_info = [("name", "address", "host", "port", "sort", "format", "filter")]
                key_info = [("key", "format", "title")]
                address = result.address if result.address else ""
                host = result.host if result.host else ""
                port = result.port if result.port else ""
                res_filter = result.res_filter if result.res_filter else ""
                syslog_info.append((result.name, address, host, port, ", ".join(result.sort),
                                    result.sys_format, res_filter))
                print("   Syslog Info:")
                print("\n" + jube2.util.output.text_table(syslog_info, use_header_line=True,
                                                        indent=3))
                for key in result._keys:
                    key_format = key.format if key.format else ""
                    title = key.title if key.title else ""
                    key_info.append((key.name, key_format, title))
                print("   Key Info:")
                print("\n" + jube2.util.output.text_table(key_info, use_header_line=True,
                                                        indent=3))

    print(jube2.util.output.text_line("="))
    print(jube2.util.output.text_line("="))

    print("\nSteps status:")
    print("\n" + jube2.util.output.text_table(status_info, use_header_line=True,
                                                indent=1))

    if continue_possible:
        print("\n--- Benchmark not finished! ---\n")
    else:
        print("\n--- Benchmark finished ---\n")

    print(jube2.util.output.text_line())


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
        print(jube2.util.output.text_boxed(
            "{0} Step: {1}".format(benchmark.name, step_name)))

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
            work_dir = jube2.util.util.substitution(step.alt_work_dir,
                                                    parameter)

        # collect parameterization
        parameter_list.append(dict())
        parameter_list[-1]["id"] = str(workpackage.id)
        for parameter in workpackage.parameterset:
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
        print(jube2.util.output.text_table(wp_info, use_header_line=True,
                                           indent=1, auto_linebreak=False))

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
            print("")
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
        print(jube2.util.output.text_table(
            table_data, use_header_line=True, indent=1, align_right=True,
            auto_linebreak=False,
            style="csv" if parametrization_only_csv else "pretty",
            separator=(parametrization_only_csv if (parametrization_only_csv)
                       else None)))

    if not parametrization_only:
        if len(error_dict) > 0:
            print("!!! Errors found !!!:")
        for error_file in error_dict:
            print(">>> {0}:".format(error_file))
            try:
                print("{0}\n".format(error_dict[error_file]))
            except UnicodeDecodeError:
                print("\n")


def print_workpackage_info(benchmark, workpackage):
    """Print information concerning a single workpackage in a specific benchmark"""
    print(jube2.util.output.text_boxed(
            "{0} Workpackage with ID {1}".format(benchmark.name, workpackage.id)))
    print("Step: {}".format(workpackage.step.name))
    print("")

    # Get and print workpackage status
    if workpackage.error:
        status = "ERROR"
    elif not workpackage.done:
        status = "RUNNING"
    else:
        status = "DONE"
    print("Status: {}".format(status))
    print("")
    print("Iteration {}".format(workpackage.iteration))
    print("Cycle {}".format(workpackage.cycle))
    print("")

    # Print parents id
    if workpackage.parents:
        parent_str = "Workpackage Parents by ID: "
        for parent in workpackage.parents:
            parent_str += "{}".format(parent.id)
        print(parent_str)

    # Print sibling id
    if workpackage.iteration_siblings:
        sibling_str = "Iteration Sibling by ID: "
        for sibling in workpackage.iteration_siblings:
            sibling_str += "{}".format(sibling.id)
        print(sibling_str)
    print("")

    # Print parameterization
    print("Parameterization:")
    for parameter in workpackage.parameterset:
        if parameter.name != "id":
            print("  {0}: {1}".format(parameter.name, parameter.value))
    print("")

    # Print environments
    if workpackage.env:
        env_str = ""
        for env_name, value in workpackage.env.items():
            if (env_name not in ["PWD", "OLDPWD", "_"]) and \
               (env_name not in os.environ or os.environ[env_name] != value):
                env_str += "  {0}: {1}\n".format(env_name, value)
        if env_str:
            print("Environment:")
            print(env_str)
            print("")
    if os.environ:
        env_str = ""
        for env_name in os.environ:
            if (env_name not in ["PWD", "OLDPWD", "_"]) and \
               (env_name not in workpackage.env):
                env_str += "  {0}\n".format(env_name)
        if env_str:
            print("Environment:")
            print(env_str)
            print("")


def print_benchmark_status(benchmark):
    """Print overall workpackage status in the following order
        RUNNING: At least one WP is still active
        ERROR: At least one WP raised an errror
        FINISHED: All WPs are finalized and no error was raised
    """
    error = False
    running = False
    for step_name in benchmark.workpackages:
        for workpackage in benchmark.workpackages[step_name]:
            running = \
                (not workpackage.done and not workpackage.error) or running
            error = workpackage.error or error
    if running:
        print("RUNNING")
    elif error:
        print("ERROR")
    else:
        print("FINISHED")


def print_tag_documentation(benchmark):
    """Print configuration information concerning a specific benchmark"""
    infostr = \
        jube2.util.output.text_boxed("{0} id:{1} tags:{2}\n\n{3}"
                                     .format(benchmark.name,
                                             benchmark.id,
                                             jube2.conf.DEFAULT_SEPARATOR.join(
                                                 benchmark.tags),
                                             benchmark.comment))
    print(infostr)

    print("  Directory: {0}"
          .format(os.path.abspath(benchmark.bench_dir)))

    tag_docu = [("tag name", "description")]
    for name, doku in benchmark.tag_docu.items():
        tag_docu.append((name, doku))

    print("\n" + jube2.util.output.text_table(tag_docu, use_header_line=True,
                                              indent=1))

    print(jube2.util.output.text_line())
