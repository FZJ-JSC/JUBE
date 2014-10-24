"""Step contains the commands for steps"""

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

import subprocess
import os
import xml.etree.ElementTree as ET
import jube2.util
import logging

logger = logging.getLogger(__name__)


class Step(object):

    """A Step represent one execution step. It contains a list of
    Do-operations and multiple parametersets, substitutionsets and filesets.
    A Step is a template for Workpackages.
    """

    def __init__(self, name, depend, iterations=1, alt_work_dir=None,
                 shared_name=None):
        self._name = name
        self._use = list()
        self._operations = list()
        self._iterations = iterations
        self._depend = depend
        self._alt_work_dir = alt_work_dir
        self._shared_name = shared_name

    def etree_repr(self, new_cwd=None):
        """Return etree object representation"""
        step_etree = ET.Element("step")
        step_etree.attrib["name"] = self._name
        if len(self._depend) > 0:
            step_etree.attrib["depend"] = \
                jube2.util.DEFAULT_SEPARATOR.join(self._depend)
        if self._alt_work_dir is not None:
            if (new_cwd is not None) and \
               (not os.path.isabs(self._alt_work_dir)):
                work_dir = os.path.relpath(self._alt_work_dir, new_cwd)
            else:
                work_dir = self._alt_work_dir
            step_etree.attrib["work_dir"] = work_dir
        if self._shared_name is not None:
            step_etree.attrib["shared"] = self._shared_name
        if self._iterations > 1:
            step_etree.attrib["iterations"] = str(self._iterations)
        for use in self._use:
            use_etree = ET.SubElement(step_etree, "use")
            use_etree.text = jube2.util.DEFAULT_SEPARATOR.join(use)
        for operation in self._operations:
            step_etree.append(operation.etree_repr())
        return step_etree

    def __repr__(self):
        return "{}".format(vars(self))

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
    def iterations(self):
        """Return iterations"""
        return self._iterations

    @property
    def shared_link_name(self):
        """Return shared link name"""
        return self._shared_name

    def get_used_sets(self, available_sets):
        """Get set of all used sets, which can be found in available_sets"""
        set_names = set()
        # Filter for filesets in uses
        for use in self._use:
            for name in use:
                if name in available_sets:
                    set_names.add(name)
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


class Operation(object):

    """The Operation-class represents a single instruction, which will be
    executed in a shell environment.
    """

    def __init__(self, do, async_filename=None, stdout_filename=None,
                 stderr_filename=None, active="true", shared=False):
        self._do = do
        self._async_filename = async_filename
        self._stdout_filename = stdout_filename
        self._stderr_filename = stderr_filename
        self._active = active
        self._shared = shared

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

    def execute(self, parameter_dict, work_dir, only_check_pending=False):
        """Execute the operation. work_dir must be set to the given context
        path. The parameter_dict used for inline substitution.
        If only_check_pending is set to True, the operation will not be
        executed, only the async_file will be checked.
        Return operation status:
        True => operation finished
        False => operation pending
        """
        active = jube2.util.substitution(self._active, parameter_dict)
        if active == "false":
            return True
        elif active != "true":
            raise RuntimeError(("<do active=\"{}\"> not allowed. Must be " +
                                "true or false").format(active))

        if not only_check_pending:
            # Inline substitution
            do = jube2.util.substitution(self._do, parameter_dict)

            if not jube2.util.DEBUG_MODE:
                # Change stdout
                if self._stdout_filename is not None:
                    stdout_filename = jube2.util.substitution(
                        self._stdout_filename,
                        parameter_dict)
                else:
                    stdout_filename = "stdout"
                stdout = open(os.path.join(work_dir, stdout_filename), "a")

                # Change stderr
                if self._stderr_filename is not None:
                    stderr_filename = jube2.util.substitution(
                        self._stderr_filename,
                        parameter_dict)
                else:
                    stderr_filename = "stderr"
                stderr = open(os.path.join(work_dir, stderr_filename), "a")

            # Execute "do"
            logger.debug(">>> {}".format(do))
            if not jube2.util.DEBUG_MODE:
                try:
                    sub = subprocess.Popen(do, cwd=work_dir, stdout=stdout,
                                           stderr=stderr, shell=True)
                except OSError:
                    raise RuntimeError(("Error (returncode <> 0) while " +
                                        "running \"{}\" in " +
                                        "directory \"{}\"")
                                       .format(do, os.path.abspath(work_dir)))
                returncode = sub.wait()

                # Close filehandles
                stdout.close()
                stderr.close()

                if returncode != 0:
                    raise RuntimeError(("Error (returncode <> 0) while " +
                                        "running \"{}\" in " +
                                        "directory \"{}\"")
                                       .format(do, os.path.abspath(work_dir)))

        if self._async_filename is not None:
            async_filename = jube2.util.substitution(
                self._async_filename,
                parameter_dict)
            async_filename = \
                os.path.expandvars(os.path.expanduser(async_filename))
            if not os.path.exists(os.path.join(work_dir, async_filename)):
                logger.debug("Waiting for file \"{}\" ..."
                             .format(async_filename))
                if jube2.util.DEBUG_MODE:
                    logger.debug("  skip waiting")
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
        return do_etree

    def __repr__(self):
        return self._do
