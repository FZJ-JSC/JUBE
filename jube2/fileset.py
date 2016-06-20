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
"""Fileset related classes"""

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
               environment=None, file_path_ref=""):
        """Copy/load/prepare all files in fileset"""
        for file_handle in self:
            if type(file_handle) is Prepare:
                file_handle.execute(
                    parameter_dict=parameter_dict,
                    work_dir=alt_work_dir if alt_work_dir
                    is not None else work_dir,
                    environment=environment)
            else:
                file_handle.create(
                    work_dir=work_dir, parameter_dict=parameter_dict,
                    alt_work_dir=alt_work_dir, file_path_ref=file_path_ref,
                    environment=environment)


class File(object):

    """Generic file access"""

    def __init__(self, path, name=None, is_internal_ref=False):
        self._path = path
        self._name = name
        self._file_path_ref = ""
        self._is_internal_ref = is_internal_ref

    def create(self, work_dir, parameter_dict, alt_work_dir=None,
               file_path_ref="", environment=None):
        """Create file access"""
        pathname = jube2.util.substitution(self._path, parameter_dict)
        pathname = os.path.expanduser(pathname)
        if environment is not None:
            pathname = jube2.util.substitution(pathname, environment)
        else:
            pathname = os.path.expandvars(pathname)
        if self._is_internal_ref:
            pathname = os.path.join(work_dir, pathname)
        else:
            pathname = os.path.join(self._file_path_ref, pathname)
            pathname = os.path.join(file_path_ref, pathname)
            pathname = os.path.normpath(pathname)
        if self._name is None:
            name = os.path.basename(pathname)
        else:
            name = jube2.util.substitution(self._name, parameter_dict)
        if alt_work_dir is not None:
            work_dir = alt_work_dir
        # Shell expansion
        pathes = glob.glob(pathname)
        if (len(pathes) == 0) and (not jube2.conf.DEBUG_MODE):
            raise RuntimeError("no files found using \"{0}\""
                               .format(pathname))
        for path in pathes:
            # When using shell extensions, alternative filenames are not
            # allowed for multiple matches.
            if (len(pathes) > 1) or ((pathname != path) and
                                     (name == os.path.basename(pathname))):
                name = os.path.basename(path)
            new_file_path = os.path.join(work_dir, name)
            self.create_action(path, name, new_file_path)

    def create_action(self, path, name, new_file_path):
        """File access type specific creation"""
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

    def create_action(self, path, name, new_file_path):
        """Create link to file in work_dir"""
        # Manipulate target_path if a new relative name path was selected
        if os.path.isabs(path):
            target_path = path
        else:
            target_path = os.path.relpath(path, os.path.dirname(new_file_path))
        LOGGER.debug("  link \"{0}\" <- \"{1}\"".format(target_path, name))
        if not jube2.conf.DEBUG_MODE and not os.path.exists(new_file_path):
            os.symlink(target_path, new_file_path)

    def etree_repr(self):
        """Return etree object representation"""
        link_etree = ET.Element("link")
        link_etree.text = self._path
        if self._name is not None:
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

    def create_action(self, path, name, new_file_path):
        """Copy file/directory to work_dir"""
        LOGGER.debug("  copy \"{0}\" -> \"{1}\"".format(path, name))
        if not jube2.conf.DEBUG_MODE and not os.path.exists(new_file_path):
            if os.path.isdir(path):
                shutil.copytree(path, new_file_path, symlinks=True)
            else:
                shutil.copy2(path, new_file_path)

    def etree_repr(self):
        """Return etree object representation"""
        copy_etree = ET.Element("copy")
        copy_etree.text = self._path
        if self._name is not None:
            copy_etree.attrib["name"] = self._name
        if self._is_internal_ref:
            copy_etree.attrib["rel_path_ref"] = "internal"
        if self._file_path_ref != "":
            copy_etree.attrib["file_path_ref"] = self._file_path_ref
        return copy_etree


class Prepare(jube2.step.Operation):

    """Prepare the workpackage work directory"""

    def __init__(self, cmd, stdout_filename=None, stderr_filename=None,
                 work_dir=None):
        jube2.step.Operation.__init__(self,
                                      do=cmd,
                                      stdout_filename=stdout_filename,
                                      stderr_filename=stderr_filename,
                                      work_dir=work_dir)

    def execute(self, parameter_dict, work_dir, only_check_pending=False,
                environment=None):
        """Execute the prepare command"""
        jube2.step.Operation.execute(
            self, parameter_dict=parameter_dict, work_dir=work_dir,
            only_check_pending=only_check_pending, environment=environment)

    def etree_repr(self):
        """Return etree object representation"""
        do_etree = ET.Element("prepare")
        do_etree.text = self._do
        if self._stdout_filename is not None:
            do_etree.attrib["stdout"] = self._stdout_filename
        if self._stderr_filename is not None:
            do_etree.attrib["stderr"] = self._stderr_filename
        if self._work_dir is not None:
            do_etree.attrib["work_dir"] = self._work_dir
        return do_etree
