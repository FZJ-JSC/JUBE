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
"""Utility functions, constants and classes"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

try:
    import queue
except ImportError:
    import Queue as queue
import re
import string
import os.path
import subprocess
import jube2.log
import time
import jube2.conf
import grp
import pwd


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
    elif script_type in ["perl", "shell"]:
        if script_type == "perl":
            cmd = "perl -e \"print " + cmd + "\""
        sub = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
        stdout, stderr = sub.communicate()
        stdout = stdout.decode()
        stderr = stderr.decode()
        # Check command execution error code
        errorcode = sub.wait()
        if errorcode != 0:
            raise RuntimeError(stderr)
        else:
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
            raise ValueError(("\"{0}\" couldn't be evaluated and handled as " +
                              "boolean value. Check if all parameter were " +
                              "correctly replaced and the syntax of the " +
                              "expression is well formed ({1}).")
                             .format(cmd, str(se)))


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
            raise ValueError("Can't resolve dependencies.")


class CompType(object):
    """Allow comparison of different datatypes"""

    def __init__(self, value):
        self.__value = value

    @property
    def value(self):
        return self.__value

    def __lt__(self, other):
        if self.value is None or other.value is None:
            return False
        else:
            try:
                return self.value < other.value
            except TypeError:
                return False
