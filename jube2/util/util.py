# JUBE Benchmarking Environment
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
"""Utility functions, constants and classes"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

from collections import deque
import re
import string
import operator
import os.path
import subprocess
import jube2.log
import time
import jube2.conf
import grp
import pwd


LOGGER = jube2.log.get_logger(__name__)


class Queue:
    '''
    Queue based on collections.dequeue
    '''

    def __init__(self):
        '''
        Initialize this queue to the empty queue.
        '''

        self._queue = deque()

    def put(self, item):
        '''
        Add this item to the left of this queue.
        '''

        self._queue.appendleft(item)

    def put_first(self, item):
        '''
        Add this item to the left of this queue.
        '''

        self._queue.append(item)

    def get_nowait(self):
        '''
        Dequeues (i.e., removes) the item from the right side of this queue *and*
        returns this item.

        Raises
        ----------
        IndexError
            If this queue is empty.
        '''

        return self._queue.pop()

    def empty(self):
        '''
        Return True if the queue is empty, False otherwise
        '''

        return False if len(self._queue) > 0 else True


class WorkStat(object):

    """Workpackage queuing handler"""

    def __init__(self):
        self._work_list = Queue()
        self._cnt_work = dict()
        self._wait_lists = dict()

    def put(self, workpackage):
        """Add some workpackage to queue"""

        # Substitute max_wps if needed
        max_wps = int(substitution(workpackage.step.max_wps,
                                   workpackage.parameter_dict))

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
                self._wait_lists[workpackage.step.name] = Queue()
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

    def push_back(self, wp):
        """push element to the first position of the queue"""
        self._work_list.put_first(wp)


def valid_tags(tag_string, tags):
    """Check if tag_string contains only valid tags"""
    if tags is None:
        tags = set()
    tag_tags_str = tag_string
    if tag_tags_str is not None:
        # Check for old tag format
        if "," in tag_tags_str:
            tag_tags_str = jube2.jubeio.Parser._convert_old_tag_format(
                tag_tags_str)
        tag_tags_str = tag_tags_str.replace(' ', '')
        tag_array = [i for i in re.split('[()|+!]', tag_tags_str)
                     if len(i) > 0]
        tag_state = {}
        for tag in tag_array:
            tag_state.update({tag: str(tag in tags)})
        for tag in tag_array:
            tag_tags_str = re.sub(r'(?:^|(?<=\W))' + tag + r'(?=\W|$)',
                                  tag_state[tag], tag_tags_str)
        tag_tags_str = tag_tags_str.replace('|', ' or ')\
            .replace('+', ' and ').replace('!', ' not ')
        try:
            return eval(tag_tags_str)
        except SyntaxError:
            raise ValueError("Tag string '{0}' not parseable."
                             .format(tag_string))
    else:
        return True


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


def expand_dollar_count(text):
    # Replace a even number of $ by $$$$, because they will be
    # substituted to $$. Even number will stay the same, odd number
    # will shrink in every turn
    # $$ -> $$$$ -> $$
    # $$$ -> $$$ -> $
    # $$$$ -> $$$$$$$$ -> $$$$
    # $$$$$ -> $$$$$$$ -> $$$
    return re.sub(r"(^(?=\$)|[^$])((?:\$\$)+?)((?:\${3})?(?:[^$]|$))", r"\1\2\2\3", text)


def substitution(text, substitution_dict):
    """Substitute templates given by parameter_dict inside of text"""
    changed = True
    count = 0
    # All values must be string values (handle Python 2 separatly)
    try:
        str_substitution_dict = \
            dict([(k, str(v).decode("utf-8", errors="ignore")) for k, v in
                  substitution_dict.items()])
    except TypeError:
        str_substitution_dict = \
            dict([(k, str(v).decode("utf-8", "ignore")) for k, v in
                  substitution_dict.items()])
    except AttributeError:
        str_substitution_dict = dict([(k, str(v)) for k, v in
                                      substitution_dict.items()])
    # Preserve non evaluated parameter before starting substitution
    local_substitution_dict = dict([(k, re.sub(r"\$", "$$", v)
                                     if "$" in v else v) for k, v in
                                    str_substitution_dict.items()])

    # Run multiple times to allow recursive parameter substitution
    while changed and count < jube2.conf.MAX_RECURSIVE_SUB:
        count += 1
        orig_text = text
        # Save double $$
        text = expand_dollar_count(text) \
            if "$" in text else text
        tmp = string.Template(text)
        new_text = tmp.safe_substitute(local_substitution_dict)
        changed = new_text != orig_text
        text = new_text
    # Final substitution to remove $$
    tmp = string.Template(text)
    return re.sub("\$(?=([\s]|$))","$$",tmp.safe_substitute(str_substitution_dict))


def convert_type(value_type, value, stop=True):
    """Convert value to given type"""
    result_value = None
    value_type_incorrect=False
    try:
        if value_type == "int":
            if value == "nan":
                result_value = float("nan")
            else:
                result_value = int(float(value))
                if re.match(r"^[-+]?\d+$", value) is None:
                    value_type_incorrect=True
        elif value_type == "float":
            result_value = float(value)
            if re.match(r"([+-]?(?:\d*\.?\d+(?:[eE][-+]?\d+)?|\d+\.))",value) is None:
                value_type_incorrect=True
        else:
            result_value = value
    except ValueError:
        if stop:
            raise ValueError(f"\"{value}\" cannot be represented as a \"{value_type}\"")
        else:
            result_value = value
    if value_type_incorrect:
        print(f"Warning: \"{value}\" was converted to type \"{value_type}\": {result_value}.\n")
        LOGGER.debug(f"Warning: \"{value}\" was converted to type \"{value_type}\": {result_value}.\n")
    return result_value


def script_evaluation(cmd, script_type):
    """cmd will be evaluated with given script language"""
    if script_type == "python":
        if "return " not in cmd:
            try:
                return str(eval(cmd))
            except:
                pass
        loc = {}
        i = cmd.rfind("return ")
        exec(cmd[:i] + cmd[i:].replace("return ", "return_value = "), globals(), loc)
        return str(loc["return_value"])
    elif script_type in ["perl", "shell"]:
        if script_type == "perl":
            cmd = "perl -e \"print " + cmd + "\""

        # Select unix shell
        shell = jube2.conf.STANDARD_SHELL
        if "JUBE_EXEC_SHELL" in os.environ:
            alt_shell = os.environ["JUBE_EXEC_SHELL"].strip()
            if len(alt_shell) > 0:
                shell = alt_shell
        sub = subprocess.Popen([shell, "-c", cmd], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=False)

        stdout, stderr = sub.communicate()
        stdout = stdout.decode(errors="ignore")
        # Check command execution error code
        errorcode = sub.wait()
        if errorcode != 0:
            raise RuntimeError(stderr)
        else:
            if len(stderr.strip()) > 0:
                try:
                    LOGGER.debug((" The command \"{0}\" was executed with a "
                                  "successful error code,\n  but the "
                                  "following error message was produced "
                                  "during its execution: {1}")
                                 .format(cmd, stderr))
                except UnicodeDecodeError:
                    pass
            return stdout


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
            raise ValueError(
                ("\"{0}\" could not be evaluated and handled as boolean "
                 "value. Check if all parameter were correctly replaced and "
                 "the syntax of the expression is well formed ({1}).").format(
                     cmd, str(se)))


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
    order = resolve_depend(depend_dict)
    for step_name in benchmark.steps:
        if step_name not in order:
            raise ValueError("Cannot resolve dependencies.")


class CompType(object):
    """Allow comparison of different datatypes"""

    def __init__(self, value):
        self.__value = value

    def __repr__(self):
        return str(self.__value)

    @property
    def value(self):
        return self.__value

    def _special_comp(self, other, comp_func):
        """Allow comparision of different datatypes"""
        if self.value is None or other.value is None:
            return False
        else:
            try:
                return comp_func(self.value, other.value)
            except TypeError:
                return False

    def __lt__(self, other):
        return self._special_comp(other, operator.lt)

    def __eq__(self, other):
        return self._special_comp(other, operator.eq)


def safe_split(text, separator):
    """Like split for non-empty separator, list with text otherwise."""
    if separator:
        return text.split(separator)
    else:
        return [text]


def ensure_list(element):
    if type(element)!=list:
        return [element]
    else:
        return element
