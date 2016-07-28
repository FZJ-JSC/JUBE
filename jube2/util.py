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
"""Storage for utility functions, constants and classes"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

try:
    import queue
except ImportError:
    import Queue as queue
import xml.etree.ElementTree as ET
import re
import string
import os.path
import subprocess
import jube2.log
import sys
import time
import textwrap
import jube2.conf
import grp
import pwd
import copy


LOGGER = jube2.log.get_logger(__name__)


class WorkStat(object):

    """Workpackage queuing handler"""

    def __init__(self):
        self._work_list = queue.Queue()
        self._cnt_work = dict()
        self._wait_lists = dict()

    def put(self, workpackage):
        """Add some workpackage to queue"""

        # Substitute max_wps if needed
        parameterset = \
            workpackage.add_jube_parameter(workpackage.parameterset.copy())
        parameter = \
            dict([[par.name, par.value] for par in
                  parameterset.constant_parameter_dict.values()])
        max_wps = int(substitution(workpackage.step.max_wps, parameter))

        if (max_wps == 0) or \
           (workpackage.started) or \
           (workpackage.step.name not in self._cnt_work) or \
           (self._cnt_work[workpackage.step.name] < max_wps):
            self._work_list.put(workpackage)
            if workpackage.step.name not in self._cnt_work:
                self._cnt_work[workpackage.step.name] = 1
            else:
                self._cnt_work[workpackage.step.name] += 1
        else:
            if workpackage.step.name not in self._wait_lists:
                self._wait_lists[workpackage.step.name] = queue.Queue()
            self._wait_lists[workpackage.step.name].put(workpackage)

    def update_queues(self, last_workpackage):
        """Check if a workpackage can move from waiting to work queue"""
        if last_workpackage.done:
            self._cnt_work[last_workpackage.step.name] -= 1
            if (last_workpackage.step.name in self._wait_lists) and \
               (not self._wait_lists[last_workpackage.step.name].empty()):
                workpackage = \
                    self._wait_lists[last_workpackage.step.name].get_nowait()
                # Check if workpackage was started from another position
                if not workpackage.started:
                    self.put(workpackage)
                else:
                    self.update_queues(last_workpackage)

    def get(self):
        """Get some workpackage from work queue"""
        return self._work_list.get_nowait()

    def empty(self):
        """Check if work queue is empty"""
        return self._work_list.empty()


def get_current_id(base_dir):
    """Return the highest id found in directory 'base_dir'."""
    try:
        filelist = sorted(os.listdir(base_dir))
    except OSError as error:
        LOGGER.warning(error)
        filelist = list()

    maxi = -1
    for item in filelist:
        try:
            maxi = max(int(re.findall("^([0-9]+)$", item)[0]), maxi)
        except IndexError:
            pass
    return maxi


def id_dir(base_dir, id_number):
    """Return path for 'id_number' in 'base_dir'."""
    return os.path.join(
        base_dir,
        "{id_number:0{zfill}d}".format(zfill=jube2.conf.ZERO_FILL_DEFAULT,
                                       id_number=id_number))


def text_boxed(text):
    """Create an ASCII boxed version of text."""
    box = "#" * jube2.conf.DEFAULT_WIDTH
    for line in text.split("\n"):
        box += "\n"
        lines = ["# {0}".format(element) for element in
                 textwrap.wrap(line.strip(), jube2.conf.DEFAULT_WIDTH - 2)]
        if len(lines) == 0:
            box += "#"
        else:
            box += "\n".join(lines)
    box += "\n" + "#" * jube2.conf.DEFAULT_WIDTH
    return box


def text_line():
    """Return a horizonal ASCII line"""
    return "#" * jube2.conf.DEFAULT_WIDTH


def text_table(entries_ext, use_header_line=False, indent=1, align_right=True,
               auto_linebreak=True, colw=None, pretty=True, separator=None,
               transpose=False):
    """Create a ASCII based table.
    entries must contain a list of lists, use_header_line can be used to
    mark the first entry as title.

    Return the ASCII table
    """

    if not pretty:
        auto_linebreak = False
        use_header_line = False
        indent = 0

    # Transpose data entries if needed
    if transpose:
        entries = list(zip(*entries_ext))
        use_header_line = False
    else:
        entries = copy.deepcopy(entries_ext)

    max_length = list()
    table_str = ""
    header_line_used = not use_header_line

    # calculate needed maxlength
    for item in entries:
        for i, text in enumerate(item):
            if i > len(max_length) - 1:
                max_length.append(0)
            if pretty:
                for line in text.splitlines():
                    max_length[i] = max(max_length[i], len(line))
                if auto_linebreak:
                    max_length[i] = min(max_length[i],
                                        jube2.conf.MAX_TABLE_CELL_WIDTH)

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
                lines = list()
                for line in text.splitlines():
                    lines += \
                        textwrap.wrap(line, jube2.conf.MAX_TABLE_CELL_WIDTH)
                wraps.append(lines)
            else:
                wraps.append(text.splitlines())

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
                    ("{0:" + align + str(max_length[i]) + "s}").format(text)
                if pretty:
                    if i < len(max_length) - 1:
                        if separator is None:
                            line_str += " | "
                        else:
                            line_str += separator
                else:
                    if i < len(max_length) - 1:
                        if separator is None:
                            line_str += ","
                        else:
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
    changed = True
    count = 0
    # All values must be string values
    str_substitution_dict = dict([(k, str(v)) for k, v in
                                  substitution_dict.items()])
    # Preserve non evaluated parameter before starting substitution
    local_substitution_dict = dict([(k, re.sub(r"\$", "$$", v)) for k, v in
                                    str_substitution_dict.items()])
    # Run multiple times to allow recursive parameter substitution
    while changed and count < jube2.conf.MAX_RECURSIVE_SUB:
        count += 1
        orig_text = text
        # Save double $$
        text = re.sub(r"(\$\$)(?=(\$\$|[^$]))", "$$$$", text)
        tmp = string.Template(text)
        new_text = tmp.safe_substitute(local_substitution_dict)
        changed = new_text != orig_text
        text = new_text
    # Final substitution to remove $$
    tmp = string.Template(text)
    return tmp.safe_substitute(str_substitution_dict)


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
    format_string = "{{0:{0}}}".format(format_string)
    return format_string.format(value)


def convert_type(value_type, value, stop=True):
    """Convert value to given type"""
    result_value = None
    try:
        if value_type == "int":
            if value == "nan":
                result_value = float("nan")
            else:
                result_value = int(float(value))
        elif value_type == "float":
            result_value = float(value)
        else:
            result_value = value
    except ValueError:
        if stop:
            raise ValueError(("\"{0}\" can't be represented as a \"{1}\"")
                             .format(value, value_type))
        else:
            result_value = value
    return result_value


def script_evaluation(cmd, script_type):
    """cmd will be evaluated with given script language"""
    if script_type == "python":
        return str(eval(cmd))
    elif script_type == "perl":
        cmd = "perl -e \"print " + cmd + "\""
        sub = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
        return sub.communicate()[0].decode()
    elif script_type == "shell":
        sub = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
        return sub.communicate()[0].decode()


def eval_bool(cmd):
    """Evaluate a bool expression"""
    if cmd.lower() == "true":
        return True
    elif cmd.lower() == "false":
        return False
    else:
        try:
            return bool(eval(cmd))
        except SyntaxError as se:
            raise ValueError(("\"{0}\" couldn't be evaluated and handled as " +
                              "boolean value. Check if all parameter were " +
                              "correctly replaced and the syntax of the " +
                              "expression is well formed ({1}).")
                             .format(cmd, str(se)))


def print_loading_bar(current_cnt, all_cnt, second_cnt=0):
    """Show a simple loading animation"""
    width = jube2.conf.DEFAULT_WIDTH - 10
    if all_cnt > 0:
        done_cnt = (current_cnt * width) // all_cnt
        medium_cnt = (second_cnt * width) // all_cnt
    else:
        done_cnt = 0
        medium_cnt = 0

    # shrink medium_cnt if there was some rounding issue
    if (medium_cnt > 0) and (width < medium_cnt + done_cnt):
        medium_cnt = width - done_cnt

    # fill up medium_cnt if there was some rounding issue
    if (current_cnt + second_cnt == all_cnt) and \
            (medium_cnt + done_cnt < width):
        medium_cnt += width - (medium_cnt + done_cnt)

    todo_cnt = width - done_cnt - medium_cnt

    bar_str = "\r{0}{1}{2} ({3:3d}/{4:3d})".format("#" * done_cnt,
                                                   "0" * medium_cnt,
                                                   "." * todo_cnt,
                                                   current_cnt, all_cnt)
    sys.stdout.write(bar_str)
    sys.stdout.flush()


def element_tree_tostring(element, encoding=None):
    """A more encoding friendly ElementTree.tostring method"""
    class Dummy(object):

        """Dummy class to offer write method for etree."""

        def __init__(self):
            self._data = list()

        @property
        def data(self):
            """Return data"""
            return self._data

        def write(self, *args):
            """Simulate write"""
            self._data.append(*args)
    file_dummy = Dummy()
    ET.ElementTree(element).write(file_dummy, encoding)
    return "".join(dat.decode(encoding) for dat in file_dummy.data)


def get_tree_element(node, tag_path=None, attribute_dict=None):
    """Can be used instead of node.find(.//tag_path[@attrib=value])"""
    result = get_tree_elements(node, tag_path, attribute_dict)
    if len(result) > 0:
        return result[0]
    else:
        return None


def get_tree_elements(node, tag_path=None, attribute_dict=None):
    """Can be used instead of node.findall(.//tag_path[@attrib=value])"""
    if attribute_dict is None:
        attribute_dict = dict()

    result = list()

    if tag_path is not None:
        node_list = node.findall(tag_path)
    else:
        node_list = [node]

    for found_node in node_list:
        for attribute, value in attribute_dict.items():
            if found_node.get(attribute) != value:
                break
        else:
            result.append(found_node)

    for subtree in node:
        result += get_tree_elements(subtree, tag_path, attribute_dict)

    return result


def now_str():
    """Return current time string"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def update_timestamps(path, *args):
    """Set all timestamps for given arg_names to now"""
    timestamps = dict()
    timestamps.update(read_timestamps(path))
    file_ptr = open(path, "w")
    for arg in args:
        timestamps[arg] = now_str()
    for timestamp in timestamps:
        file_ptr.write("{0}: {1}\n".format(timestamp, timestamps[timestamp]))
    file_ptr.close()


def read_timestamps(path):
    """Return timestamps dictionary"""
    timestamps = dict()
    if os.path.isfile(path):
        file_ptr = open(path, "r")
        for line in file_ptr:
            matcher = re.match("(.*?): (.*)", line.strip())
            if matcher:
                timestamps[matcher.group(1)] = matcher.group(2)
        file_ptr.close()
    return timestamps


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
            infostr = ("unresolved steps: {0}".
                       format(",".join(unresolved_steps)) + "\n" +
                       "unresolved dependencies: {0}".
                       format(",".join(unresolved_dependencies)))
            LOGGER.warning(infostr)

        return (possible, remain)

    finished = set()
    work_list = list()

    work, remain = find_next(depend_dict, finished)
    while work:
        work_list += list(work)
        finished.update(work)
        work, remain = find_next(remain, finished)

    return work_list


def check_and_get_group_id():
    """Read environment var JUBE_GROUP_NAME and return group id"""
    group_name = ""
    if "JUBE_GROUP_NAME" in os.environ:
        group_name = os.environ["JUBE_GROUP_NAME"].strip()

    if group_name != "":
        try:
            group_id = grp.getgrnam(group_name).gr_gid
        except KeyError:
            raise ValueError(("Failed to get group ID, group \"{0}\" " +
                              "does not exist").format(group_name))
        user = pwd.getpwuid(os.getuid()).pw_name
        grp_members = grp.getgrgid(group_id).gr_mem
        if user in grp_members:
            return group_id
        else:
            raise ValueError(("User \"{0}\" is not in " +
                              "group \"{1}\"").format(user, group_name))
    else:
        return None


def consistency_check(benchmark):
    """Do some consistency checks"""

    # check if step uses exists
    for step in benchmark.steps.values():
        for uses in step.use:
            for use in uses:
                if (use not in benchmark.parametersets) and \
                   (use not in benchmark.filesets) and \
                   (use not in benchmark.substitutesets) and \
                   ("$" not in use):
                    raise ValueError(("<use>{0}</use> not found in "
                                      "available sets").format(use))
    # Dependency check
    depend_dict = \
        dict([(step.name, step.depend) for step in benchmark.steps.values()])
    order = jube2.util.resolve_depend(depend_dict)
    for step_name in benchmark.steps:
        if step_name not in order:
            raise ValueError("Can't resolve dependencies.")
