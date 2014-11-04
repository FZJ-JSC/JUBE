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
import jube2.info
import jube2.help
import jube2.jubetojube2
import argparse
import os
import re
import shutil
import logging
import sys

logger = logging.getLogger(__name__)


def continue_benchmarks(args):
    """Continue benchmarks"""
    found_benchmarks = search_for_benchmarks(args)
    jube2.util.HIDE_ANIMATIONS = args.hide_animation
    for benchmark_folder in found_benchmarks:
        _continue_benchmark(benchmark_folder, args)


def benchmarks_results(args):
    """Continue benchmarks"""
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


def _load_existing_benchmark(benchmark_folder, restore_workpackages=True,
                             load_analyse=True):
    """Load an existing benchmark, given by directory benchmark_folder."""
    # Store current working dir
    cwd = os.getenv("PWD")

    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)
    # Read existing benchmark configuration
    benchmarks = jube2.jubeio.benchmarks_from_xml(
        jube2.util.CONFIGURATION_FILENAME)[0]
    # Only one single benchmark exist inside benchmarks
    benchmark = list(benchmarks.values())[0]
    if restore_workpackages:
        # Read existing workpackage information
        workpackages, work_list = \
            jube2.jubeio.workpackages_from_xml(
                jube2.util.WORKPACKAGES_FILENAME, benchmark)
        benchmark.set_workpackage_information(workpackages, work_list)

    if load_analyse and os.path.isfile(jube2.util.ANALYSE_FILENAME):
        # Read existing analyse data
        analyse_result = \
            jube2.jubeio.analyse_result_from_xml(jube2.util.ANALYSE_FILENAME)
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

    jube2.util.HIDE_ANIMATIONS = args.hide_animation

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
            if jube2.util.DEBUG_MODE:
                bench.delete_bench_dir()

        # Restore current working dir
        os.chdir(cwd)


def jube2jube2(args):
    """Convert jube XMLs to jube2 XMLs"""
    main_dir = args.input_path
    jube_main_file = args.main_xml_file
    convertit = jube2.jubetojube2.JubeXMLConverter(jube_main_file, main_dir)
    convertit.convert_platformfile()
    convertit.convert_xml(jube_main_file)
    convertit.write_platformfile(main_dir + "platform_jube2.xml")


def _continue_benchmark(benchmark_folder, args):
    """Continue existing benchmark"""
    benchmark = _load_existing_benchmark(benchmark_folder)
    # Store current working dir
    cwd = os.getenv("PWD")
    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)

    # Change logfile
    logfile = "continue.log"
    jube2.util.setup_logging(filename=logfile)

    # Run existing benchmark
    benchmark.run()

    # Run analyse
    if args.analyse or args.result:
        benchmark.analyse()

    # Create result data
    if args.result:
        benchmark.create_result()

    # Clean up when using debug mode
    if jube2.util.DEBUG_MODE:
        benchmark.reset_all_workpackages()
    # Restore current working dir
    os.chdir(cwd)


def _analyse_benchmark(benchmark_folder, args):
    """Analyse existing benchmark"""
    benchmark = _load_existing_benchmark(benchmark_folder, load_analyse=False)

    # Update benchmark data
    _update_benchmark_analyse_and_result(args, benchmark, benchmark_folder)

    # Store current working dir
    cwd = os.getenv("PWD")

    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)

    # Change logfile
    logfile = "analyse.log"
    jube2.util.setup_logging(filename=logfile)

    logger.info(jube2.util.text_boxed(("Analyse benchmark \"{0}\" id: {1}")
                                      .format(benchmark.name, benchmark.id)))
    benchmark.analyse()
    logger.info(">>> Analyse data storage: {}".format(os.path.join(
        benchmark_folder, jube2.util.ANALYSE_FILENAME)))
    logger.info(jube2.util.text_line())
    # Restore current working dir
    os.chdir(cwd)


def _benchmark_result(benchmark_folder, args):
    """Show benchmark result"""
    benchmark = _load_existing_benchmark(benchmark_folder)

    # Update benchmark data
    _update_benchmark_analyse_and_result(args, benchmark, benchmark_folder)

    # Store current working dir
    cwd = os.getenv("PWD")

    # Change current working dir to benchmark_folder
    os.chdir(benchmark_folder)

    # Change logfile
    logfile = "result.log"
    jube2.util.setup_logging(filename=logfile)

    # Run becnhmark analyse
    if args.analyse:
        benchmark.analyse(show_info=False)

    # Create benchmark results
    benchmark.create_result(args.only)

    # Restore current working dir
    os.chdir(cwd)


def _update_benchmark_analyse_and_result(args, benchmark, benchmark_folder):
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
        remove = inp[0:1] == "y"
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
                     jube2.util.CONFIGURATION_FILENAME))


def _get_args_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="show version",
                        action="version",
                        version="JUBE, version {}".format(
                            jube2.util.JUBE_VERSION))
    parser.add_argument('--debug', action="store_true",
                        help='use debugging mode')
    parser.add_argument('--devel', action="store_true",
                        help='show development related information')
    subparsers = parser.add_subparsers(dest="subparser", help='subparsers')
    subparser = dict()

    # run subparser
    subparser["run"] = \
        subparsers.add_parser(
            'run', help='processes benchmark',
            description=jube2.help.HELP['run'],
            formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser["run"].add_argument('files', metavar="FILE", nargs='+',
                                  help="input file")
    subparser["run"].add_argument('--only-bench', nargs='+',
                                  help='only run benchmark')
    subparser["run"].add_argument('--not-bench', nargs='+',
                                  help='do not run benchmark')
    subparser["run"].add_argument("-t", "--tag", nargs='+',
                                  help='select tags')
    subparser["run"].add_argument('--hide-animation', action="store_true",
                                  help='hide animations')
    subparser["run"].add_argument('--include-path', nargs='+',
                                  help='directory containing include files')
    subparser["run"].add_argument("-a", "--analyse", action="store_true",
                                  help="run analyse")
    subparser["run"].add_argument("-r", "--result", action="store_true",
                                  help="show results")
    subparser["run"].add_argument("-m", "--comment", help="add comment")
    subparser["run"].set_defaults(func=run_new_benchmark)

    # continue subparser
    subparser["continue"] = \
        subparsers.add_parser(
            'continue', help='continue benchmark',
            description=jube2.help.HELP['continue'],
            formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser["continue"].add_argument('dir', metavar="DIRECTORY", nargs='?',
                                       help="benchmark directory",
                                       default=".")
    subparser["continue"].add_argument("-i", "--id", type=int,
                                       help="use benchmarks given by id",
                                       nargs="+")
    subparser["continue"].add_argument("--hide-animation", action="store_true",
                                       help="hide animations")
    subparser["continue"].add_argument("-a", "--analyse", action="store_true",
                                       help="run analyse")
    subparser["continue"].add_argument("-r", "--result", action="store_true",
                                       help="show results")
    subparser["continue"].set_defaults(func=continue_benchmarks)

    # analyse subparser
    subparser["analyse"] = \
        subparsers.add_parser(
            'analyse', help='analyse benchmark',
            description=jube2.help.HELP['analyse'],
            formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser["analyse"].add_argument('dir', metavar="DIRECTORY", nargs='?',
                                      help="benchmark directory",
                                      default=".")
    subparser["analyse"].add_argument("-i", "--id", type=int,
                                      help="use benchmarks given by id",
                                      nargs="+")
    subparser["analyse"].add_argument("-u", "--update", metavar="UPDATE_FILE",
                                      help="update analyse and " +
                                      "result configuration")
    subparser["analyse"].add_argument('--include-path', nargs='+',
                                      help="directory containing include " +
                                      "files")
    subparser["analyse"].add_argument("-t", "--tag", nargs='+',
                                      help='select tags')
    subparser["analyse"].set_defaults(func=analyse_benchmarks)

    # result subparser
    subparser["result"] = \
        subparsers.add_parser(
            'result', help='show benchmark results',
            description=jube2.help.HELP['result'],
            formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser["result"].add_argument('dir', metavar="DIRECTORY", nargs='?',
                                     help="benchmark directory",
                                     default=".")
    subparser["result"].add_argument("-i", "--id", type=int,
                                     help="use benchmarks given by id",
                                     nargs="+")
    subparser["result"].add_argument("-a", "--analyse", action="store_true",
                                     help="run analyse before creating" +
                                     "result")
    subparser["result"].add_argument("-u", "--update", metavar="UPDATE_FILE",
                                     help="update analyse and " +
                                     "result configuration")
    subparser["result"].add_argument("--include-path", nargs="+",
                                     help="directory containing include " +
                                     "files")
    subparser["result"].add_argument("-t", "--tag", nargs='+',
                                     help='select tags')
    subparser["result"].add_argument("-o", "--only", nargs="+",
                                     metavar="RESULT_NAME",
                                     help="only create results " +
                                     "given by specific name")
    subparser["result"].set_defaults(func=benchmarks_results)

    # info subparser
    subparser["info"] = \
        subparsers.add_parser(
            'info', help='benchmark information',
            description=jube2.help.HELP['info'],
            formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser["info"].add_argument('dir', metavar="DIRECTORY", nargs='?',
                                   help="benchmark directory",
                                   default=".")
    subparser["info"].add_argument("-i", "--id", type=int,
                                   help="use benchmarks given by id",
                                   nargs="+")
    subparser["info"].add_argument("-s", "--step",
                                   help="show information for given step",
                                   nargs="+")
    subparser["info"].set_defaults(func=info)

    # comment subparser
    subparser["comment"] = \
        subparsers.add_parser(
            'comment', help='comment handling',
            description=jube2.help.HELP['comment'],
            formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser["comment"].add_argument('comment', help="comment")
    subparser["comment"].add_argument('dir', metavar="DIRECTORY", nargs='?',
                                      help="benchmark directory",
                                      default=".")
    subparser["comment"].add_argument("-i", "--id", type=int,
                                      help="use benchmarks given by id",
                                      nargs="+")
    subparser["comment"].add_argument("-a", "--append",
                                      help="append comment to existing one",
                                      action='store_true')
    subparser["comment"].set_defaults(func=manipulate_comments)

    # remove subparser
    subparser["remove"] = \
        subparsers.add_parser(
            'remove', help='remove benchmark',
            description=jube2.help.HELP['remove'],
            formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser["remove"].add_argument('dir', metavar="DIRECTORY", nargs='?',
                                     help="benchmark directory",
                                     default=".")
    subparser["remove"].add_argument("-i", "--id", type=int,
                                     help="use benchmarks given by id",
                                     nargs="+")
    subparser["remove"].add_argument("-f", "--force",
                                     help="force removing, never prompt",
                                     action='store_true')
    subparser["remove"].set_defaults(func=remove_benchmarks)

    # remove subparser
    subparser["help"] = \
        subparsers.add_parser('help', help='command help',
                              description="available commands or " +
                              "info elements: " +
                              ", ".join(sorted(jube2.help.HELP)))
    subparser["help"].add_argument('command', nargs='?',
                                   help="command or info element")
    subparser["help"].set_defaults(func=command_help)

    # convert jube files to jube2 files
    subparser["convert"] = \
        subparsers.add_parser(
            'convert', help='UNDER CONSTRUCTION!!! convert jube files')
    subparser["convert"].add_argument("-i", "--input_path", type=str,
                                      default="./",
                                      help="location of jube XML files")
    subparser["convert"].add_argument("main_xml_file", type=str,
                                      help="Main jube XML")
    subparser["convert"].set_defaults(func=jube2jube2)

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

        jube2.util.setup_logging(logger_config)

        logger.debug("Using logger_config: '{}'".format(logger_config))
        logger.debug("Command: '{}'".format(" ".join(sys.argv)))

        if args.devel:
            args.func(args)
        else:
            try:
                args.func(args)
            except Exception as exeption:
                # Catch all possible Exceptions
                logger.error("\n" + str(exeption))

if __name__ == "__main__":
    main()
