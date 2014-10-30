"""Storage for utility functions, constants and classes"""

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

import re
import string
import os.path
import subprocess
import logging
import sys
import textwrap

JUBE_VERSION = "2.0.0"
ZERO_FILL_DEFAULT = 6
DEFAULT_WIDTH = 70
WORKPACKAGE_DONE_FILENAME = "done"
CONFIGURATION_FILENAME = "configuration.xml"
WORKPACKAGES_FILENAME = "workpackages.xml"
ANALYSE_FILENAME = "analyse.xml"
RESULT_DIRNAME = "result"
ALLOWED_SCRIPTTYPES = ["python", "perl"]
DEBUG_MODE = False
DEFAULT_SEPARATOR = ","
MAX_TABLE_CELL_WIDTH = 40
HIDE_ANIMATIONS = False

# logging related
LOGFILE_NAME = "jube.log"
LOGFILE_MODE = "a"
LOG_CONSOLE_FORMAT = "%(message)s"
LOG_FILE_FORMAT = "[%(asctime)s]:%(levelname)s: %(message)s"


class JubeLogger(logging.getLoggerClass()):

    """Overwrite logging to handle multi line messages."""

    def _log(self, level, msg, *args, **kwargs):
        """Log multi line messages each as a separate entry."""
        if hasattr(msg, "splitlines"):
            lines = msg.splitlines()
        else:
            lines = str(msg).splitlines()
        for line in lines:
            super(JubeLogger, self)._log(level, line, *args, **kwargs)


logging.setLoggerClass(JubeLogger)
logger = logging.getLogger(__name__)


def setup_logging(mode, filename=LOGFILE_NAME):
    """Setup the logging configuration.

    Available modes are
      default   log to console and file
      console   only console output

    filename can be given optionally.

    The setup includes setting the handlers and formatters. Calling
    this function multiple times causes old handlers to be removed
    before new ones are added.

    """
    _logger = logging.getLogger("jube2")
    # this is needed to make the other handlers accept on low priority
    # events
    _logger.setLevel(logging.DEBUG)

    # list is needed since we remove from the list we just iterate
    # over
    for handler in list(_logger.handlers):
        handler.close()
        _logger.removeHandler(handler)

    # create, configure and add console handler
    console_formatter = logging.Formatter(LOG_CONSOLE_FORMAT)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    if mode == "default":
        # create, configure and add file handler
        file_formatter = logging.Formatter(LOG_FILE_FORMAT)
        file_handler = logging.FileHandler(filename, LOGFILE_MODE)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        _logger.addHandler(file_handler)


def get_current_id(base_dir):
    """Return the highest id found in directory 'base_dir'."""
    try:
        filelist = sorted(os.listdir(base_dir))
    except OSError as error:
        logger.warning(error)
        filelist = list()

    maxi = -1
    for item in filelist:
        try:
            maxi = max(int(re.findall("([0-9]+)", item)[0]), maxi)
        except IndexError:
            pass
    return maxi


def id_dir(base_dir, id_number):
    """Return path for 'id_number' in 'base_dir'."""
    return os.path.join(base_dir,
                        "{id_number:0{zfill}d}".format(zfill=ZERO_FILL_DEFAULT,
                                                       id_number=id_number))


def text_boxed(text):
    """Create an ASCII boxed version of text."""
    box = "{line}\n# {text}\n{line}".format(
        line="#" * DEFAULT_WIDTH, text=text)
    return box


def text_line():
    """Return a horizonal ASCII line"""
    return "#" * DEFAULT_WIDTH


def text_table(entries, use_header_line=False, indent=1, align_right=True,
               auto_linebreak=True, colw=None, pretty=True, separator=","):
    """Create a ASCII based table.
    entries must contain a list of lists, use_header_line can be used to
    mark the first entry as title.

    Return the ASCII table
    """

    if not pretty:
        auto_linebreak = False
        use_header_line = False
        indent = 0

    max_length = list()
    table_str = ""
    header_line_used = not use_header_line

    # calculate needed maxlength
    for item in entries:
        for i, text in enumerate(item):
            if i > len(max_length) - 1:
                max_length.append(0)
            if pretty:
                max_length[i] = max(max_length[i], len(text))
                if auto_linebreak:
                    max_length[i] = min(max_length[i], MAX_TABLE_CELL_WIDTH)

    if colw is not None:
        for i, maxl in enumerate(max_length):
            if i < len(colw):
                max_length[i] = max(maxl, colw[i])

    # fill cells
    for item in entries:

        # Wrap text
        wraps = list()
        for text in item:
            if auto_linebreak:
                wraps.append(textwrap.wrap(text, MAX_TABLE_CELL_WIDTH))
            else:
                wraps.append([text])

        grow = True
        height = 0
        while grow:
            grow = False
            line_str = " " * indent
            for i, wrap in enumerate(wraps):
                grow = grow or len(wrap) > height + 1
                if len(wrap) > height:
                    text = wrap[height]
                else:
                    text = ""
                if align_right and height == 0:
                    align = ">"
                else:
                    align = "<"
                line_str += \
                    ("{:" + align + str(max_length[i]) + "s}").format(text)
                if pretty:
                    if i < len(max_length) - 1:
                        line_str += " | "
                else:
                    if i < len(max_length) - 1:
                        line_str += separator
            line_str += "\n"
            table_str += line_str
            height += 1

        if not header_line_used:
            # Create title separator line
            table_str += " " * indent
            for i, cell_length in enumerate(max_length):
                table_str += "-" * cell_length
                if i < len(max_length) - 1:
                    table_str += "-+-"
            table_str += "\n"
            header_line_used = True
    return table_str


def substitution(text, substitution_dict):
    """Substitute templates given by parameter_dict inside of text"""
    tmp = string.Template(text)
    return tmp.safe_substitute(substitution_dict)


def format_value(format_string, value):
    """Return formated value"""
    if (type(value) is not int) and \
            (("d" in format_string) or ("b" in format_string) or
             ("c" in format_string) or ("o" in format_string) or
             ("x" in format_string) or ("X" in format_string)):
        value = int(float(value))
    elif (type(value) is not float) and \
         (("e" in format_string) or ("E" in format_string) or
          ("f" in format_string) or ("F" in format_string) or
          ("g" in format_string) or ("G" in format_string)):
        value = float(value)
    format_string = "{{:{}}}".format(format_string)
    return format_string.format(value)


def convert_type(value_type, value, stop=True):
    """Convert value to given type"""
    result_value = None
    try:
        if value_type == "int":
            result_value = int(value)
        elif value_type == "float":
            result_value = float(value)
        else:
            result_value = value
    except ValueError:
        if stop:
            raise ValueError(("\"{0}\" can't be represented as a \"{1}\"")
                             .format(value, value_type))
        else:
            if value_type == "int":
                result_value = int()
            elif value_type == "float":
                result_value = float()
            logger.warning(("\"{0}\" can't be represented as a \"{1}\"")
                           .format(value, value_type))
    return result_value


def script_evaluation(cmd, script_type):
    """cmd will be evaluated with given script language"""
    if script_type == "python":
        return str(eval(cmd))
    elif script_type == "perl":
        cmd = "perl -e \"print " + cmd + "\""
        sub = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
        return sub.communicate()[0]


def print_loading_bar(current_cnt, all_cnt, second_cnt=0):
    """Show a simple loading animation"""
    width = DEFAULT_WIDTH - 10
    if all_cnt > 0:
        done_cnt = (current_cnt * width) // all_cnt
        medium_cnt = (second_cnt * width) // all_cnt
    else:
        done_cnt = 0
        medium_cnt = 0

    if (medium_cnt > 0) and (width < medium_cnt + done_cnt):
        medium_cnt = width - done_cnt

    todo_cnt = width - done_cnt - medium_cnt

    bar_str = "\r{0}{1}{2} ({3:3d}/{4:3d})".format("#" * done_cnt,
                                                   "0" * medium_cnt,
                                                   "." * todo_cnt,
                                                   current_cnt, all_cnt)
    sys.stdout.write(bar_str)
    sys.stdout.flush()


def resolve_depend(depend_dict):
    """Generate a serialization of dependent steps.

    Return a list with a possible order of execution.
    """
    def find_next(dependencies, finished):
        """Returns the next possible items to be processed and remainder.

        dependencies  Dictionary containing the dependencies
        finished      Set which is already processed
        """
        possible = set()
        remain = dict()

        for key, val in dependencies.items():
            if val.issubset(finished):
                possible.add(key)
            else:
                remain[key] = val

        possible.difference_update(finished)
        # no advance
        if dependencies and not possible:
            unresolved_steps = set(dependencies) - finished
            unresolved_dependencies = set()
            for step in unresolved_steps:
                unresolved_dependencies.update(depend_dict[step] -
                                               finished)
            infostr = ("unresolved steps: {}".
                       format(",".join(unresolved_steps)) + "\n" +
                       "unresolved dependencies: {}".
                       format(",".join(unresolved_dependencies)))
            logger.warning(infostr)

        return (possible, remain)

    finished = set()
    work_list = list()

    work, remain = find_next(depend_dict, finished)
    while work:
        work_list += list(work)
        finished.update(work)
        work, remain = find_next(remain, finished)

    return work_list


def consistency_check(benchmark):
    """Do some consistency checks"""

    # check if step uses exists
    for step in benchmark.steps.values():
        for uses in step.use:
            for use in uses:
                if (use not in benchmark.parametersets) and \
                   (use not in benchmark.filesets) and \
                   (use not in benchmark.substitutesets):
                    raise ValueError(("<use>{}</use> not found in available " +
                                      "sets").format(use))
