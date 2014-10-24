"""The Benchmark class manages the benchmark process"""

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
import xml.dom.minidom as DOM
import os
import pprint
import shutil
import itertools
try:
    import queue
except ImportError:
    import Queue as queue
import jube2.parameter
import jube2.workpackage
import jube2.util
import logging

logger = logging.getLogger(__name__)


class Benchmark(object):

    """The Benchmark class contains all data to run a benchmark"""

    def __init__(self, name, outpath, parametersets, substitutesets,
                 filesets, patternsets, steps, analyzer, results, comment=""):
        self._name = name
        self._outpath = outpath
        self._parametersets = parametersets
        self._substitutesets = substitutesets
        self._filesets = filesets
        self._patternsets = patternsets
        self._steps = steps
        self._analyzer = analyzer
        for analyzer in self._analyzer.values():
            analyzer.benchmark = self
        self._results = results
        for result in self._results.values():
            result.benchmark = self
        self._workpackages = dict()
        self._work_list = queue.Queue()
        self._comment = comment
        self._id = -1
        self._org_cwd = "."
        self._cwd = "."

    @property
    def name(self):
        """Return benchmark name"""
        return self._name

    @property
    def comment(self):
        """Return comment string"""
        return self._comment

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
    def analyzer(self):
        """Return analyzer"""
        return self._analyzer

    @property
    def results(self):
        """Return results"""
        return self._results

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
    def substitutesets(self):
        """Return substitutesets"""
        return self._substitutesets

    @property
    def workpackages(self):
        """Return workpackages"""
        return self._workpackages

    @property
    def work_list(self):
        """Return work queue"""
        return self._work_list

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
        return parameterset

    def etree_repr(self, new_cwd=None):
        """Return etree object representation"""
        benchmark_etree = ET.Element("benchmark")
        if len(self._comment) > 0:
            comment_element = ET.SubElement(benchmark_etree, "comment")
            comment_element.text = self._comment
        benchmark_etree.attrib["name"] = self._name
        if (new_cwd is not None) and (not os.path.isabs(self._outpath)):
            benchmark_etree.attrib["outpath"] = os.path.relpath(self._outpath,
                                                                new_cwd)
        else:
            benchmark_etree.attrib["outpath"] = self._outpath
        for parameterset in self._parametersets.values():
            benchmark_etree.append(parameterset.etree_repr())
        for substituteset in self._substitutesets.values():
            benchmark_etree.append(substituteset.etree_repr())
        for fileset_name in self._filesets:
            fileset_etree = ET.SubElement(benchmark_etree, "fileset")
            fileset_etree.attrib["name"] = fileset_name
            for file_handle in self._filesets[fileset_name]:
                fileset_etree.append(file_handle.etree_repr(new_cwd))
        for patternset in self._patternsets.values():
            benchmark_etree.append(patternset.etree_repr())
        for step in self._steps.values():
            benchmark_etree.append(step.etree_repr(new_cwd))
        for analyzer in self._analyzer.values():
            benchmark_etree.append(analyzer.etree_repr())
        for result in self._results.values():
            benchmark_etree.append(result.etree_repr(new_cwd))
        return benchmark_etree

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def _create_all_workpackages(self):
        """Create all workpackages of current benchmark and create graph
        structure."""
        self._workpackages = dict()
        self._work_list = queue.Queue()

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
            logger.info(">>> Start analyse")

        for analyser in self._analyzer.values():
            analyser.analyse()
        if not jube2.util.DEBUG_MODE:
            self.write_analyse_data(os.path.join(self.bench_dir,
                                                 jube2.util.ANALYSE_FILENAME))
        if show_info:
            logger.info(">>> Analyse finished")

    def create_result(self, only=None):
        """Show benchmark result"""
        if only is None:
            only = [result_name for result_name in self._results]
        for result in self._results.values():
            if result.name in only:
                result_str = result.create_result()
                if result.result_dir is None:
                    result_dir = os.path.join(self.bench_dir,
                                              jube2.util.RESULT_DIRNAME)
                else:
                    result_dir = jube2.util.id_dir(result.result_dir, self.id)
                if (not os.path.exists(result_dir)) and \
                   (not jube2.util.DEBUG_MODE):
                    os.makedirs(result_dir)
                logger.info(result_str)
                logger.info("\n")
                if not jube2.util.DEBUG_MODE:
                    file_handle = \
                        open(os.path.join(result_dir,
                                          "{}.dat".format(result.name)), "w")
                    file_handle.write(result_str)
                    file_handle.close()

    def update_analyse_and_result(self, new_patternsets, new_analyzer,
                                  new_results, new_cwd):
        """Update analyzer and result data"""
        if os.path.exists(self.bench_dir):
            logger.debug("Update analyse and result data")
            self._patternsets = new_patternsets
            old_analyzer = self._analyzer
            self._analyzer = new_analyzer
            self._results = new_results
            for analyzer in self._analyzer.values():
                if analyzer.name in old_analyzer:
                    analyzer.analyse_result = \
                        old_analyzer[analyzer.name].analyse_result
                analyzer.benchmark = self
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
                             jube2.util.CONFIGURATION_FILENAME))

    def write_analyse_data(self, filename):
        """All analyse data will be written to given file
        using xml representation"""
        # Create root-tag and append analyzer
        analyse_etree = ET.Element("analyse")
        for analyzer_name in self._analyzer:
            analyzer_etree = ET.SubElement(analyse_etree, "analyzer")
            analyzer_etree.attrib["name"] = analyzer_name
            for etree in self._analyzer[analyzer_name].analyse_etree_repr():
                analyzer_etree.append(etree)
        xml = ET.tostring(analyse_etree, encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml)
        fout = open(filename, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))
        fout.close()

    def _create_workpackages_for_step(self, step, parameterset_names):
        """Create all workpackages for given step and create graph
        structure."""
        # Create local parameterset
        logger.debug("Create workpackages for step {}".format(step.name))
        local_parameterset = jube2.parameter.Parameterset()
        for parameterset_name in parameterset_names:
            # The parametersets in a single step must be compatible
            if not local_parameterset.is_compatible(
                    self._parametersets[parameterset_name]):
                raise ValueError(("Can't use parameterset '{0}' in " +
                                  "step '{1}'.")
                                 .format(parameterset_name, step.name))
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

                        # Create links
                        for parent in parent_workpackages:
                            workpackage.add_parent(parent)
                            parent.add_children(workpackage)
                        self._workpackages[step.name].append(workpackage)
                        if len(workpackage.parents) == 0:
                            workpackage.queued = True
                            self._work_list.put(workpackage)
            else:
                logger.debug("Incompatible parameterset combination found " +
                             "between current and parent steps.")

    def new_run(self):
        """Create workpackage structure and run benchmark"""
        # Check benchmark consistency
        jube2.util.consistency_check(self)

        # Create benchmark directory
        self._create_bench_dir()

        # Reset Workpackage counter
        jube2.workpackage.Workpackage.id_counter = 0

        # Create all workpackages
        self._create_all_workpackages()

        # Store workpackage information
        self.write_workpackage_information(
            os.path.join(self.bench_dir, jube2.util.WORKPACKAGES_FILENAME))

        self.run()

    def run(self):
        """Run benchmark"""
        title = "benchmark: {0}".format(self._name)
        if jube2.util.DEBUG_MODE:
            title += " ---DEBUG_MODE---"
        title += "\n\n{}".format(self._comment)
        infostr = jube2.util.boxed(title)
        logger.info(infostr)

        # Handle all workpackages in given order
        while not self._work_list.empty():
            workpackage = self._work_list.get_nowait()
            workpackage.run()
            workpackage.queued = False
            for child in workpackage.children:
                all_done = True
                for parent in child.parents:
                    all_done = all_done and parent.done
                if all_done:
                    child.queued = True
                    self._work_list.put(child)

        infostr = "\n>>>> Benchmark information and further useful commands:"
        logger.info(infostr)

        infostr = ">>>>       id: {0}".format(self._id)
        logger.info(infostr)
        path = os.path.relpath(os.path.join(self._cwd, self._outpath),
                               self._org_cwd)
        infostr = ">>>>      dir: {0}".format(path)
        logger.info(infostr)
        all_done = True
        for step in self._workpackages:
            for workpackage in self._workpackages[step]:
                all_done = all_done and workpackage.done

        # Store workpackage information
        self.write_workpackage_information(
            os.path.join(self.bench_dir, jube2.util.WORKPACKAGES_FILENAME))

        if not all_done:
            infostr = (">>>> continue: jube continue {0} " +
                       "--id {1}").format(path, self._id)
            logger.info(infostr)
        infostr = (">>>>  analyse: jube analyse {0} " +
                   "--id {1}").format(path, self._id)
        logger.info(infostr)
        infostr = (">>>>   result: jube result {0} " +
                   "--id {1}").format(path, self._id)
        logger.info(infostr)
        infostr = (">>>>     info: jube info {0} " +
                   "--id {1}").format(path, self._id)
        logger.info(infostr)
        infostr = jube2.util.line()
        logger.info(infostr + "\n")

    def _create_bench_dir(self):
        """Create the directory for a benchmark."""
        # Check if outpath exists
        if not (os.path.exists(self._outpath) and
                os.path.isdir(self._outpath)):
            os.mkdir(self._outpath)
        # Generate unique ID in outpath
        self._id = jube2.util.get_current_id(self._outpath) + 1
        os.makedirs(self.bench_dir)
        self.write_benchmark_configuration(
            os.path.join(self.bench_dir, jube2.util.CONFIGURATION_FILENAME))

    def write_benchmark_configuration(self, filename):
        """The current benchmark configuration will be written to given file
        using xml representation"""
        # Create root-tag and append single benchmark
        benchmarks_etree = ET.Element("benchmarks")
        benchmarks_etree.append(self.etree_repr(new_cwd=self.bench_dir))
        xml = ET.tostring(benchmarks_etree, encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml)
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
        xml = ET.tostring(workpackages_etree, encoding="UTF-8")
        # Using dom for pretty-print
        dom = DOM.parseString(xml)
        fout = open(filename, "wb")
        fout.write(dom.toprettyxml(indent="  ", encoding="UTF-8"))
        fout.close()

    def set_workpackage_information(self, workpackages, work_list):
        """Set new workpackage information"""
        self._workpackages = workpackages
        self._work_list = work_list

    @property
    def bench_dir(self):
        """Return benchmark directory"""
        return jube2.util.id_dir(self._outpath, self._id)
