"""Logging Support"""

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

import logging
import sys
import glob
import os.path
import jube2.conf


class JubeLogger(logging.getLoggerClass()):

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

logging_mode = jube2.conf.DEFAULT_LOGGING_MODE
logfile_name = jube2.conf.LOGFILE_NAME


def getLogger(name=None):
    """Return logger given by name"""
    return logging.getLogger(__name__)


def setup_logging(mode=None, filename=None):
    """Setup the logging configuration.

    Available modes are
      default   log to console and file
      console   only console output

    filename can be given optionally.

    The setup includes setting the handlers and formatters. Calling
    this function multiple times causes old handlers to be removed
    before new ones are added.

    """
    global logging_mode, logfile_name

    # Use debug file name and debug file mode when in debug mode
    if jube2.conf.DEBUG_MODE:
        filename = jube2.conf.LOGFILE_DEBUG_NAME
        mode = "default"
        filemode = jube2.conf.LOGFILE_DEBUG_MODE
    else:
        filemode = jube2.conf.LOGFILE_MODE

    if not mode:
        mode = logging_mode
    else:
        logging_mode = mode
    if not filename:
        filename = logfile_name
    else:
        logfile_name = filename

    # this is needed to make the other handlers accept on low priority
    # events
    _logger = logging.getLogger("jube2")
    _logger.setLevel(logging.DEBUG)

    # list is needed since we remove from the list we just iterate
    # over
    for handler in list(_logger.handlers):
        handler.close()
        _logger.removeHandler(handler)

    # create, configure and add console handler
    console_formatter = logging.Formatter(jube2.conf.LOG_CONSOLE_FORMAT)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    if mode == "default":
        # create, configure and add file handler
        file_formatter = logging.Formatter(jube2.conf.LOG_FILE_FORMAT)
        file_handler = logging.FileHandler(filename, filemode)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        _logger.addHandler(file_handler)


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
    requested_logs = {"{}.log".format(command) for command in commands}

    available_base = {os.path.basename(log) for log in available_logs}

    matching = list(requested_logs.intersection(available_base))
    not_matching = list(requested_logs.difference(available_base))

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
    setup_logging(filename=filename)
