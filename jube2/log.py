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
"""Logging Support"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import logging
import sys
import glob
import os.path
import jube2.conf


class JubeLogger(logging.getLoggerClass(), object):

    """Overwrite logging to handle multi line messages."""

    def _log(self, level, msg, *args, **kwargs):
        """Log multi line messages each as a separate entry."""
        if hasattr(msg, "splitlines"):
            lines = msg.splitlines()
        else:
            lines = str(msg).splitlines()
        for line in lines:
            super(JubeLogger, self)._log(level, line, *args, **kwargs)

logging.setLoggerClass(JubeLogger)

LOGGING_MODE = jube2.conf.DEFAULT_LOGGING_MODE
LOGFILE_NAME = jube2.conf.DEFAULT_LOGFILE_NAME
CONSOLE_VERBOSE = False


def get_logger(name=None):
    """Return logger given by name"""
    return logging.getLogger(name)


def setup_logging(mode=None, filename=None, verbose=None):
    """Setup the logging configuration.

    Available modes are
      default   log to console and file
      console   only console output

    filename can be given optionally.

    verbose: enable verbose console output

    The setup includes setting the handlers and formatters. Calling
    this function multiple times causes old handlers to be removed
    before new ones are added.

    """
    global LOGGING_MODE, LOGFILE_NAME, CONSOLE_VERBOSE

    # Use debug file name and debug file mode when in debug mode
    if jube2.conf.DEBUG_MODE:
        filename = jube2.conf.LOGFILE_DEBUG_NAME
        mode = "default"
        filemode = jube2.conf.LOGFILE_DEBUG_MODE
    else:
        filemode = "a"

    if mode is None:
        mode = LOGGING_MODE
    else:
        LOGGING_MODE = mode
    if filename is None:
        filename = LOGFILE_NAME
    else:
        LOGFILE_NAME = filename
    if verbose is None:
        verbose = CONSOLE_VERBOSE
    else:
        CONSOLE_VERBOSE = verbose

    # this is needed to make the other handlers accept on low priority
    # events
    _logger = get_logger("jube2")
    _logger.setLevel(logging.DEBUG)

    # list is needed since we remove from the list we just iterate
    # over
    for handler in list(_logger.handlers):
        handler.close()
        _logger.removeHandler(handler)

    # create, configure and add console handler
    console_formatter = logging.Formatter(jube2.conf.LOG_CONSOLE_FORMAT)
    console_handler = logging.StreamHandler(sys.stdout)
    if verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    if mode == "default":
        try:
            # create, configure and add file handler
            file_formatter = logging.Formatter(jube2.conf.LOG_FILE_FORMAT)
            file_handler = logging.FileHandler(filename, filemode)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            _logger.addHandler(file_handler)
        except IOError:
            pass


def search_for_logs(path=None):
    """Search for files matching in path with .log extension"""
    if path is None:
        path = "."
    matches = glob.glob(os.path.join(path, "*.log"))
    return matches


def log_print(text):
    """Output text"""
    print(text)


def matching_logs(commands, available_logs):
    """Find intersection between requested logs and available logs.

    Returns tuple (matching, not_matching), containing the
    intersection and its complement.

    Only compares basenames.

    """
    requested_logs = set("{0}.log".format(command) for command in commands)
    matching = list()
    for log in available_logs:
        if os.path.basename(log) in requested_logs:
            matching.append(log)
    not_matching = requested_logs.difference(set([os.path.basename(log)
                                                  for log in matching]))
    return matching, not_matching


def safe_output_logfile(filename):
    """Try to print logfile. If try fails, fail gracefully."""
    try:
        with open(filename) as logfile:
            log_print(logfile.read())
    except IOError:
        log_print("No log found in current directory")


def change_logfile_name(filename):
    """Change log file name if not in debug mode."""
    if jube2.conf.DEBUG_MODE:
        return
    setup_logging(filename=filename, mode="default")


def only_console_log():
    """Change to console log if not in debug mode."""
    if jube2.conf.DEBUG_MODE:
        return
    setup_logging(mode="console")


def reset_logging():
    """Reset logging to default."""
    global LOGGING_MODE, LOGFILE_NAME

    LOGGING_MODE = jube2.conf.DEFAULT_LOGGING_MODE
    LOGFILE_NAME = jube2.conf.DEFAULT_LOGFILE_NAME
