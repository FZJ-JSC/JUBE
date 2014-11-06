"""Configuration"""

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

# general
JUBE_VERSION = "2.0.0"
ALLOWED_SCRIPTTYPES = ["python", "perl"]
DEBUG_MODE = False

# input/output
DEFAULT_SEPARATOR = ","
ZERO_FILL_DEFAULT = 6
DEFAULT_WIDTH = 70
MAX_TABLE_CELL_WIDTH = 40
HIDE_ANIMATIONS = False

# filenames
WORKPACKAGE_DONE_FILENAME = "done"
CONFIGURATION_FILENAME = "configuration.xml"
WORKPACKAGES_FILENAME = "workpackages.xml"
ANALYSE_FILENAME = "analyse.xml"
RESULT_DIRNAME = "result"

# logging
DEFAULT_LOGFILE_NAME = "jube-parse.log"
LOGFILE_DEBUG_NAME = "jube-debug.log"
LOGFILE_MODE = "a"
LOGFILE_DEBUG_MODE = "w"
LOG_CONSOLE_FORMAT = "%(message)s"
LOG_FILE_FORMAT = "[%(asctime)s]:%(levelname)s: %(message)s"
DEFAULT_LOGGING_MODE = "default"
