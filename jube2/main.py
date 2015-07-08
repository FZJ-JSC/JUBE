# JUBE Benchmarking Environment
# Copyright (C) 2008-2015
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
"""CLI program"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import jube2.jubeio
import jube2.util
import jube2.conf
import jube2.info
import jube2.help
import jube2.jubetojube2
import jube2.log

import sys
import os
import re
import shutil

try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

try:
    import argparse
except ImportError:
    print("argparse module not available; either install it "
          "(https://pypi.python.org/pypi/argparse), or "
          "switch to a Python version that includes it.")
    sys.exit(1)

LOGGER = jube2.log.get_logger(__name__)


def continue_benchmarks(args):
    """Continue benchmarks"""
    found_benchmarks = search_for_benchmarks(args)
    jube2.conf.HIDE_ANIMATIONS = args.hide_animation
    for benchmark_folder in found_benchmarks:
        _continue_benchmark(benchmark_folder, args)


def status(args):
    """Show benchmark status"""
    found_benchmarks = search_for_benchmarks(args)
    for benchmark_folder in found_benchmarks:
        benchmark = _load_existing_benchmark(benchmark_folder,
                                             load_analyse=False)
        jube2.info.print_benchmark_status(benchmark)


def benchmarks_results(args):
    """Show benchmark results"""
    found_benchmarks = search_for_benchmarks(args, load_all=True)
    result_list = list()
    # Start with the newest benchmark to set the newest result configuration
    found_benchmarks.reverse()
    cnt = 0
    for benchmark_folder in found_benchmarks:
        if (args.num is None) or (cnt < args.num):
            result_list = _benchmark_result(benchmark_folder=benchmark_folder,
                                            args=args,
                                            result_list=result_list)
            cnt += 1

    jube2.log.setup_logging("console")

    for result_data in result_list:
        # If there are multiple benchmarks, add benchmark id information
        if len(found_benchmarks) > 1:
            result_data.add_id_information(reverse=args.reverse)
        result_data.create_result()


def analyse_benchmarks(args):
    """Analyse benchmarks"""
    found_benchmarks = search_for_benchmarks(args)
    for benchmark_folder in found_benchmarks:
        _analyse_benchmark(benchmark_folder, args)


def remove_benchmarks(args):
    """Remove benchmarks"""
    found_benchmarks = search_for_benchmarks(args)
    for benchmark_folder in found_benchmarks:
        _remove_benchmark(benchmark_folder, args)


def command_help(args):
    """Show command help"""
    subparser = _get_args_parser()[1]
    if args.command is None:
        subparser["help"].print_help()
    else:
        if args.command in jube2.help.HELP:
            if args.command in subparser:
                subparser[args.command].print_help()
            else:
                print(jube2.help.HELP[args.command])
        else:
            print("no help found for {0}".format(args.command))
            subparser["help"].print_help()


def info(args):
    """Benchmark information"""
    if args.id is None:
        jube2.info.print_benchmarks_info(args.dir)
    else:
        found_benchmarks = search_for_benchmarks(args)
        for benchmark_folder in found_benchmarks:
            benchmark = \
                _load_existing_benchmark(benchmark_folder, load_analyse=False)
            if args.step is None:
                jube2.info.print_benchmark_info(benchmark)
            else:
                for step_name in args.step:
                    jube2.info.print_step_info(
                        benchmark, step_name,
                        parametrization_only=args.parametrization)


def update_check(args):
    """Check if a newer JUBE version is available."""
    try:
        website = urlopen(jube2.conf.UPDATE_VERSION_URL)
        version_str = website.read().decode().strip()
        version_loc = jube2.conf.JUBE_VERSION.split(".")
        version_ext = version_str.split(".")
        newest_version = True
        if len(version_loc) == len(version_ext):
            for i in range(len(version_loc)):
                if int(version_ext[i]) > int(version_loc[i]):
                    newest_version = newest_version and \
                        (int(version_loc[i]) >= int(version_ext[i]))
                if int(version_loc[i]) > int(version_ext[i]):
                    break
            if newest_version:
                LOGGER.info("Newest JUBE version {0} is already "
                            "installed.".format(jube2.conf.JUBE_VERSION))
            else:
                LOGGER.info(("Newer JUBE version {0} is available. "
                             "Currently installed version is {1}.\n"
                             "New version can be "
                             "downloaded here: {2}").format(
                    version_str, jube2.conf.JUBE_VERSION,
                    jube2.conf.UPDATE_URL))
        else:
            raise IOError("Unknown version format at {0}".format(
                jube2.conf.UPDATE_VERSION_URL))
    except IOError as ioe:
        raise IOError("Can not connect to {0}: {1}".format(
            jube2.conf.UPDATE_VERSION_URL, str(ioe)))
    except ValueError as verr:
        raise ValueError("Can not read version string from {0}: {1}".format(
            jube2.conf.UPDATE_VERSION_URL, str(verr)))


def show_log(args):
    """Show logs for benchmarks"""
    found_benchmarks = search_for_benchmarks(args)
    for benchmark_folder in found_benchmarks:
        show_log_single(args, benchmark_folder)


def show_log_single(args, benchmark_folder):
    """Show logs for a single benchmark"""
    # Find available logs
    available_logs = jube2.log.search_for_logs(benchmark_folder)

    # Use all available logs if none is selected ...
    if not args.command:
        matching = available_logs
        not_matching = list()
    # ... otherwise find intersection between available and
    # selected
    else:
        matching, not_matching = jube2.log.matching_logs(
            args.command, available_logs)

    # Output the log file
    for log in matching:
        jube2.log.log_print("BenchmarkID: {0} | Log: {1}".format(
            int(os.path.basename(benchmark_folder)), log))
        jube2.log.safe_output_logfile(log)

    # Inform user if any selected log was not found
    if not_matching:
        jube2.log.log_print("Could not find logs: {0}".format(
            ",".join(not_matching)))


def _load_existing_benchmark(benchmark_folder, restore_workpackages=True,
                             load_analyse=True):
    """Load an existing benchmark, given by directory benchmark_folder."""
    # Read existing benchmark configuration
    parser = jube2.jubeio.XMLParser(os.path.join(
        benchmark_folder, jube2.conf.CONFIGURATION_FILENAME))
    benchmarks = parser.benchmarks_from_xml()[0]
    # Only one single benchmark exist inside benchmarks
    benchmark = list(benchmarks.values())[0]

    # Restore old benchmark id
    benchmark.id = int(os.path.basename(benchmark_folder))

    if restore_workpackages:
        # Read existing workpackage information
        parser = jube2.jubeio.XMLParser(os.path.join(
            benchmark_folder, jube2.conf.WORKPACKAGES_FILENAME))
        workpackages, work_stat = parser.workpackages_from_xml(benchmark)
        benchmark.set_workpackage_information(workpackages, work_stat)

    if load_analyse and os.path.isfile(os.path.join(
            benchmark_folder, jube2.conf.ANALYSE_FILENAME)):
        # Read existing analyse data
        parser = jube2.jubeio.XMLParser(os.path.join(
            benchmark_folder, jube2.conf.ANALYSE_FILENAME))
        analyse_result = parser.analyse_result_from_xml()
        for analyser in benchmark.analyser.values():
            if analyser.name in analyse_result:
                analyser.analyse_result = analyse_result[analyser.name]

    return benchmark


def manipulate_comments(args):
    """Manipulate benchmark comment"""
    found_benchmarks = search_for_benchmarks(args)
    for benchmark_folder in found_benchmarks:
        _manipulate_comment(benchmark_folder, args)


def search_for_benchmarks(args, load_all=False):
    """Search for existing benchmarks"""
    found_benchmarks = list()
    if not os.path.isdir(args.dir):
        raise OSError("Not a directory: \"{0}\"".format(args.dir))
    if (args.id is not None) and ("all" not in args.id):
        for benchmark_id in args.id:
            if benchmark_id == "last":
                benchmark_id = jube2.util.get_current_id(args.dir)
            # Search for existing benchmark
            benchmark_folder = jube2.util.id_dir(args.dir, int(benchmark_id))
            if not os.path.isdir(benchmark_folder):
                raise OSError("Benchmark directory not found: \"{0}\""
                              .format(benchmark_folder))
            if benchmark_folder not in found_benchmarks:
                found_benchmarks.append(benchmark_folder)
    else:
        if load_all or (args.id is not None) and ("all" in args.id):
            # Add all available benchmark folder
            found_benchmarks = [
                os.path.join(args.dir, directory)
                for directory in os.listdir(args.dir)
                if os.path.isdir(os.path.join(args.dir, directory))]
        else:
            # Get highest benchmark id
            benchmark_id = jube2.util.get_current_id(args.dir)
            # Restart existing benchmark
            benchmark_folder = jube2.util.id_dir(args.dir, benchmark_id)
            if os.path.isdir(benchmark_folder):
                found_benchmarks.append(benchmark_folder)
            else:
                raise OSError("No benchmark directory found in \"{0}\""
                              .format(args.dir))
    found_benchmarks = \
        [benchmark_folder for benchmark_folder in found_benchmarks if
         os.path.isfile(os.path.join(benchmark_folder,
                                     jube2.conf.CONFIGURATION_FILENAME))]
    found_benchmarks.sort()
    return found_benchmarks


def _update_include_path(args):
    """Update the global include path information list"""
    jube2.jubeio.INCLUDE_PATH = list()

    # Add commandline include-path
    if args.include_path is not None:
        jube2.jubeio.INCLUDE_PATH = \
            [include_path for include_path in args.include_path
             if include_path != ""]


def run_new_benchmark(args):
    """Start a new benchmark run"""

    jube2.conf.HIDE_ANIMATIONS = args.hide_animation

    id_cnt = 0

    # Update include path
    _update_include_path(args)

    # Extract tags
    tags = args.tag
    if tags is not None:
        tags = set(tags)

    for path in args.files:
        # Read new benchmarks
        parser = jube2.jubeio.XMLParser(path, tags)
        benchmarks, only_bench, not_bench = parser.benchmarks_from_xml()

        # Add new comment
        if args.comment is not None:
            for benchmark in benchmarks.values():
                benchmark.comment = re.sub(r"\s+", " ", args.comment)

        # CLI input overwrite fileinput
        if args.only_bench:
            only_bench = args.only_bench
        if args.not_bench:
            not_bench = args.not_bench

        # No specific -> do all
        if len(only_bench) == 0:
            only_bench = list(benchmarks)

        for bench_name in only_bench:
            if bench_name in not_bench:
                continue
            bench = benchmarks[bench_name]
            # Set user defined id
            if (args.id is not None) and (len(args.id) > id_cnt):
                bench.id = args.id[id_cnt]
                id_cnt += 1
            bench.new_run()
            # Run analyse
            if args.analyse or args.result:
                bench.analyse()

            # Create result data
            if args.result:
                bench.create_result(show=True)

            # Clean up when using debug mode
            if jube2.conf.DEBUG_MODE:
                bench.delete_bench_dir()


def jube2jube2(args):
    """Convert jube XMLs to jube2 XMLs"""
    main_dir = args.input_path
    jube_main_file = args.main_xml_file
    convertit = jube2.jubetojube2.JubeXMLConverter(jube_main_file, main_dir)
    # convertit.convert_platformfile()
    convertit.convert_xml()
    convertit.write_platformfile(os.path.join(main_dir, "platform_jube2.xml"))


def _continue_benchmark(benchmark_folder, args):
    """Continue existing benchmark"""
    benchmark = _load_existing_benchmark(benchmark_folder)

    # Change logfile
    jube2.log.change_logfile_name(os.path.join(
        benchmark_folder, jube2.conf.LOGFILE_CONTINUE_NAME))

    # Run existing benchmark
    benchmark.run()

    # Run analyse
    if args.analyse or args.result:
        benchmark.analyse()

    # Create result data
    if args.result:
        benchmark.create_result(show=True)

    # Clean up when using debug mode
    if jube2.conf.DEBUG_MODE:
        benchmark.reset_all_workpackages()


def _analyse_benchmark(benchmark_folder, args):
    """Analyse existing benchmark"""
    benchmark = _load_existing_benchmark(benchmark_folder, load_analyse=False)

    # Update benchmark data
    _update_analyse_and_result(args, benchmark, benchmark_folder)

    # Change logfile
    jube2.log.change_logfile_name(os.path.join(
        benchmark_folder, jube2.conf.LOGFILE_ANALYSE_NAME))

    LOGGER.info(jube2.util.text_boxed(("Analyse benchmark \"{0}\" id: {1}")
                                      .format(benchmark.name, benchmark.id)))
    benchmark.analyse()
    LOGGER.info(">>> Analyse data storage: {0}".format(os.path.join(
        benchmark_folder, jube2.conf.ANALYSE_FILENAME)))
    LOGGER.info(jube2.util.text_line())


def _benchmark_result(benchmark_folder, args, result_list=None):
    """Show benchmark result"""
    benchmark = _load_existing_benchmark(benchmark_folder)

    if result_list is None:
        result_list = list()

    if (args.tag is not None) and (len(benchmark.tags & set(args.tag)) == 0):
        return result_list

    # Update benchmark data
    _update_analyse_and_result(args, benchmark, benchmark_folder)

    # Run benchmark analyse
    if args.analyse:
        jube2.log.change_logfile_name(os.path.join(
            benchmark_folder, jube2.conf.LOGFILE_ANALYSE_NAME))
        benchmark.analyse(show_info=False)

        # Change logfile
    jube2.log.change_logfile_name(os.path.join(
        benchmark_folder, jube2.conf.LOGFILE_RESULT_NAME))

    # Create benchmark results
    result_list = benchmark.create_result(only=args.only,
                                          data_list=result_list)

    # Reset logging
    jube2.log.change_logfile_name(jube2.conf.DEFAULT_LOGFILE_NAME)

    return result_list


def _update_analyse_and_result(args, benchmark, benchmark_folder):
    """Update analyse and result data in given benchmark by using the
    given update file"""
    if args.update is not None:
        dirname = os.path.dirname(args.update)

        # Update include path
        _update_include_path(args)

        # Extract tags
        tags = args.tag
        if tags is not None:
            tags = set(tags)

        # Read new benchmarks
        parser = jube2.jubeio.XMLParser(args.update, tags)
        benchmarks = parser.benchmarks_from_xml()[0]

        # Update benchmark
        for bench in benchmarks.values():
            if bench.name == benchmark.name:
                benchmark.update_analyse_and_result(bench.patternsets,
                                                    bench.analyser,
                                                    bench.results,
                                                    bench.results_order,
                                                    dirname)
                break


def _remove_benchmark(benchmark_folder, args):
    """Remove existing benchmark"""
    remove = True
    if not args.force:
        try:
            inp = raw_input("Really remove \"{0}\" (y/n):"
                            .format(benchmark_folder))
        except NameError:
            inp = input("Really remove \"{0}\" (y/n):"
                        .format(benchmark_folder))
        remove = inp.startswith("y")
    if remove:
        # Delete benchmark folder
        shutil.rmtree(benchmark_folder, ignore_errors=True)


def _manipulate_comment(benchmark_folder, args):
    """Change or append the comment in given benchmark."""
    benchmark = _load_existing_benchmark(benchmark_folder=benchmark_folder,
                                         restore_workpackages=False,
                                         load_analyse=False)

    # Change benchmark comment
    if args.append:
        comment = benchmark.comment + args.comment
    else:
        comment = args.comment
    benchmark.comment = re.sub(r"\s+", " ", comment)
    benchmark.write_benchmark_configuration(
        os.path.join(benchmark_folder,
                     jube2.conf.CONFIGURATION_FILENAME))


def _get_args_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="show version",
                        action="version",
                        version="JUBE, version {0}".format(
                            jube2.conf.JUBE_VERSION))
    parser.add_argument('--debug', action="store_true",
                        help='use debugging mode')
    parser.add_argument('--devel', action="store_true",
                        help='show development related information')
    subparsers = parser.add_subparsers(dest="subparser", help='subparsers')

    subparser_configuration = dict()

    # run subparser
    subparser_configuration["run"] = {
        "help": "processes benchmark",
        "func": run_new_benchmark,
        "arguments": {
            ("files",):
                {"metavar": "FILE", "nargs": "+", "help": "input file"},
            ("--only-bench",):
                {"nargs": "+", "help": "only run benchmark"},
            ("--not-bench",):
                {"nargs": "+", "help": "do not run benchmark"},
            ("-t", "--tag"):
                {"nargs": "+", "help": "select tags"},
            ("-i", "--id"):
                {"type": int, "help": "use specific benchmark id",
                 "nargs": "+"},
            ("--hide-animation",):
                {"action": "store_true", "help": "hide animations"},
            ("--include-path",):
                {"nargs": "+", "help": "directory containing include files"},
            ("-a", "--analyse"):
                {"action": "store_true", "help": "run analyse"},
            ("-r", "--result"):
                {"action": "store_true", "help": "show results"},
            ("-m", "--comment"):
                {"help": "add comment"}
        }
    }

    # continue subparser
    subparser_configuration["continue"] = {
        "help": "continue benchmark",
        "func": continue_benchmarks,
        "arguments": {
            ("dir",):
                {"metavar": "DIRECTORY", "nargs": "?",
                 "help": "benchmark directory", "default": "."},
            ("-i", "--id"):
                {"help": "use benchmarks given by id",
                 "nargs": "+"},
            ("--hide-animation",):
                {"action": "store_true", "help": "hide animations"},
            ("-a", "--analyse"):
                {"action": "store_true", "help": "run analyse"},
            ("-r", "--result"):
                {"action": "store_true", "help": "show results"}
        }
    }

    # analyse subparser
    subparser_configuration["analyse"] = {
        "help": "analyse benchmark",
        "func": analyse_benchmarks,
        "arguments": {
            ("dir",):
                {"metavar": "DIRECTORY", "nargs": "?",
                 "help": "benchmark directory", "default": "."},
            ("-i", "--id"):
                {"help": "use benchmarks given by id",
                 "nargs": "+"},
            ("-u", "--update"):
                {"metavar": "UPDATE_FILE",
                 "help": "update analyse and result configuration"},
            ("--include-path",):
                {"nargs": "+", "help": "directory containing include files"},
            ("-t", "--tag"):
                {"nargs": "+", "help": "select tags"}
        }
    }

    # result subparser
    subparser_configuration["result"] = {
        "help": "show benchmark results",
        "func": benchmarks_results,
        "arguments": {
            ("dir",):
                {"metavar": "DIRECTORY", "nargs": "?",
                 "help": "benchmark directory", "default": "."},
            ("-i", "--id"):
                {"help": "use benchmarks given by id",
                 "nargs": "+"},
            ("-a", "--analyse"):
                {"action": "store_true",
                 "help": "run analyse before creating result"},
            ("-u", "--update"):
                {"metavar": "UPDATE_FILE",
                 "help": "update analyse and result configuration"},
            ("--include-path",):
                {"nargs": "+", "help": "directory containing include files"},
            ("-t", "--tag"):
                {"nargs": '+', "help": "select tags"},
            ("-o", "--only"):
                {"nargs": "+", "metavar": "RESULT_NAME",
                 "help": "only create results given by specific name"},
            ("-r", "--reverse"):
                {"help": "reverse benchmark output order",
                 "action": "store_true"},
            ("-n", "--num"):
                {"type": int, "help": "show only last N benchmarks"}
        }
    }

    # info subparser
    subparser_configuration["info"] = {
        "help": "benchmark information",
        "func": info,
        "arguments": {
            ('dir',):
                {"metavar": "DIRECTORY", "nargs": "?",
                 "help": "benchmark directory", "default": "."},
            ("-i", "--id"):
                {"help": "use benchmarks given by id",
                 "nargs": "+"},
            ("-s", "--step"):
                {"help": "show information for given step", "nargs": "+"},
            ("-p", "--parametrization"):
                {"help": "display only parametrization of given step " +
                 "using csv format", "action": "store_true"}
        }
    }

    # status subparser
    subparser_configuration["status"] = {
        "help": "show benchmark status",
        "func": status,
        "arguments": {
            ('dir',):
                {"metavar": "DIRECTORY", "nargs": "?",
                 "help": "benchmark directory", "default": "."},
            ("-i", "--id"):
                {"help": "use benchmarks given by id",
                 "nargs": "+"}
        }
    }

    # comment subparser
    subparser_configuration["comment"] = {
        "help": "comment handling",
        "func": manipulate_comments,
        "arguments": {
            ('comment',):
                {"help": "comment"},
            ('dir',):
                {"metavar": "DIRECTORY", "nargs": "?",
                 "help": "benchmark directory", "default": "."},
            ("-i", "--id"):
                {"help": "use benchmarks given by id",
                 "nargs": "+"},
            ("-a", "--append"):
                {"help": "append comment to existing one",
                 "action": 'store_true'}
        }
    }

    # remove subparser
    subparser_configuration["remove"] = {
        "help": "remove benchmark",
        "func": remove_benchmarks,
        "arguments": {
            ('dir',):
                {"metavar": "DIRECTORY", "nargs": "?",
                 "help": "benchmark directory", "default": "."},
            ("-i", "--id"):
                {"help": "use benchmarks given by id",
                 "nargs": "+"},
            ("-f", "--force"):
                {"help": "force removing, never prompt",
                 "action": "store_true"}
        }
    }

    # convert subparser
    subparser_configuration["convert"] = {
        "help": "Convert jube version 1 files to jube version 2 files",
        "func": jube2jube2,
        "arguments": {
            ("-i", "--input_path"):
                {"type": str, "default": "./",
                 "help": "Location of jube XML files"},
            ("main_xml_file",):
                {"type": str, "help": "Main jube XML"}
        }
    }

    # update subparser
    subparser_configuration["update"] = {
        "help": "Check if a newer JUBE version is available",
        "func": update_check
    }

    # log subparser
    subparser_configuration["log"] = {
        "help": "show benchmark logs",
        "func": show_log,
        "arguments": {
            ('dir',):
                {"metavar": "DIRECTORY", "nargs": "?",
                 "help": "benchmark directory", "default": "."},
            ('--command', "-c"):
                {"nargs": "+", "help": "show log for this command"},
            ("-i", "--id"):
                {"help": "use benchmarks given by id",
                 "nargs": "+"}
        }
    }

    # create subparser out of subparser configuration
    subparser = dict()
    for name, subparser_config in subparser_configuration.items():
        subparser[name] = \
            subparsers.add_parser(
                name, help=subparser_config.get("help", ""),
                description=jube2.help.HELP.get(name, ""),
                formatter_class=argparse.RawDescriptionHelpFormatter)
        subparser[name].set_defaults(func=subparser_config["func"])
        if "arguments" in subparser_config:
            for names, arg in subparser_config["arguments"].items():
                subparser[name].add_argument(*names, **arg)

    # help subparser
    subparser["help"] = \
        subparsers.add_parser('help', help='command help',
                              description="available commands or " +
                              "info elements: " +
                              ", ".join(sorted(jube2.help.HELP)))
    subparser["help"].add_argument('command', nargs='?',
                                   help="command or info element")
    subparser["help"].set_defaults(func=command_help)

    return parser, subparser


def main(command=None):
    """Parse the command line and run the requested command."""
    jube2.help.load_help()
    parser = _get_args_parser()[0]
    if command is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(command)

    jube2.conf.DEBUG_MODE = args.debug

    if args.subparser:
        if args.func in [run_new_benchmark, continue_benchmarks,
                         analyse_benchmarks, benchmarks_results]:
            logger_config = "default"
        else:
            logger_config = "console"

        jube2.log.setup_logging(logger_config)

        LOGGER.debug("Using logger_config: '{0}'".format(logger_config))
        LOGGER.debug("Command: '{0}'".format(" ".join(sys.argv)))

        if args.devel:
            args.func(args)
        else:
            try:
                args.func(args)
            except Exception as exeption:
                # Catch all possible Exceptions
                LOGGER.error("\n" + str(exeption))
                jube2.log.reset_logging()
                exit(1)
    else:
        parser.print_usage()
    jube2.log.reset_logging()

if __name__ == "__main__":
    main()
