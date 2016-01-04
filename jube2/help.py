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
"""User help"""

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
