# JUBE Benchmarking Environment
# Copyright (C) 2008-2024
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
import re
import jube2.util.util
import jube2.util.output
import jube2.conf
import xml.etree.ElementTree as ET
import jube2.log
import shutil
import codecs

LOGGER = jube2.log.get_logger(__name__)


class Substituteset(object):

    """A Substituteset contains all information"""

    def __init__(self, name, file_data, substitute_dict):
        self._name = name
        self._files = file_data
        self._substitute_dict = substitute_dict

    @property
    def name(self):
        """Return name of Substituteset"""
        return self._name

    @property
    def files(self):
        """Return iofiles"""
        return self._files

    @property
    def subs(self):
        """Return subs"""
        return self._substitute_dict

    def update_files(self, file_data):
        """Update iofiles"""
        outfiles = set([data[0] for data in self._files])
        for data in file_data:
            if (data[2] == "a") or (data[0] not in outfiles):
                self._files.append(data)
            elif (data[2] == "w"):
                self._files = [fdat for fdat in self._files
                               if fdat[0] != data[0]]
                self._files.append(data)

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
            for name, sub in self._substitute_dict.items():
                new_source = jube2.util.util.substitution(sub.source, parameter_dict)
                new_dest = jube2.util.util.substitution(sub.dest, parameter_dict)
                substitute_dict[new_source] = Sub(new_source, sub.mode, new_dest)
        else:
            substitute_dict = self._substitute_dict

        # Do file substitution
        for data in self._files:
            outfile_name = data[0]
            infile_name = data[1]
            out_mode = data[2]

            infile = jube2.util.util.substitution(infile_name,
                                                  parameter_dict)
            outfile = jube2.util.util.substitution(outfile_name,
                                                   parameter_dict)

            LOGGER.debug("  substitute {0} -> {1}".format(infile, outfile))

            LOGGER.debug("  substitute:\n" +
                         jube2.util.output.text_table(
                             [("source", "dest")] + [(sub.source, sub.dest)
                                                     for sub in
                                                     substitute_dict.values()],
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
                for name, sub in substitute_dict.items():
                    if sub.mode == "text":
                        text = text.replace(sub.source, sub.dest)
                    else:
                        text = re.sub(sub.source, sub.dest, text)

                # Write out-file
                file_handle = codecs.open(outfile, out_mode, "utf-8")
                file_handle.write(text)
                file_handle.close()
                if infile != outfile:
                    shutil.copymode(infile, outfile)

    def etree_repr(self):
        """Return etree object representation"""
        substituteset_etree = ET.Element("substituteset")
        substituteset_etree.attrib["name"] = self._name
        for data in self._files:
            iofile_etree = ET.SubElement(substituteset_etree, "iofile")
            iofile_etree.attrib["in"] = data[1]
            iofile_etree.attrib["out"] = data[0]
            iofile_etree.attrib["out_mode"] = data[2]
        for name, sub in self._substitute_dict.items():
            sub_etree = ET.SubElement(substituteset_etree, "sub")
            sub_etree.attrib["source"] = sub.source
            sub_etree.attrib["mode"] = sub.mode
            sub_etree.text = sub.dest
        return substituteset_etree

    def __repr__(self):
        return "Substitute({0})".format(self.__dict__)
    
class Sub(object):
    def __init__(self, source, sub_mode, dest):
        self._source = source
        self._mode = sub_mode
        self._dest = dest

    @property
    def source(self):
        """Return source of Sub"""
        return self._source

    @property
    def mode(self):
        """Return type of Sub"""
        return self._mode

    @property
    def dest(self):
        """Return dest of Sub"""
        return self._dest

    def __eq__(self, other):
        return self._source == other.source

    def __hash__(self):
        return hash(self._source)
