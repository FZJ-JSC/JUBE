"""Fileset related classes"""

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

import os
import shutil
import xml.etree.ElementTree as ET
import jube2.util
import jube2.conf
import jube2.step
import jube2.log
import glob

LOGGER = jube2.log.get_logger(__name__)


class Fileset(list):

    """Container for file copy, link and prepare operations"""

    def __init__(self, name):
        list.__init__(self)
        self._name = name

    @property
    def name(self):
        """Return fileset name"""
        return self._name

    def etree_repr(self):
        """Return etree object representation"""
        fileset_etree = ET.Element("fileset")
        fileset_etree.attrib["name"] = self._name
        for file_handle in self:
            fileset_etree.append(file_handle.etree_repr())
        return fileset_etree

    def create(self, work_dir, parameter_dict, alt_work_dir=None,
               export_parameter_dict=None, file_path_ref=""):
        """Copy/load/prepare all files in fileset"""
        for file_handle in self:
            if type(file_handle) is Prepare:
                file_handle.execute(
                    parameter_dict=parameter_dict,
                    work_dir=alt_work_dir if alt_work_dir
                    is not None else work_dir,
                    export_parameter_dict=export_parameter_dict)
            else:
                file_handle.create(
                    work_dir=work_dir, parameter_dict=parameter_dict,
                    alt_work_dir=alt_work_dir, file_path_ref=file_path_ref)


class File(object):

    """Generic file access"""

    def __init__(self, path, name, is_internal_ref=False):
        self._path = path
        self._name = name
        self._file_path_ref = ""
        self._is_internal_ref = is_internal_ref

    def create(self, work_dir, parameter_dict, alt_work_dir=None,
               file_path_ref=""):
        """Create file access"""
        raise NotImplementedError()

    def etree_repr(self):
        """Return etree object representation"""
        raise NotImplementedError()

    @property
    def path(self):
        """Return filepath"""
        return self._path

    @property
    def file_path_ref(self):
        """Get file path reference"""
        return self._file_path_ref

    @file_path_ref.setter
    def file_path_ref(self, file_path_ref):
        """Set file path reference"""
        self._file_path_ref = file_path_ref

    @property
    def is_internal_ref(self):
        """Return path is internal ref"""
        return self._is_internal_ref

    def __repr__(self):
        return self._path


class Link(File):

    """A link to a given path. Which can be used inside steps."""

    def create(self, work_dir, parameter_dict, alt_work_dir=None,
               file_path_ref=""):
        """Create link to file in work_dir"""
        path = jube2.util.substitution(self._path, parameter_dict)
        path = os.path.expandvars(os.path.expanduser(path))
        name = jube2.util.substitution(self._name, parameter_dict)
        if self._is_internal_ref:
            path = os.path.join(work_dir, path)
        else:
            path = os.path.join(self._file_path_ref, path)
            path = os.path.join(file_path_ref, path)
            path = os.path.normpath(path)
        if (not os.path.exists(path)) and (not jube2.conf.DEBUG_MODE):
            raise RuntimeError("'{}' not found".format(path))
        if alt_work_dir is not None:
            work_dir = alt_work_dir
        target_path = os.path.relpath(path, work_dir)
        link_path = os.path.join(work_dir, name)
        LOGGER.debug("  link \"{0}\" <- \"{1}\"".format(path, name))
        if not jube2.conf.DEBUG_MODE and not os.path.exists(link_path):
            os.symlink(target_path, link_path)

    def etree_repr(self):
        """Return etree object representation"""
        link_etree = ET.Element("link")
        link_etree.text = self._path
        link_etree.attrib["name"] = self._name
        if self._is_internal_ref:
            link_etree.attrib["rel_path_ref"] = "internal"
        if self._file_path_ref != "":
            link_etree.attrib["file_path_ref"] = self._file_path_ref
        return link_etree


class Copy(File):

    """A file or directory given by path. Which can be copied to the work_dir
    inside steps.
    """

    def create(self, work_dir, parameter_dict, alt_work_dir=None,
               file_path_ref="."):
        """Copy file/directory to work_dir"""
        pathname = jube2.util.substitution(self._path, parameter_dict)
        pathname = os.path.expandvars(os.path.expanduser(pathname))
        name = jube2.util.substitution(self._name, parameter_dict)
        if self._is_internal_ref:
            pathname = os.path.join(work_dir, pathname)
        else:
            pathname = os.path.join(self._file_path_ref, pathname)
            pathname = os.path.join(file_path_ref, pathname)
            pathname = os.path.normpath(pathname)
        if alt_work_dir is not None:
            work_dir = alt_work_dir
        pathes = glob.glob(pathname)
        if len(pathes) == 0:
            LOGGER.debug("no files found using \"{}\"".format(pathname))
        for path in pathes:
            if len(pathes) > 1:
                file_path = os.path.join(work_dir, os.path.basename(path))
                LOGGER.debug("  copy \"{0}\" -> \"{1}\""
                             .format(path, os.path.basename(path)))
            else:
                file_path = os.path.join(work_dir, name)
                LOGGER.debug("  copy \"{0}\" -> \"{1}\"".format(path, name))
            if not jube2.conf.DEBUG_MODE and not os.path.exists(file_path):
                if os.path.isdir(path):
                    shutil.copytree(path, file_path, symlinks=True)
                else:
                    shutil.copyfile(path, file_path)
                    # Copy filemode
                    shutil.copymode(path, file_path)

    def etree_repr(self):
        """Return etree object representation"""
        copy_etree = ET.Element("copy")
        copy_etree.text = self._path
        copy_etree.attrib["name"] = self._name
        if self._is_internal_ref:
            copy_etree.attrib["rel_path_ref"] = "internal"
        return copy_etree


class Prepare(jube2.step.Operation):

    """Prepare the workpackage work directory"""

    def __init__(self, cmd, stdout_filename=None, stderr_filename=None):
        jube2.step.Operation.__init__(self,
                                      do=cmd,
                                      stdout_filename=stdout_filename,
                                      stderr_filename=stderr_filename)

    def execute(self, parameter_dict, work_dir, export_parameter_dict=None):
        """Execute the prepare command"""
        jube2.step.Operation.execute(
            self, parameter_dict=parameter_dict, work_dir=work_dir,
            export_parameter_dict=export_parameter_dict)

    def etree_repr(self):
        """Return etree object representation"""
        do_etree = ET.Element("prepare")
        do_etree.text = self._do
        if self._stdout_filename is not None:
            do_etree.attrib["stdout"] = self._stdout_filename
        if self._stderr_filename is not None:
            do_etree.attrib["stderr"] = self._stderr_filename
        return do_etree
