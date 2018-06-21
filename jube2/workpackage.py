# JUBE Benchmarking Environment
# Copyright (C) 2008-2018
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
"""The Workpackage class handles a step and its parameter space"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as ET
import jube2.util.util
import jube2.util.output
import jube2.conf
import jube2.log
import jube2.parameter
import os
import stat

LOGGER = jube2.log.get_logger(__name__)


class Workpackage(object):

    """A Workpackage contains all information to run a specific step with
    its given parameterset.
    """

    # class based counter for unique id creation
    id_counter = 0

    def __init__(self, benchmark, step, local_parameter_names, parameterset,
                 workpackage_id=None, iteration=0, cycle=0):
        # set id
        if workpackage_id is None:
            self._id = Workpackage.id_counter
            Workpackage.id_counter = Workpackage.id_counter + 1
        else:
            self._id = workpackage_id

        self._benchmark = benchmark
        self._step = step
        self._local_parameter_names = local_parameter_names
        self._parameterset = parameterset
        self._iteration = iteration
        self._parents = list()
        self._children = list()
        self._iteration_siblings = set()
        self._queued = False
        self._env = dict(os.environ)
        self._cycle = cycle
        self._workpackage_dir_caching_enabled = False
        self._workpackage_dir_cache = None

    def etree_repr(self):
        """Return etree object representation"""
        workpackage_etree = ET.Element("workpackage")
        workpackage_etree.attrib["id"] = str(self._id)
        step_etree = ET.SubElement(workpackage_etree, "step")
        step_etree.attrib["iteration"] = str(self._iteration)
        step_etree.attrib["cycle"] = str(self._cycle)
        step_etree.text = self._step.name
        if len(self._local_parameter_names) > 0:
            workpackage_etree.append(
                self.local_parameterset.etree_repr(use_current_selection=True))
        if len(self._parents) > 0:
            parents_etree = ET.SubElement(workpackage_etree, "parents")
            parents_etree.text = ",".join(
                [str(parent.id) for parent in self._parents])
        if len(self._iteration_siblings) > 0:
            sibling_etree = ET.SubElement(workpackage_etree,
                                          "iteration_siblings")
            sibling_etree.text = ",".join(
                [str(sibling.id) for sibling in self._iteration_siblings])
        environment_etree = ET.SubElement(workpackage_etree, "environment")
        for env_name, value in self._env.items():
            if (env_name not in ["PWD", "OLDPWD", "_"]) and \
                    (env_name not in os.environ or
                     os.environ[env_name] != value):
                env_etree = ET.SubElement(environment_etree, "env")
                env_etree.attrib["name"] = env_name
                # use string repr to avoid special characters
                env_etree.text = repr(value)
        for env_name in os.environ:
            if (env_name not in ["PWD", "OLDPWD", "_"]) and \
                    (env_name not in self._env):
                env_etree = ET.SubElement(environment_etree, "nonenv")
                env_etree.attrib["name"] = env_name
        return workpackage_etree

    def __repr__(self):
        return (("Workpackage(Id:{0:2d}; Step:{1}; ParentIDs:{2}; " +
                 "ChildIDs:{3} {4})").
                format(self._id, self._step.name,
                       [parent.id for parent in self._parents],
                       [child.id for child in self._children],
                       self.local_parameterset))

    def __eq__(self, other):
        if isinstance(other, Workpackage):
            return self.id == other.id
        else:
            return False

    def __hash__(self):
        return object.__hash__(self)

    @property
    def parameter_dict(self):
        """get all available parameter inside a dict"""
        # Collect parameter for substitution
        parameter = dict([[par.name, par.value] for par in
                          self._parameterset.constant_parameter_dict.values()])
        return parameter

    @property
    def env(self):
        """Return workpackage environment"""
        return self._env

    @property
    def cycle(self):
        """Return current loop cycle"""
        return self._cycle

    def allow_workpackage_dir_caching(self):
        """Enable workpackage dir cache"""
        self._workpackage_dir_caching_enabled = True
        self._workpackage_dir_cache = None

    @property
    def active(self):
        """Check active state"""
        active = self._step.active
        # Collect parameter for substitution
        parameter = self.parameter_dict
        # Parameter substitution
        active = jube2.util.util.substitution(active, parameter)
        # Evaluate active state
        return jube2.util.util.eval_bool(active)

    @property
    def done(self):
        """Workpackage done?"""
        done_file = os.path.join(self.workpackage_dir,
                                 jube2.conf.WORKPACKAGE_DONE_FILENAME)
        exist = os.path.exists(done_file)
        if jube2.conf.DEBUG_MODE:
            exist = exist or os.path.exists(done_file + "_DEBUG")
        return exist

    @done.setter
    def done(self, set_done):
        """Set/reset Workpackage done"""
        done_file = os.path.join(self.workpackage_dir,
                                 jube2.conf.WORKPACKAGE_DONE_FILENAME)
        if jube2.conf.DEBUG_MODE:
            done_file = done_file + "_DEBUG"
        if set_done:
            fout = open(done_file, "w")
            fout.write(jube2.util.util.now_str())
            fout.close()
            self._remove_operation_info_files()
        else:
            if os.path.exists(done_file):
                os.remove(done_file)

    @property
    def error(self):
        """Workpackage error?"""
        error_file = os.path.join(self.workpackage_dir,
                                  jube2.conf.WORKPACKAGE_ERROR_FILENAME)
        return os.path.exists(error_file)

    def set_error(self, set_error, msg=""):
        """Set/reset Workpackage error"""
        error_file = os.path.join(self.workpackage_dir,
                                  jube2.conf.WORKPACKAGE_ERROR_FILENAME)
        if set_error:
            fout = open(error_file, "w")
            fout.write(msg)
            fout.close()
        else:
            if os.path.exists(error_file):
                os.remove(error_file)

    @property
    def queued(self):
        """Workpackage queued?"""
        return self._queued

    @queued.setter
    def queued(self, set_queued):
        """Set queued state"""
        self._queued = set_queued

    @property
    def started(self):
        """Workpackage started?"""
        return os.path.exists(self.workpackage_dir)

    def operation_done_but_pending(self, operation_number):
        """Check if an operation was executed, but the result is still
        pending (because it is a async do)"""
        result = self.operation_done(operation_number)

        operation = self._step.operations[operation_number]

        if result and (operation.async_filename is not None):
            parameter_dict = self.parameter_dict
            if operation.active(parameter_dict):
                work_dir = self.work_dir
                alt_work_dir = self.alt_work_dir(parameter_dict)
                if alt_work_dir is not None:
                    work_dir = alt_work_dir
                async_filename = jube2.util.util.substitution(
                    operation.async_filename, parameter_dict)
                async_filename = \
                    os.path.expandvars(os.path.expanduser(async_filename))
                result = not os.path.exists(os.path.join(work_dir,
                                                         async_filename))
            else:
                result = False
        else:
            result = False
        return result

    def operation_done(self, operation_number, set_done=None):
        """Mark/checks operation status"""
        done_file = os.path.join(self.workpackage_dir,
                                 "wp_{0}_{1:02d}".format(
                                     jube2.conf.WORKPACKAGE_DONE_FILENAME,
                                     operation_number))
        if set_done is None:
            exist = os.path.exists(done_file)
            if jube2.conf.DEBUG_MODE:
                exist = exist or os.path.exists(done_file + "_DEBUG")
            return exist
        else:
            if jube2.conf.DEBUG_MODE:
                done_file = done_file + "_DEBUG"
            elif ((set_done and not os.path.exists(done_file)) or
                  (not set_done and os.path.exists(done_file))):
                jube2.util.util.update_timestamps(
                    os.path.join(self._benchmark.bench_dir,
                                 jube2.conf.TIMESTAMPS_INFO),
                    "change")
            if set_done:
                fout = open(done_file, "w")
                fout.close()
            else:
                if os.path.exists(done_file):
                    os.remove(done_file)
            return set_done

    def _remove_operation_info_files(self):
        """Remove all operation info files"""
        for operation_number in range(len(self._step.operations)):
            self.operation_done(operation_number, False)

    def add_parent(self, workpackage):
        """Add a parent Workpackage"""
        self._parents.append(workpackage)

    @property
    def parameterset(self):
        """Return parameterset"""
        return self._parameterset

    def add_children(self, workpackage):
        """Add a children workpackage"""
        self._children.append(workpackage)

    @property
    def local_parameterset(self):
        """Return local parameterset"""
        parameterset = jube2.parameter.Parameterset()
        for name in self._local_parameter_names:
            parameterset.add_parameter(self._parameterset[name])
        return parameterset

    @property
    def parent_history(self):
        """Create a list of all parents in the history of this workpackage"""
        history = list()
        for parent in self._parents:
            history += parent.parent_history
        history += self._parents
        return history

    @property
    def children_future(self):
        """Create a list of all children in the future of this workpackage"""
        future = list()
        future += self._children
        for child in self._children:
            future += child.children_future
        return future

    @property
    def id(self):
        """Return workpackage id"""
        return self._id

    @property
    def parents(self):
        """Return list of parent workpackages"""
        return self._parents

    @property
    def iteration_siblings(self):
        """Return set of iteration siblings"""
        return self._iteration_siblings

    @property
    def iteration(self):
        """Return workpackage iteration number"""
        return self._iteration

    @property
    def children(self):
        """Return list of child workpackages"""
        return self._children

    @property
    def step(self):
        """Return Step data"""
        return self._step

    def get_jube_cycle_parameterset(self):
        """Return parameterset which contains cycle related
        information"""
        parameterset = jube2.parameter.Parameterset()

        # worpackage cycle
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_cycle",
                             str(self._cycle), parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))

        return parameterset

    def create_relpath(self, value):
        """Create relative path representation"""
        return os.path.relpath(
            os.path.join(self._benchmark.file_path_ref, value),
            self._benchmark.file_path_ref)

    def create_abspath(self, value):
        """Create absolute path representation"""
        return os.path.abspath(
            os.path.join(self._benchmark.file_path_ref, value))

    def get_jube_parameterset(self):
        """Return parameterset which contains workpackage related
        information"""
        parameterset = jube2.parameter.Parameterset()
        # workpackage id
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_id", str(self._id),
                             parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))

        # workpackage id with padding
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_padid",
                             jube2.util.util.id_dir("", self._id),
                             parameter_type="string",
                             update_mode=jube2.parameter.JUBE_MODE))

        # workpackage iteration
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_iteration",
                             str(self._iteration), parameter_type="int",
                             update_mode=jube2.parameter.JUBE_MODE))

        parameterset.add_parameterset(self.get_jube_cycle_parameterset())

        # pathes
        if self._step.alt_work_dir is None:
            path = self.work_dir
        else:
            path = self._step.alt_work_dir

        # workpackage relative folder path
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_relpath", path,
                             update_mode=jube2.parameter.JUBE_MODE,
                             eval_helper=self.create_relpath))

        # workpackage absolute folder path
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_abspath", path,
                             update_mode=jube2.parameter.JUBE_MODE,
                             eval_helper=self.create_abspath))

        # parent workpackage id
        for parent in self._parents:
            parameterset.add_parameter(
                jube2.parameter.Parameter.
                create_parameter(("jube_wp_parent_{0}_id")
                                 .format(parent.step.name),
                                 str(parent.id), parameter_type="int",
                                 update_mode=jube2.parameter.JUBE_MODE))

        # environment export string
        env_str = ""
        parameter_names = [parameter.name for parameter in
                           self._parameterset.export_parameter_dict.values()]
        parameter_names.sort(key=str.lower)
        for name in parameter_names:
            env_str += "export {0}=${1}\n".format(name, name)
        env_par = jube2.parameter.Parameter.create_parameter(
            "jube_wp_envstr", env_str, no_templates=True,
            update_mode=jube2.parameter.JUBE_MODE,
            eval_helper=jube2.parameter.StaticParameter.fix_export_string)
        parameterset.add_parameter(env_par)

        # environment export list
        parameterset.add_parameter(
            jube2.parameter.Parameter.create_parameter(
                "jube_wp_envlist",
                ",".join([name for name in parameter_names]),
                no_templates=True, update_mode=jube2.parameter.JUBE_MODE))

        return parameterset

    def create_workpackage_dir(self):
        """Create work directory"""
        if not os.path.exists(self.workpackage_dir):
            if "$" in self.workpackage_dir:
                raise RuntimeError(("'{0}' could not be evaluated and used " +
                                    "as a workpackage directory name. " +
                                    "Please check the suffix setting.")
                                   .format(self.workpackage_dir))
            os.mkdir(self.workpackage_dir)
            os.mkdir(self.work_dir)

        # Create symbolic link to parent workpackage folder
        for parent in self._parents:
            link_path = os.path.join(self.work_dir, parent.step.name)
            parent_path = os.path.relpath(parent.work_dir, self.work_dir)
            if not os.path.exists(link_path):
                os.symlink(parent_path, link_path)

    def create_shared_folder_link(self, parameter_dict=None):
        """Create shared folder connection"""
        # Create symbolic link to shared folder
        if self._step.shared_link_name is not None:
            shared_folder = self._step.shared_folder_path(
                self._benchmark.bench_dir, parameter_dict)
            # Create shared folder (if it not already exists)
            if not os.path.exists(shared_folder):
                os.mkdir(shared_folder)

            # Create shared folder link
            if parameter_dict is not None:
                shared_name = \
                    jube2.util.util.substitution(self._step.shared_link_name,
                                                 parameter_dict)
            else:
                shared_name = self._step.shared_link_name
            link_path = os.path.join(self.work_dir, shared_name)
            target_path = \
                os.path.relpath(shared_folder, self.work_dir)
            if not os.path.exists(link_path):
                os.symlink(target_path, link_path)

    @property
    def workpackage_dir(self):
        """Return workpackage directory"""
        if not self._workpackage_dir_caching_enabled or \
                self._workpackage_dir_cache is None:
            suffix = self.step.suffix
            if suffix != "":
                # Collect parameter for substitution
                parameter = \
                    dict([[par.name, par.value] for par in
                          self._parameterset.constant_parameter_dict.values()])
                # Parameter substitution
                suffix = jube2.util.util.substitution(suffix, parameter)
                suffix = "_" + os.path.expandvars(os.path.expanduser(suffix))
            path = "{path}_{step_name}{suffix}".format(
                path=jube2.util.util.id_dir(
                    self._benchmark.bench_dir, self._id),
                step_name=self._step.name,
                suffix=suffix)
        if self._workpackage_dir_caching_enabled:
            if self._workpackage_dir_cache is None:
                self._workpackage_dir_cache = path
            return self._workpackage_dir_cache
        else:
            return path

    @property
    def work_dir(self):
        """Return working directory (user space)"""
        return os.path.join(self.workpackage_dir, "work")

    def alt_work_dir(self, parameter_dict=None):
        """Return location of alternative working_dir"""
        if self._step.alt_work_dir is not None:
            if parameter_dict is None:
                parameter_dict = self.parameter_dict
            alt_work_dir = self._step.alt_work_dir
            alt_work_dir = jube2.util.util.substitution(alt_work_dir,
                                                        parameter_dict)
            alt_work_dir = os.path.expandvars(os.path.expanduser(alt_work_dir))
            alt_work_dir = os.path.join(self._benchmark.file_path_ref,
                                        alt_work_dir)
            return alt_work_dir
        else:
            return None

    def _run_operations(self, parameter, work_dir):
        """Run all available operations"""
        continue_op = True
        continue_cycle = True
        for operation_number, operation in enumerate(self._step.operations):
            # Check if the operation is activated
            active = operation.active(parameter)
            if not active:
                self.operation_done(operation_number, True)
            # Do nothing, if the next operation is already finished.
            # Otherwise a removed async_file will result in a new
            # pending operation, if there are two async-operations in
            # a row
            elif not self.operation_done(operation_number + 1):
                # shared operation
                if operation.shared:
                    # wait for all other workpackages and check if shared
                    # operation already finished
                    shared_done = False
                    for workpackage in \
                            self._benchmark.workpackages[self._step.name]:
                        # All workpackages must reach the same position in
                        # the program
                        if operation_number > 0:
                            continue_op = continue_op and \
                                ((workpackage.operation_done(
                                    operation_number - 1) and
                                  (not workpackage.operation_done_but_pending(
                                      operation_number - 1))
                                  ) or
                                 workpackage.done) and \
                                workpackage.cycle == self._cycle
                        # Check if another workpackage already finalized
                        # the operation, only if the operation was active
                        # for this particular workpackage
                        shared_done = shared_done or \
                            ((workpackage.operation_done(
                                operation_number + 1) or workpackage.done
                              ) and
                             operation.active(workpackage.parameter_dict))

                    # All older workpackages in tree must be done
                    for step_name in self._step.get_depend_history(
                            self._benchmark):
                        for workpackage in self._benchmark.workpackages[
                                step_name]:
                            continue_op = continue_op and workpackage.done

                    if continue_op and not shared_done:
                        # remove workpackage specific parameter
                        shared_parameter = dict(parameter)
                        for jube_parameter in self.get_jube_parameterset()\
                                .all_parameter_names:
                            if jube_parameter in shared_parameter:
                                del shared_parameter[jube_parameter]

                        # work_dir = shared_dir
                        shared_dir = \
                            self._step.shared_folder_path(
                                self._benchmark.bench_dir, shared_parameter)

                        LOGGER.debug("====== {0} - shared ======"
                                     .format(self._step.name))

                        continue_op, continue_cycle = operation.execute(
                            parameter_dict=shared_parameter,
                            work_dir=shared_dir,
                            environment=self._env,
                            only_check_pending=self.operation_done(
                                operation_number))

                        # update all workpackages
                        for workpackage in self._benchmark.workpackages[
                                self._step.name]:
                            # if the operation wasn't active in the shared
                            # operation it must not be triggered to
                            # restart
                            if operation.active(
                                    workpackage.parameter_dict):
                                if not workpackage.started:
                                    workpackage.create_workpackage_dir()
                                workpackage.operation_done(
                                    operation_number, True)
                                if continue_op and not continue_cycle:
                                    workpackage.done = True
                                # requeue other workpackages
                                if not workpackage.queued and continue_op:
                                    self._benchmark.work_stat.put(
                                        workpackage)
                        LOGGER.debug("======================={0}"
                                     .format(len(self._step.name) * "="))
                else:
                    continue_op, continue_cycle = operation.execute(
                        parameter_dict=parameter, work_dir=work_dir,
                        environment=self._env,
                        only_check_pending=self.operation_done(
                            operation_number))
                    self.operation_done(operation_number, True)
            if not continue_op or not continue_cycle:
                break
        return continue_op, continue_cycle

    def run(self):
        """Run step and use current parameter space"""

        # Workpackage already done or error?
        if self.done or self.error:
            return

        continue_op = True
        continue_cycle = True
        while (continue_cycle and continue_op):

            stepstr = ("{0} ( iter:{2} | id:{1} | parents:{3} | cycle:{4} )"
                       .format(self._step.name, self._id, self._iteration,
                               ",".join([parent.step.name + "(" +
                                         str(parent.id) + ")"
                                         for parent in self._parents]),
                               self._cycle))
            stepstr = "----- {0} -----".format(stepstr)
            LOGGER.debug(stepstr)

            # --- Check if this is the first run ---
            started_before = self.started

            # --- Create directory structure ---
            if not started_before:
                self.create_workpackage_dir()

            # --- Load environment of parent steps ---
            if not started_before:
                for parent in self._parents:
                    if parent.step.export:
                        self._env.update(parent.env)

            # --- Update JUBE parameter for new cycle ---
            if self._cycle > 0:
                self.parameterset.update_parameterset(
                    self.get_jube_cycle_parameterset())

            # --- Update cycle parameter ---
            update_parameter = \
                self.parameterset.get_updatable_parameter(
                    mode=jube2.parameter.CYCLE_MODE, keep_index=True)
            if len(update_parameter) > 0:
                fixed_parameterset = self.parameterset.copy()
                for parameter in update_parameter:
                    fixed_parameterset.delete_parameter(parameter)
                change = True
                while change:
                    change = False
                    update_parameter.parameter_substitution(
                        [fixed_parameterset])
                    if update_parameter.has_templates:
                        update_parameter = list(
                            update_parameter.expand_templates())[0]
                        change = True
                update_parameter.parameter_substitution(
                    [fixed_parameterset], final_sub=True)
                self.parameterset.update_parameterset(update_parameter)
                debugstr = "  updated parameter:\n"
                debugstr += jube2.util.output.text_table(
                    [("parameter", "value")] + sorted(
                        [(par.name, par.value) for par in update_parameter]),
                    use_header_line=True, indent=9, align_right=False)
                LOGGER.debug(debugstr)

            # --- Collect parameter for substitution ---
            parameter = self.parameter_dict

            if not started_before:
                # --- Collect export parameter ---
                self._env.update(
                    dict([[par.name, par.value] for par in
                          self._parameterset.export_parameter_dict.values()]))

            # --- Create shared folder connection ---
            if self._cycle == 0:
                self.create_shared_folder_link(parameter)

            # --- Create alternativ working dir ---
            alt_work_dir = self.alt_work_dir(parameter)
            if alt_work_dir is not None:
                LOGGER.debug("  switch to alternativ work dir: \"{0}\""
                             .format(alt_work_dir))
                if not jube2.conf.DEBUG_MODE and \
                        not os.path.exists(alt_work_dir):
                    os.makedirs(alt_work_dir)
                    # Get group_id if available (given by JUBE_GROUP_NAME)
                    group_id = jube2.util.util.check_and_get_group_id()
                    if group_id is not None:
                        os.chown(alt_work_dir, os.getuid(), group_id)
                        os.chmod(alt_work_dir,
                                 os.stat(alt_work_dir).st_mode | stat.S_ISGID)

            # Print debug info
            if self._cycle == 0:
                debugstr = "  available parameter:\n"
                debugstr += jube2.util.output.text_table(
                    [("parameter", "value")] + sorted(
                        [(name, par) for name, par in parameter.items()]),
                    use_header_line=True, indent=9,
                    align_right=False)
                LOGGER.debug(debugstr)

            # --- Copy files to working dir or create links ---
            if not started_before:
                # Filter for filesets in uses
                fileset_names = \
                    self._step.get_used_sets(self._benchmark.filesets,
                                             parameter)
                for name in fileset_names:
                    self._benchmark.filesets[name].create(
                        work_dir=self.work_dir,
                        parameter_dict=parameter,
                        alt_work_dir=alt_work_dir,
                        environment=self._env,
                        file_path_ref=self._benchmark.file_path_ref)

            work_dir = self.work_dir
            if alt_work_dir is not None:
                work_dir = alt_work_dir

            # --- File substitution ---
            if not started_before:
                # Filter for substitutionsets in uses
                substituteset_names = \
                    self._step.get_used_sets(self._benchmark.substitutesets,
                                             parameter)
                for name in substituteset_names:
                    self._benchmark.substitutesets[name].substitute(
                        parameter_dict=parameter, work_dir=work_dir)

            try:
                # Run all operations
                # continue_op = false means -> async operation or wait for
                #     others in shared operation
                # continue_cycle = false -> loop cycle was interrupted
                continue_op, continue_cycle = \
                    self._run_operations(parameter, work_dir)

                # --- Check cycle limit ---
                if self._cycle + 1 >= self._step.cycles:
                    continue_cycle = False

                if continue_op and continue_cycle:
                    # --- Prepare additional cycle if needed ---
                    self._cycle += 1
                    self._remove_operation_info_files()
                elif continue_op:
                    # --- Write information file to mark end of work ---
                    self.done = True
            except RuntimeError as re:
                self.set_error(True, str(re))
                continue_cycle = False
                if jube2.conf.EXIT_ON_ERROR:
                    raise(RuntimeError(str(re)))
                else:
                    LOGGER.debug(
                        "{0}\n{1}\n{2}".format(40 * "-", str(re), 40 * "-"))

    @staticmethod
    def reduce_workpackage_id_counter():
        Workpackage.id_counter = Workpackage.id_counter - 1
