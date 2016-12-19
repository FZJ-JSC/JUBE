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
"""ASCII and string output generators"""

from __future__ import (print_function,
                        unicode_literals,
                        division)

import jube2.conf
import textwrap
import copy
import sys
import xml.etree.ElementTree as ET


def text_boxed(text):
    """Create an ASCII boxed version of text."""
    box = "#" * jube2.conf.DEFAULT_WIDTH
    for line in text.split("\n"):
        box += "\n"
        lines = ["# {0}".format(element) for element in
                 textwrap.wrap(line.strip(), jube2.conf.DEFAULT_WIDTH - 2)]
        if len(lines) == 0:
            box += "#"
        else:
            box += "\n".join(lines)
    box += "\n" + "#" * jube2.conf.DEFAULT_WIDTH
    return box


def text_line():
    """Return a horizonal ASCII line"""
    return "#" * jube2.conf.DEFAULT_WIDTH


def text_table(entries_ext, use_header_line=False, indent=1, align_right=True,
               auto_linebreak=True, colw=None, pretty=True, separator=None,
               transpose=False):
    """Create a ASCII based table.
    entries must contain a list of lists, use_header_line can be used to
    mark the first entry as title.

    Return the ASCII table
    """

    if not pretty:
        auto_linebreak = False
        use_header_line = False
        indent = 0

    # Transpose data entries if needed
    if transpose:
        entries = list(zip(*entries_ext))
        use_header_line = False
    else:
        entries = copy.deepcopy(entries_ext)

    max_length = list()
    table_str = ""
    header_line_used = not use_header_line

    # calculate needed maxlength
    for item in entries:
        for i, text in enumerate(item):
            if i > len(max_length) - 1:
                max_length.append(0)
            if pretty:
                for line in text.splitlines():
                    max_length[i] = max(max_length[i], len(line))
                if auto_linebreak:
                    max_length[i] = min(max_length[i],
                                        jube2.conf.MAX_TABLE_CELL_WIDTH)

    if colw is not None:
        for i, maxl in enumerate(max_length):
            if i < len(colw):
                max_length[i] = max(maxl, colw[i])

    # fill cells
    for item in entries:

        # Wrap text
        wraps = list()
        for text in item:
            if auto_linebreak:
                lines = list()
                for line in text.splitlines():
                    lines += \
                        textwrap.wrap(line, jube2.conf.MAX_TABLE_CELL_WIDTH)
                wraps.append(lines)
            else:
                if pretty:
                    wraps.append(text.splitlines())
                else:
                    wraps.append([text.replace("\n", " ")])

        grow = True
        height = 0
        while grow:
            grow = False
            line_str = " " * indent
            for i, wrap in enumerate(wraps):
                grow = grow or len(wrap) > height + 1
                if len(wrap) > height:
                    text = wrap[height]
                else:
                    text = ""
                if align_right and height == 0:
                    align = ">"
                else:
                    align = "<"
                line_str += \
                    ("{0:" + align + str(max_length[i]) + "s}").format(text)
                if pretty:
                    if i < len(max_length) - 1:
                        if separator is None:
                            line_str += " | "
                        else:
                            line_str += separator
                else:
                    if i < len(max_length) - 1:
                        if separator is None:
                            line_str += ","
                        else:
                            line_str += separator
            line_str += "\n"
            table_str += line_str
            height += 1

        if not header_line_used:
            # Create title separator line
            table_str += " " * indent
            for i, cell_length in enumerate(max_length):
                table_str += "-" * cell_length
                if i < len(max_length) - 1:
                    table_str += "-+-"
            table_str += "\n"
            header_line_used = True
    return table_str


def print_loading_bar(current_cnt, all_cnt, wait_cnt=0, error_cnt=0):
    """Show a simple loading animation"""
    width = jube2.conf.DEFAULT_WIDTH - 10
    cnt = dict()
    if all_cnt > 0:
        cnt["done_cnt"] = (current_cnt * width) // all_cnt
        cnt["wait_cnt"] = (wait_cnt * width) // all_cnt
        cnt["error_cnt"] = (error_cnt * width) // all_cnt
    else:
        cnt["done_cnt"] = 0
        cnt["wait_cnt"] = 0
        cnt["error_cnt"] = 0

    # shrink cnt if there was some rounding issue
    for key in ("wait_cnt", "error_cnt"):
        if (cnt[key] > 0) and (width < sum(cnt.values())):
            cnt[key] = max(0, width - sum([cnt[k] for k in cnt if k != key]))

    # fill up medium_cnt if there was some rounding issue
    if (current_cnt + wait_cnt + error_cnt == all_cnt) and \
            (sum(cnt.values()) < width):
        for key in ("wait_cnt", "error_cnt", "done_cnt"):
            if cnt[key] > 0:
                cnt[key] += width - sum(cnt.values())
                break

    cnt["todo_cnt"] = width - sum(cnt.values())

    bar_str = "\r{0}{1}{2}{3} ({4:3d}/{5:3d})".format("#" * cnt["done_cnt"],
                                                      "0" * cnt["wait_cnt"],
                                                      "E" * cnt["error_cnt"],
                                                      "." * cnt["todo_cnt"],
                                                      current_cnt, all_cnt)
    sys.stdout.write(bar_str)
    sys.stdout.flush()


def element_tree_tostring(element, encoding=None):
    """A more encoding friendly ElementTree.tostring method"""
    class Dummy(object):

        """Dummy class to offer write method for etree."""

        def __init__(self):
            self._data = list()

        @property
        def data(self):
            """Return data"""
            return self._data

        def write(self, *args):
            """Simulate write"""
            self._data.append(*args)
    file_dummy = Dummy()
    ET.ElementTree(element).write(file_dummy, encoding)
    return "".join(dat.decode(encoding) for dat in file_dummy.data)


def format_value(format_string, value):
    """Return formated value"""
    if (type(value) is not int) and \
            (("d" in format_string) or ("b" in format_string) or
             ("c" in format_string) or ("o" in format_string) or
             ("x" in format_string) or ("X" in format_string)):
        value = int(float(value))
    elif (type(value) is not float) and \
         (("e" in format_string) or ("E" in format_string) or
          ("f" in format_string) or ("F" in format_string) or
          ("g" in format_string) or ("G" in format_string)):
        value = float(value)
    format_string = "{{0:{0}}}".format(format_string)
    return format_string.format(value)
