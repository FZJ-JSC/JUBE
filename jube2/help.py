"""User help"""

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

import jube2
import os
import re

HELP = dict()


def load_help():
    """Load additional documentation out of help file and add these data to
    global help dictionary."""
    path = os.path.join(jube2.__path__[0], "help.txt")
    help_file = open(path, "r")
    group = None
    # skip header lines
    i = 0
    while i < 4:
        help_file.readline()
        i += 1
    for line in help_file:
        # search for new abstract inside of help file
        matcher = re.match(r"^(\S+)s*$", line)
        if matcher is not None:
            group = matcher.group(1)
            HELP[group] = ""
        else:
            if (len(line) > 0) and (group is not None):
                HELP[group] += line[0] + line[3:]
    help_file.close()
