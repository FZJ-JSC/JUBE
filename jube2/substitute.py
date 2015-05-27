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
"""Substitution related classes"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import os
import jube2.util
import jube2.conf
import xml.etree.ElementTree as ET
import jube2.log
import shutil
import codecs

LOGGER = jube2.log.get_logger(__name__)


class Substituteset(object):

    """A Substituteset contains all information"""

    def __init__(self, name, file_dict, substitute_dict):
        self._name = name
        self._file_dict = file_dict
        self._substitute_dict = substitute_dict

    @property
    def name(self):
        """Return name of Substituteset"""
        return self._name

    def update_files(self, file_dict):
        """Update iofiles"""
        self._file_dict.update(file_dict)

    def update_substitute(self, substitute_dict):
        """Update substitute_dict"""
        self._substitute_dict.update(substitute_dict)

    def substitute(self, parameter_dict=None, work_dir=None):
        """Do substitution. The work_dir can be set to a given context path.
        The parameter_dict used for inline substitution of
        destination-variables."""

        if work_dir is None:
            work_dir = ""

        # Do pre-substitution of source and destination-variables
        if parameter_dict is not None:
            substitute_dict = dict()
            for sub in self._substitute_dict:
                new_source = jube2.util.substitution(sub, parameter_dict)
                new_dest = jube2.util.substitution(self._substitute_dict[sub],
                                                   parameter_dict)
                substitute_dict[new_source] = new_dest
        else:
            substitute_dict = self._substitute_dict

        # Do file substitution
        for outfile_name, infile_name in self._file_dict.items():

            infile = jube2.util.substitution(infile_name,
                                             parameter_dict)
            outfile = jube2.util.substitution(outfile_name,
                                              parameter_dict)

            LOGGER.debug("  substitute {0} -> {1}".format(infile, outfile))

            LOGGER.debug("  substitute:\n" +
                         jube2.util.text_table([("source", "dest")] +
                                               [(source, dest)
                                                for source, dest in
                                                substitute_dict.items()],
                                               use_header_line=True, indent=9,
                                               align_right=False))
            if not jube2.conf.DEBUG_MODE:
                infile = os.path.join(work_dir, infile)
                outfile = os.path.join(work_dir, outfile)
                # Check not existing files
                if not (os.path.exists(infile) and os.path.isfile(infile)):
                    raise RuntimeError(("File \"{0}\" not found while "
                                        "running substitution").format(infile))
                # Read in-file
                file_handle = codecs.open(infile, "r", "utf-8")
                text = file_handle.read()
                file_handle.close()

                # Substitute
                for source, dest in substitute_dict.items():
                    text = text.replace(source, dest)

                # Write out-file
                file_handle = codecs.open(outfile, "w", "utf-8")
                file_handle.write(text)
                file_handle.close()
                if infile != outfile:
                    shutil.copymode(infile, outfile)

    def etree_repr(self):
        """Return etree object representation"""
        substituteset_etree = ET.Element("substituteset")
        substituteset_etree.attrib["name"] = self._name
        for outfile in self._file_dict:
            iofile_etree = ET.SubElement(substituteset_etree, "iofile")
            iofile_etree.attrib["in"] = self._file_dict[outfile]
            iofile_etree.attrib["out"] = outfile
        for source in self._substitute_dict:
            sub_etree = ET.SubElement(substituteset_etree, "sub")
            sub_etree.attrib["source"] = source
            sub_etree.attrib["dest"] = self._substitute_dict[source]
        return substituteset_etree

    def __repr__(self):
        return "Substitute({0})".format(self.__dict__)
