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
"""Syslogtype definition"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

from jube2.result_types.keyvaluesresult import KeyValuesResult
from jube2.result import Result
import xml.etree.ElementTree as ET
import jube2.log
import jube2.conf
import logging.handlers

LOGGER = jube2.log.get_logger(__name__)


class SysloggedResult(KeyValuesResult):

    """A result that gets sent to syslog."""

    class SyslogData(KeyValuesResult.KeyValuesData):

        """Table data"""

        def __init__(self, name_or_other, syslog_address=None,
                     syslog_host=None, syslog_port=None,
                     syslog_fmt_string=None):
            if type(name_or_other) is KeyValuesResult.KeyValuesData:
                self._name = name_or_other.name
                self._keys = name_or_other.keys
                self._data = name_or_other.data
                self._benchmark_ids = name_or_other.benchmark_ids
            else:
                KeyValuesResult.KeyValuesData.__init__(self, name_or_other)
            self._syslog_address = syslog_address
            self._syslog_host = syslog_host
            self._syslog_port = syslog_port
            self._syslog_fmt_string = syslog_fmt_string

        def create_result(self, show=True, filename=None, **kwargs):
            """Create result output"""
            # If there are multiple benchmarks, add benchmark id information
            if len(set(self._benchmark_ids)) > 1:
                self.add_id_information(reverse=kwargs.get("reverse", False))

            if self._syslog_address is not None:
                address = self._syslog_address
            else:
                address = (self._syslog_host, self._syslog_port)

            handler = logging.handlers.SysLogHandler(
                address=address,
                facility=logging.handlers.SysLogHandler.LOG_USER
            )
            handler.setFormatter(logging.Formatter(
                fmt=self._syslog_fmt_string))

            # get logger
            log = logging.getLogger("jube")
            log.setLevel(logging.INFO)
            log.addHandler(handler)

            # create log output
            for dataset in self.data:
                entry = list()
                for i, key in enumerate(self.keys):
                    entry.append("{0}={1}".format(key.name, dataset[i]))
                # Log result
                if show:
                    if not jube2.conf.DEBUG_MODE:
                        log.info(" ".join(entry))
                    LOGGER.debug("Logged: {0}\n".format(" ".join(entry)))

            # remove handler to avoid double logging
            log.removeHandler(handler)

    def __init__(self, name, syslog_address=None, syslog_host=None,
                 syslog_port=None, syslog_fmt_string=None, sort_names=None,
                 res_filter=None):
        KeyValuesResult.__init__(self, name, sort_names, res_filter)
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
        if syslog_fmt_string is None:
            self._syslog_fmt_string = jube2.conf.SYSLOG_FMT_STRING
        else:
            self._syslog_fmt_string = syslog_fmt_string

    def create_result_data(self):
        """Create result data"""
        result_data = KeyValuesResult.create_result_data(self)
        return SysloggedResult.SyslogData(result_data, self._syslog_address,
                                          self._syslog_host, self._syslog_port,
                                          self._syslog_fmt_string)

    def etree_repr(self):
        """Return etree object representation"""
        result_etree = Result.etree_repr(self)
        syslog_etree = ET.SubElement(result_etree, "syslog")
        syslog_etree.attrib["name"] = self._name
        if self._syslog_address is not None:
            syslog_etree.attrib["address"] = self._syslog_address
        if self._syslog_host is not None:
            syslog_etree.attrib["host"] = self._syslog_host
        if self._syslog_port is not None:
            syslog_etree.attrib["port"] = self._syslog_port
        if self._syslog_fmt_string is not None:
            syslog_etree.attrib["format"] = self._syslog_fmt_string
        if self._res_filter is not None:
            syslog_etree.attrib["filter"] = self._res_filter
        if len(self._sort_names) > 0:
            syslog_etree.attrib["sort"] = \
                jube2.conf.DEFAULT_SEPARATOR.join(self._sort_names)
        for key in self._keys:
            syslog_etree.append(key.etree_repr())
        return result_etree
