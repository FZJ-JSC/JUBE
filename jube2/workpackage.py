"""The Workpackage class handles a step and its parameter space"""

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

import xml.etree.ElementTree as ET
import jube2.util
import jube2.conf
import jube2.log
import jube2.parameter
import os

LOGGER = jube2.log.get_logger(__name__)


class Workpackage(object):

    """A Workpackage contains all information to run a specific step with
    its given parameterset.
    """

    # class based counter for unique id creation
    id_counter = 0

    def __init__(self, benchmark, step, parameterset, history,
                 workpackage_id=None, iteration=0):
        # set id
        if workpackage_id is None:
            self._id = Workpackage.id_counter
            Workpackage.id_counter = Workpackage.id_counter + 1
        else:
            self._id = workpackage_id

        self._benchmark = benchmark
        self._step = step
        self._parameterset = parameterset
        self._history = history
        self._iteration = iteration
        self._parents = list()
        self._children = list()
        self._queued = False

    def etree_repr(self):
        """Return etree object representation"""
        workpackage_etree = ET.Element("workpackage")
        workpackage_etree.attrib["id"] = str(self._id)
        step_etree = ET.SubElement(workpackage_etree, "step")
        step_etree.attrib["iteration"] = str(self._iteration)
        step_etree.text = self._step.name
        if len(self._parameterset) > 0:
            workpackage_etree.append(
                self._parameterset.etree_repr(use_current_selection=True))
        if len(self._parents) > 0:
            parents_etree = ET.SubElement(workpackage_etree, "parents")
            parents_etree.text = jube2.conf.DEFAULT_SEPARATOR.join(
                [str(parent.id) for parent in self._parents])
        return workpackage_etree

    def __repr__(self):
        return (("Workpackage(Id:{0:2d}; Step:{1}; ParentIDs:{2}; " +
                 "ChildIDs:{3} {4})").
                format(self._id, self._step.name,
                       [parent.id for parent in self._parents],
                       [child.id for child in self._children],
                       self._parameterset))

    def __eq__(self, other):
        if isinstance(other, Workpackage):
            return self.id == other.id
        else:
            return False

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
        if set_done:
            if jube2.conf.DEBUG_MODE:
                fout = open(done_file + "_DEBUG", "w")
            else:
                fout = open(done_file, "w")
            fout.close()
            self._remove_operation_info_files()
        else:
            if jube2.conf.DEBUG_MODE:
                if os.path.exists(done_file + "_DEBUG"):
                    os.remove(done_file + "_DEBUG")
            else:
                if os.path.exists(done_file):
                    os.remove(done_file)

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

    def operation_done(self, operation_number, set_done=None):
        """Mark/checks operation status"""
        done_file = os.path.join(self.workpackage_dir,
                                 "wp_{0}_{1:02d}".format(
                                     jube2.conf.WORKPACKAGE_DONE_FILENAME,
                                     operation_number))
        if set_done is None:
            return os.path.exists(done_file)
        else:
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
        """Add a children Workpackage"""
        self._children.append(workpackage)

    @property
    def history(self):
        """Return history Parameterset"""
        return self._history

    @property
    def id(self):
        """Return Workpackage id"""
        return self._id

    @property
    def parents(self):
        """Return list of parent Workpackages"""
        return self._parents

    @property
    def children(self):
        """Return list of child Workpackages"""
        return self._children

    @property
    def step(self):
        """Return Step data"""
        return self._step

    def get_jube_parameterset(self):
        """Return parameterset which contains workpackage related
        information"""
        parameterset = jube2.parameter.Parameterset()
        # workpackage id
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_id", str(self._id),
                             parameter_type="int"))
        # workpackage iteration
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_iteration",
                             str(self._iteration), parameter_type="int"))
        # workpackage absolute folder path
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_abspath",
                             os.path.normpath(os.path.join(
                                 self._benchmark.cwd,
                                 self.work_dir))))
        # parent workpackage id
        for parent in self._parents:
            parameterset.add_parameter(
                jube2.parameter.Parameter.
                create_parameter(("jube_wp_parent_{}_id")
                                 .format(parent.step.name),
                                 str(parent.id), parameter_type="int"))

        env_str = ""
        for parameter in self._parameterset.export_parameter_dict.values():
            env_str += "export {0}=${1}\n".format(parameter.name,
                                                  parameter.name)
        # environment export string
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_wp_envstr", env_str))

        return parameterset

    def create_workpackage_dir(self):
        """Create work directory"""
        if not os.path.exists(self.workpackage_dir):
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
                    jube2.util.substitution(self._step.shared_link_name,
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
        return "{path}_{step_name}".format(
            path=jube2.util.id_dir(self._benchmark.bench_dir, self._id),
            step_name=self._step.name)

    @property
    def work_dir(self):
        """Return working directory (user space)"""
        return os.path.join(self.workpackage_dir, "work")

    def run(self):
        """Run step and use current parameter space"""

        # Workpackage already done?
        if self.done:
            return

        # Create debug string
        if self._step.iterations > 1:
            stepstr = ("{0} ( iter:{1}"
                       .format(self._step.name, self._iteration))
        else:
            stepstr = ("{0} ("
                       .format(self._step.name))

        stepstr += (" id:{1} | parents:{3} )"
                    .format(self._step.name, self._id, self._iteration,
                            ",".join([parent.step.name + "(" +
                                      str(parent.id) + ")"
                                      for parent in self._parents])))
        stepstr = "----- {} -----".format(stepstr)
        LOGGER.debug(stepstr)

        started_before = self.started
        # --- Create directory structure ---
        if not started_before:
            self.create_workpackage_dir()

        # --- Add internal jube parameter ---
        parameterset = self._parameterset.copy()
        parameterset.add_parameterset(self._benchmark.get_jube_parameterset())
        parameterset.add_parameterset(self._step.get_jube_parameterset())
        parameterset.add_parameterset(self.get_jube_parameterset())
        # --- Parameter substitution ---
        if not started_before:
            parameterset.parameter_substitution(final_sub=True)

            # Update parametersets
            self._parameterset.update_parameterset(parameterset)
            self._history.update_parameterset(parameterset)
            for child in self._children:
                child.history.update_parameterset(parameterset)

        # --- Check parameter type ---
        for parameter in parameterset:
            if not parameter.is_template:
                jube2.util.convert_type(parameter.parameter_type,
                                        parameter.value)

        # --- Collect parameter for substitution ---
        parameter = \
            dict([[par.name, par.value] for par in
                  parameterset.constant_parameter_dict.values()])

        # --- Collect export parameter ---
        export_parameter = \
            dict([[par.name, par.value] for par in
                  parameterset.export_parameter_dict.values()])

        # --- Create shared folder connection ---
        self.create_shared_folder_link(parameter)

        # Print debug info
        debugstr = "  available parameter:\n"
        debugstr += jube2.util.text_table([("parameter", "value")] +
                                          sorted([(name, par) for name, par in
                                                  parameter.items()]),
                                          use_header_line=True, indent=9,
                                          align_right=False)
        LOGGER.debug(debugstr)

        # --- Create alternativ working dir ---
        alt_work_dir = self._step.alt_work_dir
        if alt_work_dir is not None:
            alt_work_dir = jube2.util.substitution(alt_work_dir, parameter)
            alt_work_dir = os.path.expandvars(os.path.expanduser(alt_work_dir))
            alt_work_dir = os.path.join(self._benchmark.file_path_ref,
                                        alt_work_dir)
            LOGGER.debug("  switch to alternativ work dir: \"{}\""
                         .format(alt_work_dir))
            if not jube2.conf.DEBUG_MODE and not os.path.exists(alt_work_dir):
                os.makedirs(alt_work_dir)

        # --- Copy files to working dir or create links ---
        if not started_before:
            # Filter for filesets in uses
            fileset_names = \
                self._step.get_used_sets(self._benchmark.filesets)
            for name in fileset_names:
                for file_handle in self._benchmark.filesets[name]:
                    file_handle.create(
                        work_dir=self.work_dir,
                        parameter_dict=parameter,
                        alt_work_dir=alt_work_dir,
                        file_path_ref=self._benchmark.file_path_ref)

        work_dir = self.work_dir
        if alt_work_dir is not None:
            work_dir = alt_work_dir

        # --- File substitution ---
        if not started_before:
            # Filter for substitutionsets in uses
            substituteset_names = \
                self._step.get_used_sets(self._benchmark.substitutesets)
            for name in substituteset_names:
                self._benchmark.substitutesets[name].substitute(
                    parameter_dict=parameter, work_dir=work_dir)

        # --- Run operations ---
        continue_op = True
        for operation_number, operation in enumerate(self._step.operations):
            # Do nothing, if the next operation is already finished. Otherwise
            # a removed async_file will result in a new pending operation, if
            # there are two async-operations in a row.
            if not self.operation_done(operation_number + 1):
                # shared operation
                if operation.shared:

                    # wait for all other workpackages and check if shared
                    # operation already finished
                    shared_done = False
                    for workpackage in \
                            self._benchmark.workpackages[self._step.name]:
                        if operation_number > 0:
                            continue_op = continue_op and \
                                (workpackage.operation_done(
                                    operation_number - 1) or
                                 workpackage.done)
                        shared_done = shared_done or \
                            workpackage.operation_done(
                                operation_number + 1) or workpackage.done

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

                        continue_op = operation.execute(
                            parameter_dict=shared_parameter,
                            work_dir=shared_dir,
                            only_check_pending=self.operation_done(
                                operation_number))

                        # update all workpackages
                        for workpackage in self._benchmark.workpackages[
                                self._step.name]:
                            if not workpackage.started:
                                workpackage.create_workpackage_dir()
                            workpackage.operation_done(operation_number, True)
                            # requeue other workpackages
                            if not workpackage.queued and continue_op:
                                workpackage.queued = True
                                self._benchmark.work_list.put(workpackage)
                        if continue_op:
                            LOGGER.debug(stepstr)
                else:
                    continue_op = operation.execute(
                        parameter_dict=parameter, work_dir=work_dir,
                        export_parameter_dict=export_parameter,
                        only_check_pending=self.operation_done(
                            operation_number))
                    self.operation_done(operation_number, True)
            if not continue_op:
                break

        # --- Write information file to mark end of work ---
        if continue_op:
            self.done = True
