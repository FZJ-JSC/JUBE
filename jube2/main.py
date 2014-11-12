"""CLI program"""

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

import jube2.jubeio
import jube2.util
import jube2.conf
import jube2.info
import jube2.help
import jube2.jubetojube2
import jube2.log

import argparse
import os
import re
import shutil
import sys

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
        # Store current working dir
        cwd = os.getenv("PWD")
        # Change current working dir to benchmark_folder
        os.chdir(benchmark_folder)
        jube2.info.print_benchmark_status(benchmark)
        # Restore current working dir
        os.chdir(cwd)


def benchmarks_results(args):
    """Show benchmark results"""
    found_benchmarks = search_for_benchmarks(args)
    for benchmark_folder in found_benchmarks:
        _benchmark_result(benchmark_folder, args)


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
            print("no help found for {}".format(args.command))
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
            # Store current working dir
            cwd = os.getenv("PWD")
            # Change current working dir to benchmark_folder
            os.chdir(benchmark_folder)
            if args.step is None:
                jube2.info.print_benchmark_info(benchmark)
            else:
                for step_name in args.step:
                    jube2.info.print_step_info(benchmark, step_name)
            # Restore current working dir
            os.chdir(cwd)


def show_log(args):
    """Show logs for benchmarks"""
    found_benchmarks = search_for_benchmarks(args)
    for benchmark_folder in found_benchmarks:
        show_log_single(args, benchmark_folder)


def show_log_single(args, benchmark_folder):
    """Show logs for a single benchmark"""
    benchmark = \
        _load_existing_benchmark(benchmark_folder, restore_workpackages=False,
                                 load_analyse=False)
    # Store current working dir
    cwd = os.getenv("PWD")
    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)

    # Find available logs
    available_logs = jube2.log.search_for_logs()

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
        jube2.log.log_print("BenchmarkID: {} | Log: {}".format(benchmark.id,
                                                               log))
        jube2.log.safe_output_logfile(log)

    # Inform user if any selected log was not found
    if not_matching:
        jube2.log.log_print("Could not find logs: {}".format(
            ",".join(not_matching)))

    # Restore current working dir
    os.chdir(cwd)


def _load_existing_benchmark(benchmark_folder, restore_workpackages=True,
                             load_analyse=True):
    """Load an existing benchmark, given by directory benchmark_folder."""
    # Store current working dir
    cwd = os.getenv("PWD")

    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)
    # Read existing benchmark configuration
    benchmarks = jube2.jubeio.benchmarks_from_xml(
        jube2.conf.CONFIGURATION_FILENAME)[0]
    # Only one single benchmark exist inside benchmarks
    benchmark = list(benchmarks.values())[0]
    if restore_workpackages:
        # Read existing workpackage information
        workpackages, work_list = \
            jube2.jubeio.workpackages_from_xml(
                jube2.conf.WORKPACKAGES_FILENAME, benchmark)
        benchmark.set_workpackage_information(workpackages, work_list)

    if load_analyse and os.path.isfile(jube2.conf.ANALYSE_FILENAME):
        # Read existing analyse data
        analyse_result = \
            jube2.jubeio.analyse_result_from_xml(jube2.conf.ANALYSE_FILENAME)
        for analyzer in benchmark.analyzer.values():
            if analyzer.name in analyse_result:
                analyzer.analyse_result = analyse_result[analyzer.name]

    # Restore old benchmark id and set cwd
    benchmark.id = int(os.path.basename(benchmark_folder))
    benchmark.org_cwd = cwd
    benchmark.cwd = os.path.join(cwd, benchmark_folder)
    # Restore current working dir
    os.chdir(cwd)
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
        raise OSError("Not a directory: \"{}\"".format(args.dir))
    if args.id is not None:
        for benchmark_id in args.id:
            # Restart existing benchmark
            benchmark_folder = jube2.util.id_dir(args.dir, benchmark_id)
            if not os.path.isdir(benchmark_folder):
                raise OSError("Benchmark directory not found: \"{}\""
                              .format(benchmark_folder))
            found_benchmarks.append(benchmark_folder)
    else:
        # Get highest benchmark id
        benchmark_id = jube2.util.get_current_id(args.dir)
        # Restart existing benchmark
        benchmark_folder = jube2.util.id_dir(args.dir, benchmark_id)
        if os.path.isdir(benchmark_folder):
            found_benchmarks.append(benchmark_folder)
        else:
            raise OSError("No benchmark directory found in \"{}\""
                          .format(args.dir))
    return found_benchmarks


def _update_include_path(args, dirname):
    """Update the global include path information list"""
    jube2.jubeio.INCLUDE_PATH = list()

    # Add environment var include-path
    if "JUBE_INCLUDE_PATH" in os.environ:
        jube2.jubeio.INCLUDE_PATH = \
            [os.path.relpath(include_path, dirname)
             for include_path in
             os.environ["JUBE_INCLUDE_PATH"].split(":")] + \
            jube2.jubeio.INCLUDE_PATH

    # Add commandline include-path
    if args.include_path is not None:
        jube2.jubeio.INCLUDE_PATH = \
            [os.path.relpath(include_path, dirname)
             for include_path in args.include_path] + \
            jube2.jubeio.INCLUDE_PATH


def run_new_benchmark(args):
    """Start a new benchmark run"""

    jube2.conf.HIDE_ANIMATIONS = args.hide_animation

    for path in args.files:
        # Store current working dir
        cwd = os.getenv("PWD")
        dirname = os.path.dirname(path)

        # Update include path
        _update_include_path(args, dirname)

        # Change current working dir to filename dir
        if len(dirname) > 0:
            os.chdir(dirname)

        # Extract tags
        tags = args.tag
        if tags is not None:
            tags = set(tags)

        # Read new benchmarks
        benchmarks, only_bench, not_bench = \
            jube2.jubeio.benchmarks_from_xml(os.path.basename(path), tags)

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
            bench.cwd = os.path.join(cwd, dirname)
            bench.org_cwd = cwd
            bench.new_run()
            # Run analyse
            if args.analyse or args.result:
                bench.analyse()

            # Create result data
            if args.result:
                bench.create_result()

            # Clean up when using debug mode
            if jube2.conf.DEBUG_MODE:
                bench.delete_bench_dir()

        # Restore current working dir
        os.chdir(cwd)


def jube2jube2(args):
    """Convert jube XMLs to jube2 XMLs"""
    main_dir = args.input_path
    jube_main_file = args.main_xml_file
    convertit = jube2.jubetojube2.JubeXMLConverter(jube_main_file, main_dir)
    # convertit.convert_platformfile()
    convertit.convert_xml(jube_main_file)
    convertit.write_platformfile(os.path.join(main_dir, "platform_jube2.xml"))


def _continue_benchmark(benchmark_folder, args):
    """Continue existing benchmark"""
    benchmark = _load_existing_benchmark(benchmark_folder)
    # Store current working dir
    cwd = os.getenv("PWD")

    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)

    # Change logfile
    jube2.log.change_logfile_name(jube2.conf.LOGFILE_CONTINUE_NAME)

    # Run existing benchmark
    benchmark.run()

    # Run analyse
    if args.analyse or args.result:
        benchmark.analyse()

    # Create result data
    if args.result:
        benchmark.create_result()

    # Clean up when using debug mode
    if jube2.conf.DEBUG_MODE:
        benchmark.reset_all_workpackages()
    # Restore current working dir
    os.chdir(cwd)


def _analyse_benchmark(benchmark_folder, args):
    """Analyse existing benchmark"""
    benchmark = _load_existing_benchmark(benchmark_folder, load_analyse=False)

    # Update benchmark data
    _update_analyse_and_result(args, benchmark, benchmark_folder)

    # Store current working dir
    cwd = os.getenv("PWD")

    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)

    # Change logfile
    jube2.log.change_logfile_name(jube2.conf.LOGFILE_ANALYSE_NAME)

    LOGGER.info(jube2.util.text_boxed(("Analyse benchmark \"{0}\" id: {1}")
                                      .format(benchmark.name, benchmark.id)))
    benchmark.analyse()
    LOGGER.info(">>> Analyse data storage: {}".format(os.path.join(
        benchmark_folder, jube2.conf.ANALYSE_FILENAME)))
    LOGGER.info(jube2.util.text_line())
    # Restore current working dir
    os.chdir(cwd)


def _benchmark_result(benchmark_folder, args):
    """Show benchmark result"""
    benchmark = _load_existing_benchmark(benchmark_folder)

    # Update benchmark data
    _update_analyse_and_result(args, benchmark, benchmark_folder)

    # Store current working dir
    cwd = os.getenv("PWD")

    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)

    # Change logfile
    jube2.log.change_logfile_name(jube2.conf.LOGFILE_RESULT_NAME)

    # Run becnhmark analyse
    if args.analyse:
        benchmark.analyse(show_info=False)

    # Create benchmark results
    benchmark.create_result(args.only)

    # Restore current working dir
    os.chdir(cwd)


def _update_analyse_and_result(args, benchmark, benchmark_folder):
    """Update analyse and result data in given benchmark by using the
    given update file"""
    if args.update is not None:
        # Store current working dir
        cwd = os.getenv("PWD")
        dirname = os.path.dirname(args.update)

        # Update include path
        _update_include_path(args, dirname)

        # Change current working dir to filename dir
        if len(dirname) > 0:
            os.chdir(dirname)

        # Extract tags
        tags = args.tag
        if tags is not None:
            tags = set(tags)

        # Read new benchmarks
        benchmarks = \
            jube2.jubeio.benchmarks_from_xml(os.path.basename(args.update),
                                             tags)[0]

        # Update benchmark
        os.chdir(cwd)
        for bench in benchmarks.values():
            if bench.name == benchmark.name:
                # Change current working dir to benchmark_folder
                os.chdir(benchmark_folder)
                benchmark.update_analyse_and_result(bench.patternsets,
                                                    bench.analyzer,
                                                    bench.results,
                                                    os.path.join(cwd, dirname))
                # Restore current working dir
                os.chdir(cwd)
                break


def _remove_benchmark(benchmark_folder, args):
    """Remove existing benchmark"""
    remove = True
    if not args.force:
        try:
            inp = raw_input("Really remove \"{}\" (y/n):"
                            .format(benchmark_folder))
        except NameError:
            inp = input("Really remove \"{}\" (y/n):"
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
                        version="JUBE, version {}".format(
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
                {"type": int, "help": "use benchmarks given by id",
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
                {"type": int, "help": "use benchmarks given by id",
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
                {"type": int, "help": "use benchmarks given by id",
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
                 "help": "only create results given by specific name"}
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
                {"type": int, "help": "use benchmarks given by id",
                 "nargs": "+"},
            ("-s", "--step"):
                {"help": "show information for given step", "nargs": "+"}
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
                {"type": int, "help": "use benchmarks given by id",
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
                {"type": int, "help": "use benchmarks given by id",
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
                {"type": int, "help": "use benchmarks given by id",
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
                {"type": int, "help": "use benchmarks given by id",
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
        if "arguments" not in subparser_config:
            continue
        for names, arg in subparser_config["arguments"].items():
            subparser[name].add_argument(*names, **arg)
        subparser[name].set_defaults(func=subparser_config["func"])

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


def main():
    """Parse the command line and run the requested command."""
    jube2.help.load_help()
    parser = _get_args_parser()[0]
    args = parser.parse_args()

    jube2.util.DEBUG_MODE = args.debug

    if args.subparser:
        if args.func in [run_new_benchmark, continue_benchmarks,
                         analyse_benchmarks, benchmarks_results]:
            logger_config = "default"
        else:
            logger_config = "console"

        jube2.log.setup_logging(logger_config)

        LOGGER.debug("Using logger_config: '{}'".format(logger_config))
        LOGGER.debug("Command: '{}'".format(" ".join(sys.argv)))

        if args.devel:
            args.func(args)
        else:
            try:
                args.func(args)
            except Exception as exeption:
                # Catch all possible Exceptions
                LOGGER.error("\n" + str(exeption))

if __name__ == "__main__":
    main()
