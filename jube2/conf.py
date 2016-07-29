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
"""Configuration"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

# general
JUBE_VERSION = "2.1.2"
ALLOWED_SCRIPTTYPES = ["python", "perl", "shell"]
DEBUG_MODE = False
VERBOSE_LEVEL = 0
UPDATE_VERSION_URL = "http://apps.fz-juelich.de/jsc/jube/jube2/version"
UPDATE_URL = "http://apps.fz-juelich.de/jsc/jube/jube2/download.php"
STANDARD_SHELL = "/bin/sh"

# input/output
DEFAULT_SEPARATOR = ","
ZERO_FILL_DEFAULT = 6
DEFAULT_WIDTH = 70
MAX_TABLE_CELL_WIDTH = 40
HIDE_ANIMATIONS = False
VERBOSE_STDOUT_READ_CHUNK_SIZE = 50
VERBOSE_STDOUT_POLL_SLEEP = 0.05
SYSLOG_FMT_STRING = "jube[%(process)s]: %(message)s"
PREPROCESS_MAX_ITERATION = 10

# filenames
WORKPACKAGE_DONE_FILENAME = "done"
CONFIGURATION_FILENAME = "configuration.xml"
WORKPACKAGES_FILENAME = "workpackages.xml"
ANALYSE_FILENAME = "analyse.xml"
RESULT_DIRNAME = "result"
ENVIRONMENT_INFO = "jube_environment_information.dat"
TIMESTAMPS_INFO = "timestamps"

# logging
DEFAULT_LOGFILE_NAME = "jube-parse.log"
LOGFILE_DEBUG_NAME = "jube-debug.log"
LOGFILE_DEBUG_MODE = "w"
LOGFILE_RUN_NAME = "run.log"
LOGFILE_CONTINUE_NAME = "continue.log"
LOGFILE_ANALYSE_NAME = "analyse.log"
LOGFILE_PARSE_NAME = "parse.log"
LOGFILE_RESULT_NAME = "result.log"
LOG_CONSOLE_FORMAT = "%(message)s"
LOG_FILE_FORMAT = "[%(asctime)s]:%(levelname)s: %(message)s"
DEFAULT_LOGGING_MODE = "default"

# other
ERROR_MSG_LINES = 5
MAX_RECURSIVE_SUB = 5
