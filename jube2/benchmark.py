# JUBE Benchmarking Environment
# Copyright (C) 2008-2015
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
"""The Benchmark class manages the benchmark process"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import xml.etree.ElementTree as ET
import xml.dom.minidom as DOM
import os
import pprint
import shutil
import itertools
import jube2.parameter
import jube2.workpackage
import jube2.util
import jube2.conf
import jube2.log

LOGGER = jube2.log.get_logger(__name__)


class Benchmark(object):

    """The Benchmark class contains all data to run a benchmark"""

    def __init__(self, name, outpath, parametersets, substitutesets,
                 filesets, patternsets, steps, analyser, results,
                 results_order, comment="", tags=None):
        self._name = name
        self._outpath = outpath
        self._parametersets = parametersets
        self._substitutesets = substitutesets
        self._filesets = filesets
        self._patternsets = patternsets
        self._steps = steps
        self._analyser = analyser
        for analyser in self._analyser.values():
            analyser.benchmark = self
        self._results = results
        self._results_order = results_order
        for result in self._results.values():
            result.benchmark = self
        self._workpackages = dict()
        self._work_stat = jube2.util.WorkStat()
        self._comment = comment
        self._id = -1
        self._org_cwd = "."
        self._cwd = "."
        self._file_path_ref = "."
        if tags is None:
            self._tags = set()
        else:
            self._tags = tags

    @property
    def name(self):
        """Return benchmark name"""
        return self._name

    @property
    def comment(self):
        """Return comment string"""
        return self._comment

    @property
    def tags(self):
        """Return set of tags"""
        return self._tags

    @comment.setter
    def comment(self, new_comment):
        """Set new comment string"""
        self._comment = new_comment

    @property
    def parametersets(self):
        """Return parametersets"""
        return self._parametersets

    @property
    def patternsets(self):
        """Return patternsets"""
        return self._patternsets

    @property
    def analyser(self):
        """Return analyser"""
        return self._analyser

    @property
    def results(self):
        """Return results"""
        return self._results

    @property
    def results_order(self):
        """Return results_order"""
        return self._results_order

    @property
    def cwd(self):
        """Get current working directory"""
        return self._cwd

    @cwd.setter
    def cwd(self, cwd):
        """Set current working directory"""
        self._cwd = cwd

    @property
    def org_cwd(self):
        """Get original current working directory"""
        return self._org_cwd

    @org_cwd.setter
    def org_cwd(self, org_cwd):
        """Set original current working directory"""
        self._org_cwd = org_cwd

    @property
    def file_path_ref(self):
        """Get file path reference"""
        return self._file_path_ref

    @file_path_ref.setter
    def file_path_ref(self, file_path_ref):
        """Set file path reference"""
        self._file_path_ref = file_path_ref

    @property
    def substitutesets(self):
        """Return substitutesets"""
        return self._substitutesets

    @property
    def workpackages(self):
        """Return workpackages"""
        return self._workpackages

    @property
    def work_stat(self):
        """Return work queue"""
        return self._work_stat

    @property
    def filesets(self):
        """Return filesets"""
        return self._filesets

    def delete_bench_dir(self):
        """Delete all data inside benchmark directory"""
        if os.path.exists(self.bench_dir):
            shutil.rmtree(self.bench_dir, ignore_errors=True)

    @property
    def steps(self):
        """Return steps"""
        return self._steps

    @property
    def workpackage_status(self):
        """Retun workpackage information dict"""
        result_dict = dict()
        for stepname in self._workpackages:
            result_dict[stepname] = {"all": 0,
                                     "open": 0,
                                     "wait": 0,
                                     "done": 0}
            for workpackage in self._workpackages[stepname]:
                result_dict[stepname]["all"] += 1
                if workpackage.done:
                    result_dict[stepname]["done"] += 1
                elif workpackage.started:
                    result_dict[stepname]["wait"] += 1
                else:
                    result_dict[stepname]["open"] += 1
        return result_dict

    @property
    def benchmark_status(self):
        """Retun global workpackage information dict"""
        result_dict = {"all": 0,
                       "open": 0,
                       "wait": 0,
                       "done": 0}

        for status in self.workpackage_status.values():
            result_dict["all"] += status["all"]
            result_dict["open"] += status["open"]
            result_dict["wait"] += status["wait"]
            result_dict["done"] += status["done"]

        return result_dict

    @property
    def id(self):
        """Return benchmark id"""
        return self._id

    @id.setter
    def id(self, new_id):
        """Set new benchmark id"""
        self._id = new_id

    def get_jube_parameterset(self):
        """Return parameterset which contains benchmark related
        information"""
        parameterset = jube2.parameter.Parameterset()
        # benchmark id
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_benchmark_id",
                             str(self._id), parameter_type="int"))
        # benchmark name
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_benchmark_name", self._name))

        # benchmark home
        parameterset.add_parameter(
            jube2.parameter.Parameter.
            create_parameter("jube_benchmark_home",
                             os.path.abspath(self._file_path_ref)))

        timestamps = jube2.util.read_timestamps(
            os.path.join(self.bench_dir, jube2.conf.TIMESTAMPS_INFO))

        # benchmark start
        parameterset.add_parameter(
            jube2.parameter.Parameter.create_parameter(
                "jube_benchmark_start", timestamps.get("start", "")))

        return parameterset

    def etree_repr(self, new_cwd=None):
        """Return etree object representation"""
        benchmark_etree = ET.Element("benchmark")
        if len(self._comment) > 0:
            comment_element = ET.SubElement(benchmark_etree, "comment")
            comment_element.text = self._comment
        benchmark_etree.attrib["name"] = self._name
        if new_cwd is not None:
            benchmark_etree.attrib["file_path_ref"] = \
                os.path.relpath(self._file_path_ref, new_cwd)
            if not os.path.isabs(self._outpath):
                benchmark_etree.attrib["outpath"] = \
                    os.path.relpath(self._outpath, new_cwd)
            else:
                benchmark_etree.attrib["outpath"] = self._outpath

        for parameterset in self._parametersets.values():
            benchmark_etree.append(parameterset.etree_repr())
        for substituteset in self._substitutesets.values():
            benchmark_etree.append(substituteset.etree_repr())
        for fileset in self._filesets.values():
            benchmark_etree.append(fileset.etree_repr())
        for patternset in self._patternsets.values():
            benchmark_etree.append(patternset.etree_repr())
        for step in self._steps.values():
            benchmark_etree.append(step.etree_repr())
        for analyser in self._analyser.values():
            benchmark_etree.append(analyser.etree_repr())
        for result_name in self._results_order:
            result = self._results[result_name]
            benchmark_etree.append(result.etree_repr(new_cwd))
        return benchmark_etree

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def _create_all_workpackages(self):
        """Create all workpackages of current benchmark and create graph
        structure."""
        self._workpackages = dict()
        self._work_stat = jube2.util.WorkStat()

        # Create a possible order of execution
        depend_dict = dict()
        for step in self._steps.values():
            depend_dict[step.name] = step.depend
        work_list = jube2.util.resolve_depend(depend_dict)

        # Create workpackages
        for step_name in work_list:
            self._workpackages[step_name] = list()

        for step_name in work_list:
            step = self._steps[step_name]
            parametersets_names = list()

            # Filter for parametersets in uses
            for use in step.use:
                parametersets_names.append([name for name in use
                                            if name in self._parametersets])
            parametersets_names = [names for names in parametersets_names
                                   if bool(names)]

            # Expand uses if needed (to allow <use>setA,setB</use>)
            parametersets_names = [iterator for iterator in
                                   itertools.product(*parametersets_names)]

            for names in parametersets_names:
                self._create_workpackages_for_step(step, names)

    def analyse(self, show_info=True):
        """Run analyser"""

        if show_info:
            LOGGER.info(">>> Start analyse")

        for analyser in self._analyser.values():
            analyser.analyse()
        if not jube2.conf.DEBUG_MODE:
            self.write_analyse_data(os.path.join(self.bench_dir,
                                                 jube2.conf.ANALYSE_FILENAME))
        if show_info:
            LOGGER.info(">>> Analyse finished")

    def create_result(self, only=None, show=False, data_list=None):
        """Show benchmark result"""
        if only is None:
            only = [result_name for result_name in self._results]
        if data_list is None:
            data_list = list()
        for result_name in self._results_order:
            result = self._results[result_name]
            if result.name in only:
                result_data = result.create_result_data()
                if result.result_dir is None:
                    result_dir = os.path.join(self.bench_dir,
                                              jube2.conf.RESULT_DIRNAME)
                else:
                    result_dir = jube2.util.id_dir(result.result_dir,
                                                   self.id)
                if (not os.path.exists(result_dir)) and \
                   (not jube2.conf.DEBUG_MODE):
                    os.makedirs(result_dir)
                if not jube2.conf.DEBUG_MODE:
                    filename = os.path.join(result_dir,
                                            "{0}.dat".format(result.name))
                else:
                    filename = None
                result_data.create_result(show=show, filename=filename)

                if result_data in data_list:
                    data_list[data_list.index(result_data)].add_result_data(
                        result_data)
                else:
                    data_list.append(result_data)
        return data_list

    def update_analyse_and_result(self, new_patternsets, new_analyser,
                                  new_results, new_results_order, new_cwd):
        """Update analyser and result data"""
        if os.path.exists(self.bench_dir):
            LOGGER.debug("Update analyse and result data")
            self._patternsets = new_patternsets
            old_analyser = self._analyser
            self._analyser = new_analyser
            self._results = new_results
            self._results_order = new_results_order
            for analyser in self._analyser.values():
                if analyser.name in old_analyser:
                    analyser.analyse_result = \
                        old_analyser[analyser.name].analyse_result
                analyser.benchmark = self
            for result in self._results.values():
                result.benchmark = self
                # change result dir position relative to cwd
                if (result.result_dir is not None) and \
                   (new_cwd is not None) and \
                   (not os.path.isabs(result.result_dir)):
                    result.result_dir = \
                        os.path.relpath(os.path.join(new_cwd,
                                                     result.result_dir),
                                        self._cwd)
            self.write_benchmark_configuration(
                os.path.join(self.bench_dir,
                             jube2.conf.CONFIGURATION_FILENAME))

    def write_analyse_data(self, filename):
        """All analyse data will be written to given file
        using xml representation"""
        # Create root-tag and append analyser
        analyse_etree = ET.Element("analyse")
        for analyser_name in self._analyser:
            analyser_etree = ET.SubElement(analyse_etree, "analyser")
            analyser_etree.attrib["name"] = analyser_name
            for etree in self._analyser[analyser_name].analyse_etree_repr():
                analyser_etree.append(etree)
        xml = jube2.util.element_tree_tostring(analyse_etree, encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml.encode("UTF-8"))
        fout = open(filename, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))
        fout.close()

    def _create_workpackages_for_step(self, step, parameterset_names):
        """Create all workpackages for given step and create graph
        structure."""
        # Create local parameterset
        LOGGER.debug("Create workpackages for step {0}".format(step.name))
        local_parameterset = jube2.parameter.Parameterset()
        for parameterset_name in parameterset_names:
            # The parametersets in a single step must be compatible
            if not local_parameterset.is_compatible(
                    self._parametersets[parameterset_name]):
                incompatible_names = \
                    local_parameterset.get_incompatible_parameter(
                        self._parametersets[parameterset_name])
                raise ValueError(("Can't use parameterset '{0}' in " +
                                  "step '{1}'.\nParameter '{2}' is/are " +
                                  "already defined by a different " +
                                  "parameterset.")
                                 .format(parameterset_name, step.name,
                                         ",".join(incompatible_names)))
            local_parameterset.add_parameterset(
                self._parametersets[parameterset_name])

        parent_names = [name for name in step.depend]

        # Parent workpackages must be exist
        for parent_name in parent_names:
            if (parent_name not in self._workpackages) or \
               (len(self._workpackages[parent_name]) == 0):
                raise ValueError(("Depend '{0}' for step '{1}' not " +
                                  "found.").format(parent_name, step.name))

        parent_workpackages = [self._workpackages[parent_name]
                               for parent_name in parent_names]
        # Create all parent combinations
        parent_workpackages_comb = \
            [iterator for iterator in itertools.product(*parent_workpackages)]

        # Every possible parent combination results in a new
        # parameterset
        for parent_workpackages in parent_workpackages_comb:
            history_parameterset = local_parameterset.copy()

            # Check compatibility of parametersets
            compatible = True
            i = 0
            while (i < len(parent_workpackages)) and compatible:
                compatible = history_parameterset.is_compatible(
                    parent_workpackages[i].history)
                if compatible:
                    history_parameterset.add_parameterset(
                        parent_workpackages[i].history)
                i = i + 1

            if compatible:
                # Expand templates
                parametersets = [parameterset for parameterset in
                                 history_parameterset.expand_templates()]

                # Parameter substitution and expand generated templates
                change = True

                # Get jube internal parametersets
                jube_parameterset = self.get_jube_parameterset()
                jube_parameterset.add_parameterset(
                    step.get_jube_parameterset())

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

                for parameterset in parametersets:
                    workpackage_parameterset = local_parameterset.copy()
                    workpackage_parameterset.update_parameterset(parameterset)

                    # Create new workpackage
                    for iteration in range(step.iterations):
                        workpackage = jube2.workpackage.Workpackage(
                            benchmark=self,
                            step=step,
                            parameterset=workpackage_parameterset.copy(),
                            history=parameterset.copy(),
                            iteration=iteration)

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

                        # Update history parameterset
                        workpackage.history.update_parameterset(
                            workpackage.parameterset)

                        # Create links
                        for parent in parent_workpackages:
                            workpackage.add_parent(parent)
                            parent.add_children(workpackage)
                        self._workpackages[step.name].append(workpackage)
                        if len(workpackage.parents) == 0:
                            workpackage.queued = True
                            self._work_stat.put(workpackage)
            else:
                LOGGER.debug("Incompatible parameterset combination found " +
                             "between current and parent steps.")

    def new_run(self):
        """Create workpackage structure and run benchmark"""
        # Check benchmark consistency
        jube2.util.consistency_check(self)

        # Create benchmark directory
        self._create_bench_dir()

        # Change logfile
        jube2.log.change_logfile_name(os.path.join(
            self.bench_dir, jube2.conf.LOGFILE_RUN_NAME))

        # Reset Workpackage counter
        jube2.workpackage.Workpackage.id_counter = 0

        # Create all workpackages
        self._create_all_workpackages()

        # Store workpackage information
        self.write_workpackage_information(
            os.path.join(self.bench_dir, jube2.conf.WORKPACKAGES_FILENAME))

        self.run()

    def run(self):
        """Run benchmark"""
        title = "benchmark: {0}".format(self._name)
        if jube2.conf.DEBUG_MODE:
            title += " ---DEBUG_MODE---"
        title += "\n\n{0}".format(self._comment)
        infostr = jube2.util.text_boxed(title)
        LOGGER.info(infostr)

        if not jube2.conf.HIDE_ANIMATIONS:
            print("\nRunning workpackages (#=done, 0=wait):")
            status = self.benchmark_status
            jube2.util.print_loading_bar(status["done"], status["all"],
                                         status["wait"])

        # Handle all workpackages in given order
        while not self._work_stat.empty():
            workpackage = self._work_stat.get()
            if not workpackage.done:
                workpackage.run()
                if workpackage.done:
                    # Store workpackage information
                    self.write_workpackage_information(
                        os.path.join(self.bench_dir,
                                     jube2.conf.WORKPACKAGES_FILENAME))
            # Update queues (move waiting workpackages to work queue
            # if possible)
            self._work_stat.update_queues(workpackage)
            if not jube2.conf.HIDE_ANIMATIONS:
                status = self.benchmark_status
                jube2.util.print_loading_bar(status["done"], status["all"],
                                             status["wait"])
            workpackage.queued = False
            for mode in ("only_started", "all"):
                for child in workpackage.children:
                    all_done = True
                    for parent in child.parents:
                        all_done = all_done and parent.done
                    if all_done:
                        if (mode == "only_started" and child.started) or \
                           (mode == "all" and (not child.queued)):
                            child.queued = True
                            self._work_stat.put(child)
        print("\n")

        status_data = [("stepname", "all", "open", "wait", "done")]
        status_data += [(stepname, str(_status["all"]), str(_status["open"]),
                         str(_status["wait"]), str(_status["done"]))
                        for stepname, _status in
                        self.workpackage_status.items()]
        LOGGER.info(jube2.util.text_table(status_data, use_header_line=True,
                                          indent=2))

        LOGGER.info("\n>>>> Benchmark information and " +
                    "further useful commands:")
        LOGGER.info(">>>>       id: {0}".format(self._id))
        path = os.path.relpath(os.path.join(self._cwd, self._outpath),
                               self._org_cwd)
        LOGGER.info(">>>>      dir: {0}".format(path))

        # Store workpackage information
        self.write_workpackage_information(
            os.path.join(self.bench_dir, jube2.conf.WORKPACKAGES_FILENAME))

        status = self.benchmark_status
        if status["all"] != status["done"]:
            LOGGER.info((">>>> continue: jube continue {0} " +
                         "--id {1}").format(path, self._id))
        LOGGER.info((">>>>  analyse: jube analyse {0} " +
                     "--id {1}").format(path, self._id))
        LOGGER.info((">>>>   result: jube result {0} " +
                     "--id {1}").format(path, self._id))
        LOGGER.info((">>>>     info: jube info {0} " +
                     "--id {1}").format(path, self._id))
        LOGGER.info((">>>>      log: jube log {0} " +
                     "--id {1}").format(path, self._id))
        LOGGER.info(jube2.util.text_line() + "\n")

    def _create_bench_dir(self):
        """Create the directory for a benchmark."""
        # Check if outpath exists
        if not (os.path.exists(self._outpath) and
                os.path.isdir(self._outpath)):
            os.makedirs(self._outpath)
        # Generate unique ID in outpath
        if self._id < 0:
            self._id = jube2.util.get_current_id(self._outpath) + 1
        if os.path.exists(self.bench_dir):
            raise RuntimeError("Benchmark directory \"{0}\" already exist"
                               .format(os.path.relpath(
                                   os.path.join(self._cwd, self.bench_dir),
                                   self._org_cwd)))
        os.makedirs(self.bench_dir)
        self.write_benchmark_configuration(
            os.path.join(self.bench_dir, jube2.conf.CONFIGURATION_FILENAME))
        jube2.util.update_timestamps(os.path.join(self.bench_dir,
                                                  jube2.conf.TIMESTAMPS_INFO),
                                     "start", "change")

    def write_benchmark_configuration(self, filename):
        """The current benchmark configuration will be written to given file
        using xml representation"""
        # Create root-tag and append single benchmark
        benchmarks_etree = ET.Element("jube")

        # Store tag information
        if len(self._tags) > 0:
            selection_etree = ET.SubElement(benchmarks_etree, "selection")
            for tag in self._tags:
                tag_etree = ET.SubElement(selection_etree, "tag")
                tag_etree.text = tag

        benchmarks_etree.append(self.etree_repr(new_cwd=self.bench_dir))
        xml = jube2.util.element_tree_tostring(benchmarks_etree,
                                               encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml.encode('UTF-8'))
        fout = open(filename, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))
        fout.close()

    def reset_all_workpackages(self):
        """Reset workpackage state"""
        for workpackages in self._workpackages.values():
            for workpackage in workpackages:
                workpackage.done = False

    def write_workpackage_information(self, filename):
        """All workpackage information will be written to given file
        using xml representation"""
        # Create root-tag and append workpackages
        workpackages_etree = ET.Element("workpackages")
        for workpackages in self._workpackages.values():
            for workpackage in workpackages:
                workpackages_etree.append(workpackage.etree_repr())
        xml = jube2.util.element_tree_tostring(workpackages_etree,
                                               encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml.encode("UTF-8"))
        fout = open(filename, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))
        fout.close()

    def set_workpackage_information(self, workpackages, work_stat):
        """Set new workpackage information"""
        self._workpackages = workpackages
        self._work_stat = work_stat

    @property
    def bench_dir(self):
        """Return benchmark directory"""
        return jube2.util.id_dir(self._outpath, self._id)
