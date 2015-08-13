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
"""Syslogtype definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

from jube2.result_types.keyvaluesresult import KeyValuesResult
from jube2.result import Result
import xml.etree.ElementTree as ET
import jube2.log

LOGGER = jube2.log.get_logger(__name__)


class SysloggedResult(KeyValuesResult):

    """A result that gets sent to syslog."""

    def __init__(self, name, syslog_address=None, syslog_host=None,
                 syslog_port=None, sort_names=None, file_path_ref=None):
        KeyValuesResult.__init__(self, name, sort_names)
        if (syslog_address is None) and (syslog_host is None) and \
                (syslog_port is None):
            raise IOError("Neither a syslog address nor a hostname port " +
                          "combination specified.")
        if (syslog_host is not None) and (syslog_address is not None):
            raise IOError("Please specify a syslog address or a hostname, " +
                          "not both at the same time.")
        if (syslog_host is not None) and (syslog_port is None):
            self._syslog_port = 514
        self._syslog_address = syslog_address
        self._syslog_host = syslog_host
        self._syslog_port = syslog_port
        self._file_path_ref = file_path_ref

    def etree_repr(self):
        """Return etree object representation"""
        result_etree = Result.etree_repr(self)
        syslog_etree = ET.SubElement(result_etree, "syslog")
        syslog_etree.attrib["name"] = self._name
        if self._syslog_address is not None:
            syslog_etree.attrib["address"] = self._syslog_address
        if self._syslog_address is not None:
            syslog_etree.attrib["host"] = self._syslog_host
        if self._syslog_address is not None:
            syslog_etree.attrib["port"] = self._syslog_port
        if len(self._sort_names) > 0:
            syslog_etree.attrib["sort"] = \
                jube2.conf.DEFAULT_SEPARATOR.join(self._sort_names)
        for key in self._keys:
            syslog_etree.append(key.etree_repr())
        return result_etree
