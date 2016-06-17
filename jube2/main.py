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
from distutils.version import StrictVersion

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
        benchmark = _load_existing_benchmark(args, benchmark_folder,
                                             load_analyse=False)
        if benchmark is None:
            return
        jube2.info.print_benchmark_status(benchmark)


def benchmarks_results(args):
    """Show benchmark results"""
    found_benchmarks = search_for_benchmarks(args)
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

    for result_data in result_list:
        result_data.create_result(reverse=args.reverse)


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
                _load_existing_benchmark(args, benchmark_folder,
                                         load_analyse=False)
            if benchmark is None:
                continue
            if args.step is None:
                jube2.info.print_benchmark_info(benchmark)
            else:
                for step_name in args.step:
                    jube2.info.print_step_info(
                        benchmark, step_name,
                        parametrization_only=args.parametrization,
                        parametrization_only_csv=args.csv_parametrization)


def update_check(args):
    """Check if a newer JUBE version is available."""
    try:
        website = urlopen(jube2.conf.UPDATE_VERSION_URL)
        version = website.read().decode().strip()
        if StrictVersion(jube2.conf.JUBE_VERSION) >= StrictVersion(version):
            LOGGER.info("Newest JUBE version {0} is already "
                        "installed.".format(jube2.conf.JUBE_VERSION))
        else:
            LOGGER.info(("Newer JUBE version {0} is available. "
                         "Currently installed version is {1}.\n"
                         "New version can be "
                         "downloaded here: {2}").format(
                version, jube2.conf.JUBE_VERSION,
                jube2.conf.UPDATE_URL))
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


def _load_existing_benchmark(args, benchmark_folder, restore_workpackages=True,
                             load_analyse=True):
    """Load an existing benchmark, given by directory benchmark_folder."""

    jube2.log.change_logfile_name(os.path.join(
        benchmark_folder, jube2.conf.LOGFILE_PARSE_NAME))

    # Read existing benchmark configuration
    try:
        parser = jube2.jubeio.XMLParser(os.path.join(
            benchmark_folder, jube2.conf.CONFIGURATION_FILENAME),
            force=args.force)
        benchmarks = parser.benchmarks_from_xml()[0]
    except IOError as exeption:
        LOGGER.warning(str(exeption))
        return None

    # benchmarks can be None if version conflict was blocked
    if benchmarks is not None:
        # Only one single benchmark exist inside benchmarks
        benchmark = list(benchmarks.values())[0]
    else:
        return None

    # Restore old benchmark id
    benchmark.id = int(os.path.basename(benchmark_folder))

    if restore_workpackages:
        # Read existing workpackage information
        try:
            parser = jube2.jubeio.XMLParser(os.path.join(
                benchmark_folder, jube2.conf.WORKPACKAGES_FILENAME),
                force=args.force)
            workpackages, work_stat = parser.workpackages_from_xml(benchmark)
        except IOError as exeption:
            LOGGER.warning(str(exeption))
            return None
        benchmark.set_workpackage_information(workpackages, work_stat)

    if load_analyse and os.path.isfile(os.path.join(
            benchmark_folder, jube2.conf.ANALYSE_FILENAME)):
        # Read existing analyse data
        parser = jube2.jubeio.XMLParser(os.path.join(
            benchmark_folder, jube2.conf.ANALYSE_FILENAME),
            force=args.force)
        analyse_result = parser.analyse_result_from_xml()
        for analyser in benchmark.analyser.values():
            if analyser.name in analyse_result:
                analyser.analyse_result = analyse_result[analyser.name]

    jube2.log.only_console_log()

    return benchmark


def manipulate_comments(args):
    """Manipulate benchmark comment"""
    found_benchmarks = search_for_benchmarks(args)
    for benchmark_folder in found_benchmarks:
        _manipulate_comment(benchmark_folder, args)


def search_for_benchmarks(args):
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
            if not os.path.isfile(os.path.join(
                    benchmark_folder, jube2.conf.CONFIGURATION_FILENAME)):
                LOGGER.warning(("Configuration file \"{0}\" not found in " +
                                "\"{1}\" or directory not readable.")
                               .format(jube2.conf.CONFIGURATION_FILENAME,
                                       benchmark_folder))
            if benchmark_folder not in found_benchmarks:
                found_benchmarks.append(benchmark_folder)
    else:
        if (args.id is not None) and ("all" in args.id):
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


def run_new_benchmark(args):
    """Start a new benchmark run"""

    jube2.conf.HIDE_ANIMATIONS = args.hide_animation

    id_cnt = 0

    # Extract tags
    tags = args.tag
    if tags is not None:
        tags = set(tags)

    for path in args.files:
        # Setup Logging
        jube2.log.change_logfile_name(
            filename=os.path.join(os.path.dirname(path),
                                  jube2.conf.DEFAULT_LOGFILE_NAME))
        # Read new benchmarks
        if args.include_path is not None:
            include_pathes = [include_path for include_path in
                              args.include_path if include_path != ""]
        else:
            include_pathes = None
        parser = jube2.jubeio.XMLParser(path, tags, include_pathes, args.force)
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
                jube2.log.change_logfile_name(os.path.join(
                    bench.bench_dir, jube2.conf.LOGFILE_ANALYSE_NAME))
                bench.analyse()

            # Create result data
            if args.result:
                jube2.log.change_logfile_name(os.path.join(
                    bench.bench_dir, jube2.conf.LOGFILE_RESULT_NAME))
                bench.create_result(show=True)

            # Clean up when using debug mode
            if jube2.conf.DEBUG_MODE:
                bench.delete_bench_dir()

        # Reset logging
        jube2.log.only_console_log()


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
    benchmark = _load_existing_benchmark(args, benchmark_folder)

    if benchmark is None:
        return

    # Change logfile
    jube2.log.change_logfile_name(os.path.join(
        benchmark_folder, jube2.conf.LOGFILE_CONTINUE_NAME))

    # Run existing benchmark
    benchmark.run()

    # Run analyse
    if args.analyse or args.result:
        jube2.log.change_logfile_name(os.path.join(
            benchmark_folder, jube2.conf.LOGFILE_ANALYSE_NAME))
        benchmark.analyse()

    # Create result data
    if args.result:
        jube2.log.change_logfile_name(os.path.join(
            benchmark_folder, jube2.conf.LOGFILE_RESULT_NAME))
        benchmark.create_result(show=True)

    # Clean up when using debug mode
    if jube2.conf.DEBUG_MODE:
        benchmark.reset_all_workpackages()

    # Reset logging
    jube2.log.only_console_log()


def _analyse_benchmark(benchmark_folder, args):
    """Analyse existing benchmark"""
    benchmark = _load_existing_benchmark(args, benchmark_folder,
                                         load_analyse=False)
    if benchmark is None:
        return

    # Update benchmark data
    _update_analyse_and_result(args, benchmark, benchmark_folder)

    # Change logfile
    jube2.log.change_logfile_name(os.path.join(
        benchmark_folder, jube2.conf.LOGFILE_ANALYSE_NAME))

    LOGGER.info(jube2.util.text_boxed(("Analyse benchmark \"{0}\" id: {1}")
                                      .format(benchmark.name, benchmark.id)))
    benchmark.analyse()
    if os.path.isfile(
            os.path.join(benchmark_folder, jube2.conf.ANALYSE_FILENAME)):
        LOGGER.info(">>> Analyse data storage: {0}".format(os.path.join(
            benchmark_folder, jube2.conf.ANALYSE_FILENAME)))
    else:
        LOGGER.info(">>> Analyse data storage \"{0}\" not created!".format(
            os.path.join(benchmark_folder, jube2.conf.ANALYSE_FILENAME)))
    LOGGER.info(jube2.util.text_line())

    # Reset logging
    jube2.log.only_console_log()


def _benchmark_result(benchmark_folder, args, result_list=None):
    """Show benchmark result"""
    benchmark = _load_existing_benchmark(args, benchmark_folder)
    if result_list is None:
        result_list = list()

    if benchmark is None:
        return result_list

    if (args.update is None) and (args.tag is not None) and \
            (len(benchmark.tags & set(args.tag)) == 0):
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
    jube2.log.only_console_log()

    return result_list


def _update_analyse_and_result(args, benchmark, benchmark_folder):
    """Update analyse and result data in given benchmark by using the
    given update file"""
    if args.update is not None:
        dirname = os.path.dirname(args.update)

        # Extract tags
        tags = args.tag
        if tags is not None:
            tags = set(tags)

        # Read new benchmarks
        if args.include_path is not None:
            include_pathes = [include_path for include_path in
                              args.include_path if include_path != ""]
        else:
            include_pathes = None
        parser = jube2.jubeio.XMLParser(args.update, tags, include_pathes,
                                        args.force)
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
    benchmark = _load_existing_benchmark(args,
                                         benchmark_folder=benchmark_folder,
                                         restore_workpackages=False,
                                         load_analyse=False)
    if benchmark is None:
        return

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
    parser.add_argument("-V", "--version", help="show version",
                        action="version",
                        version="JUBE, version {0}".format(
                            jube2.conf.JUBE_VERSION))
    parser.add_argument("-v", "--verbose",
                        help="enable verbose console output (use -vv to " +
                             "show stdout during execution and -vvv to " +
                             "show log and stdout)",
                        action="count", default=0)
    parser.add_argument("--debug", action="store_true",
                        help='use debugging mode')
    parser.add_argument("--force", action="store_true",
                        help='skip version check')
    parser.add_argument("--devel", action="store_true",
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
                {"help": "display only parametrization of given step",
                 "action": "store_true"},
            ("-c", "--csv-parametrization"):
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

    # create help key word overview
    help_keys = sorted(jube2.help.HELP)
    max_word_length = max(map(len, help_keys)) + 4
    # calculate max number of keyword columns
    max_columns = jube2.conf.DEFAULT_WIDTH // max_word_length
    # fill keyword list to match number of columns
    help_keys += [""] * (len(help_keys) % max_columns)
    help_keys = list(zip(*[iter(help_keys)] * max_columns))
    # create overview
    help_overview = jube2.util.text_table(help_keys, separator="   ",
                                          align_right=False)

    # help subparser
    subparser["help"] = \
        subparsers.add_parser(
            'help', help='command help',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="available commands or info elements: \n" +
            help_overview)
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
    jube2.conf.VERBOSE_LEVEL = args.verbose

    if jube2.conf.VERBOSE_LEVEL > 0:
        args.hide_animation = True

    # Set new umask if JUBE_GROUP_NAME is used
    current_mask = os.umask(0)
    if (jube2.util.check_and_get_group_id() is not None) and \
            (current_mask > 2):
        current_mask = 2
    os.umask(current_mask)

    if args.subparser:
        jube2.log.setup_logging(mode="console",
                                verbose=(jube2.conf.VERBOSE_LEVEL == 1) or
                                        (jube2.conf.VERBOSE_LEVEL == 3))
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
