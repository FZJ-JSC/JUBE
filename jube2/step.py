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
"""Step contains the commands for steps"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import subprocess
import os
import re
import time
import xml.etree.ElementTree as ET
import jube2.util
import jube2.conf
import jube2.log

LOGGER = jube2.log.get_logger(__name__)


class Step(object):

    """A Step represent one execution step. It contains a list of
    Do-operations and multiple parametersets, substitutionsets and filesets.
    A Step is a template for Workpackages.
    """

    def __init__(self, name, depend, iterations=1, alt_work_dir=None,
                 shared_name=None, export=False, max_wps="0"):
        self._name = name
        self._use = list()
        self._operations = list()
        self._iterations = iterations
        self._depend = depend
        self._alt_work_dir = alt_work_dir
        self._shared_name = shared_name
        self._export = export
        self._max_wps = max_wps

    def etree_repr(self):
        """Return etree object representation"""
        step_etree = ET.Element("step")
        step_etree.attrib["name"] = self._name
        if len(self._depend) > 0:
            step_etree.attrib["depend"] = \
                jube2.conf.DEFAULT_SEPARATOR.join(self._depend)
        if self._alt_work_dir is not None:
            step_etree.attrib["work_dir"] = self._alt_work_dir
        if self._shared_name is not None:
            step_etree.attrib["shared"] = self._shared_name
        if self._export:
            step_etree.attrib["export"] = "true"
        if self._max_wps != "0":
            step_etree.attrib["max_async"] = self._max_wps
        if self._iterations > 1:
            step_etree.attrib["iterations"] = str(self._iterations)
        for use in self._use:
            use_etree = ET.SubElement(step_etree, "use")
            use_etree.text = jube2.conf.DEFAULT_SEPARATOR.join(use)
        for operation in self._operations:
            step_etree.append(operation.etree_repr())
        return step_etree

    def __repr__(self):
        return "{0}".format(vars(self))

    def add_operation(self, operation):
        """Add operation"""
        self._operations.append(operation)

    def add_uses(self, use_names):
        """Add use"""
        for use_name in use_names:
            if any([use_name in use_list for use_list in self._use]):
                raise ValueError(("Can't use element \"{0}\" two times")
                                 .format(use_name))
        self._use.append(use_names)

    @property
    def name(self):
        """Return step name"""
        return self._name

    @property
    def export(self):
        """Return export behaviour"""
        return self._export

    @property
    def iterations(self):
        """Return iterations"""
        return self._iterations

    @property
    def shared_link_name(self):
        """Return shared link name"""
        return self._shared_name

    @property
    def max_wps(self):
        """Return maximum number of simultaneous workpackages"""
        return self._max_wps

    def get_used_sets(self, available_sets, parameter_dict=None):
        """Get list of all used sets, which can be found in available_sets"""
        set_names = list()
        if parameter_dict is None:
            parameter_dict = dict()
        for use in self._use:
            for name in use:
                name = jube2.util.substitution(name, parameter_dict)
                if (name in available_sets) and (name not in set_names):
                    set_names.append(name)
        return set_names

    def shared_folder_path(self, benchdir, parameter_dict=None):
        """Return shared folder name"""
        if self._shared_name is not None:
            if parameter_dict is not None:
                shared_name = jube2.util.substitution(self._shared_name,
                                                      parameter_dict)
            else:
                shared_name = self._shared_name
            return os.path.join(benchdir,
                                "{0}_{1}".format(self._name, shared_name))
        else:
            return ""

    def get_jube_parameterset(self):
        """Return parameterset which contains step related
        information"""
        parameterset = jube2.parameter.Parameterset()

        # step name
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_step_name", self._name))

        # iterations
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_step_iterations", str(self._iterations),
                             parameter_type="int"))

        return parameterset

    def create_workpackages(self, benchmark, local_parameterset,
                            history_parameterset, used_sets=None,
                            iteration_base=0, parents=None):
        """Create workpackages for current step using given
        benchmark context"""

        if used_sets is None:
            used_sets = set()

        if parents is None:
            parents = list()

        new_workpackages = list()

        # Create parameter dictionary for substitution
        parameter_dict = \
            dict([[par.name, par.value] for par in
                  history_parameterset.constant_parameter_dict.values()])

        # Filter for parametersets in uses
        parameterset_names = \
            set(self.get_used_sets(benchmark.parametersets, parameter_dict))
        new_sets_found = len(parameterset_names.difference(used_sets)) > 0

        if new_sets_found:
            parameterset_names = parameterset_names.difference(used_sets)
            used_sets = used_sets.union(parameterset_names)

            for parameterset_name in parameterset_names:
                # The parametersets in a single step must be compatible
                if not local_parameterset.is_compatible(
                        benchmark.parametersets[parameterset_name]):
                    incompatible_names = \
                        local_parameterset.get_incompatible_parameter(
                            benchmark.parametersets[parameterset_name])
                    raise ValueError(("Can't use parameterset '{0}' in " +
                                      "step '{1}'.\nParameter '{2}' is/are " +
                                      "already defined by a different " +
                                      "parameterset.")
                                     .format(parameterset_name, self.name,
                                             ",".join(incompatible_names)))
                local_parameterset.add_parameterset(
                    benchmark.parametersets[parameterset_name])

            # Combine local and history parameterset
            if local_parameterset.is_compatible(history_parameterset):
                history_parameterset = \
                    local_parameterset.copy().add_parameterset(
                        history_parameterset)
            else:
                LOGGER.debug("Incompatible parameterset combination found " +
                             "between current and parent steps.")
                return new_workpackages

        # Get jube internal parametersets
        jube_parameterset = benchmark.get_jube_parameterset()
        jube_parameterset.add_parameterset(self.get_jube_parameterset())

        # Expand templates
        parametersets = [history_parameterset]
        change = True
        while change:
            change = False
            new_parametersets = list()
            for parameterset in parametersets:
                parameterset.parameter_substitution(
                    additional_parametersets=[jube_parameterset])
                # Maybe new templates were created
                if parameterset.has_templates:
                    new_parametersets += \
                        [new_parameterset for new_parameterset in
                         parameterset.expand_templates()]
                    change = True
                else:
                    new_parametersets += [parameterset]
            parametersets = new_parametersets

        # Create workpackages
        for parameterset in parametersets:
            workpackage_parameterset = local_parameterset.copy()
            workpackage_parameterset.update_parameterset(parameterset)
            if new_sets_found:
                new_workpackages += \
                    self.create_workpackages(benchmark,
                                             workpackage_parameterset,
                                             parameterset, used_sets,
                                             iteration_base, parents)
            else:
                # Create new workpackage
                created_workpackages = list()
                for iteration in range(self.iterations):
                    workpackage = jube2.workpackage.Workpackage(
                        benchmark=benchmark,
                        step=self,
                        parameterset=workpackage_parameterset.copy(),
                        history=parameterset.copy(),
                        iteration=iteration_base * self.iterations + iteration)

                    # --- Link parent workpackages ---
                    for parent in parents:
                        workpackage.add_parent(parent)

                    # --- Final parameter substitution ---
                    workpackage.parameterset.parameter_substitution(
                        additional_parametersets=[
                            jube_parameterset,
                            workpackage.get_jube_parameterset(
                                substitute=False)],
                        final_sub=True)

                    # --- Check parameter type ---
                    for parameter in workpackage.parameterset:
                        if not parameter.is_template:
                            jube2.util.convert_type(
                                parameter.parameter_type, parameter.value)

                    # Update workpackage history parameterset
                    workpackage.history.update_parameterset(
                        workpackage.parameterset)

                    created_workpackages.append(workpackage)

                for workpackage in created_workpackages:
                    workpackage.iteration_siblings.update(
                        set(created_workpackages))

                new_workpackages += created_workpackages

        return new_workpackages

    @property
    def alt_work_dir(self):
        """Return alternativ work directory"""
        return self._alt_work_dir

    @property
    def use(self):
        """Return parameters and substitutions"""
        return self._use

    @property
    def operations(self):
        """Return operations"""
        return self._operations

    @property
    def depend(self):
        """Return dependencies"""
        return self._depend

    def get_depend_history(self, benchmark):
        """Creates a set of all dependent steps in history for given
        benchmark"""
        depend_history = set()
        for step_name in self._depend:
            if step_name not in depend_history:
                depend_history.add(step_name)
                depend_history.update(
                    benchmark.steps[step_name].get_depend_history(benchmark))
        return depend_history


class Operation(object):

    """The Operation-class represents a single instruction, which will be
    executed in a shell environment.
    """

    def __init__(self, do, async_filename=None, stdout_filename=None,
                 stderr_filename=None, active="true", shared=False,
                 work_dir=None):
        self._do = do
        self._async_filename = async_filename
        self._stdout_filename = stdout_filename
        self._stderr_filename = stderr_filename
        self._active = active
        self._shared = shared
        self._work_dir = work_dir

    @property
    def stdout_filename(self):
        """Get stdout filename"""
        return self._stdout_filename

    @property
    def stderr_filename(self):
        """Get stderr filename"""
        return self._stderr_filename

    @property
    def shared(self):
        """Shared operation?"""
        return self._shared

    def execute(self, parameter_dict, work_dir, only_check_pending=False,
                environment=None):
        """Execute the operation. work_dir must be set to the given context
        path. The parameter_dict used for inline substitution.
        If only_check_pending is set to True, the operation will not be
        executed, only the async_file will be checked.
        Return operation status:
        True => operation finished
        False => operation pending
        """
        active = jube2.util.substitution(self._active, parameter_dict)
        if not jube2.util.eval_bool(active):
            return True

        if environment is not None:
            env = environment
        else:
            env = os.environ

        if not only_check_pending:
            # Inline substitution
            do = jube2.util.substitution(self._do, parameter_dict)

            # Remove leading and trailing ; because otherwise ;; will cause
            # trouble when adding ; env
            do = do.strip(";")

            if (not jube2.conf.DEBUG_MODE) and (do.strip() != ""):
                # Change stdout
                if self._stdout_filename is not None:
                    stdout_filename = jube2.util.substitution(
                        self._stdout_filename, parameter_dict)
                    stdout_filename = \
                        os.path.expandvars(os.path.expanduser(stdout_filename))
                else:
                    stdout_filename = "stdout"
                stdout_path = os.path.join(work_dir, stdout_filename)
                stdout = open(stdout_path, "a")

                # Change stderr
                if self._stderr_filename is not None:
                    stderr_filename = jube2.util.substitution(
                        self._stderr_filename, parameter_dict)
                    stderr_filename = \
                        os.path.expandvars(os.path.expanduser(stderr_filename))
                else:
                    stderr_filename = "stderr"
                stderr_path = os.path.join(work_dir, stderr_filename)
                stderr = open(stderr_path, "a")

        # Use operation specific work directory
        if self._work_dir is not None:
            new_work_dir = jube2.util.substitution(
                self._work_dir, parameter_dict)
            new_work_dir = os.path.expandvars(os.path.expanduser(new_work_dir))
            work_dir = os.path.join(work_dir, new_work_dir)

        if not only_check_pending:

            abs_info_file_path = \
                os.path.abspath(os.path.join(work_dir,
                                             jube2.conf.ENVIRONMENT_INFO))

            # Select unix shell
            shell = jube2.conf.STANDARD_SHELL
            if "JUBE_EXEC_SHELL" in os.environ:
                alt_shell = os.environ["JUBE_EXEC_SHELL"].strip()
                if len(alt_shell) > 0:
                    shell = alt_shell

            # Execute "do"
            LOGGER.debug(">>> {0}".format(do))
            if (not jube2.conf.DEBUG_MODE) and (do != ""):
                LOGGER.debug("    stdout: {0}".format(
                    os.path.abspath(stdout_path)))
                LOGGER.debug("    stderr: {0}".format(
                    os.path.abspath(stderr_path)))
                try:
                    if jube2.conf.VERBOSE_LEVEL > 1:
                        stdout_handle = subprocess.PIPE
                    else:
                        stdout_handle = stdout
                    sub = subprocess.Popen(
                        [shell, "-c",
                         "{0} && env > {1}".format(do, abs_info_file_path)],
                        cwd=work_dir, stdout=stdout_handle,
                        stderr=stderr, shell=False,
                        env=env)
                except OSError:
                    stdout.close()
                    stderr.close()
                    raise RuntimeError(("Error (returncode <> 0) while " +
                                        "running \"{0}\" in " +
                                        "directory \"{1}\"")
                                       .format(do, os.path.abspath(work_dir)))

                # stdout verbose output
                if jube2.conf.VERBOSE_LEVEL > 1:
                    while True:
                        read_out = sub.stdout.read(
                            jube2.conf.VERBOSE_STDOUT_READ_CHUNK_SIZE)
                        if (not read_out):
                            break
                        stdout.write(read_out)
                        print(read_out, end="")
                        time.sleep(jube2.conf.VERBOSE_STDOUT_POLL_SLEEP)
                    sub.communicate()

                returncode = sub.wait()

                # Close filehandles
                stdout.close()
                stderr.close()

                env = Operation.read_process_environment(work_dir)

                # Read and store new environment
                if environment is not None:
                    environment.clear()
                    environment.update(env)

                if returncode != 0:
                    if os.path.isfile(stderr_path):
                        stderr = open(stderr_path, "r")
                        stderr_msg = stderr.readlines()
                        stderr.close()
                    else:
                        stderr_msg = ""
                    try:
                        raise RuntimeError(
                            ("Error (returncode <> 0) while running \"{0}\" " +
                             "in directory \"{1}\"\nMessage in \"{2}\":" +
                             "{3}\n{4}").format(
                                do,
                                os.path.abspath(work_dir),
                                os.path.abspath(stderr_path),
                                "\n..." if len(stderr_msg) >
                                jube2.conf.ERROR_MSG_LINES else "",
                                "\n".join(stderr_msg[
                                    -jube2.conf.ERROR_MSG_LINES:])))
                    except UnicodeDecodeError:
                        raise RuntimeError(
                            ("Error (returncode <> 0) while running \"{0}\" " +
                             "in directory \"{1}\"").format(
                                do,
                                os.path.abspath(work_dir)))

        if self._async_filename is not None:
            async_filename = jube2.util.substitution(
                self._async_filename, parameter_dict)
            async_filename = \
                os.path.expandvars(os.path.expanduser(async_filename))
            if not os.path.exists(os.path.join(work_dir, async_filename)):
                LOGGER.debug("Waiting for file \"{0}\" ..."
                             .format(async_filename))
                if jube2.conf.DEBUG_MODE:
                    LOGGER.debug("  skip waiting")
                    return True
                else:
                    return False
            else:
                return True
        else:
            # Operation finished successfully
            return True

    def etree_repr(self):
        """Return etree object representation"""
        do_etree = ET.Element("do")
        do_etree.text = self._do
        if self._async_filename is not None:
            do_etree.attrib["done_file"] = self._async_filename
        if self._stdout_filename is not None:
            do_etree.attrib["stdout"] = self._stdout_filename
        if self._stderr_filename is not None:
            do_etree.attrib["stderr"] = self._stderr_filename
        if self._active != "true":
            do_etree.attrib["active"] = self._active
        if self._shared:
            do_etree.attrib["shared"] = "true"
        if self._work_dir is not None:
            do_etree.attrib["work_dir"] = self._work_dir
        return do_etree

    def __repr__(self):
        return self._do

    @staticmethod
    def read_process_environment(work_dir, remove_after_read=True):
        """Read standard environment info file in given directory."""
        env = dict()
        last = None
        env_file_path = os.path.join(work_dir, jube2.conf.ENVIRONMENT_INFO)
        if os.path.isfile(env_file_path):
            env_file = open(env_file_path, "r")
            for line in env_file:
                line = line.rstrip()
                matcher = re.match(r"^(\S.*?)=(.*?)$", line)
                if matcher:
                    env[matcher.group(1)] = matcher.group(2)
                    last = matcher.group(1)
                elif last is not None:
                    env[last] += "\n" + line
            env_file.close()
            if remove_after_read:
                os.remove(env_file_path)
        return env
