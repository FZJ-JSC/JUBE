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

# For installation you can use:
#
# python setup.py install --user
#
# to install it into your .local folder. .local/bin must be inside your $PATH.
# You can also change the folder by using --prefix instead of --user

try:
    from setuptools import setup
    SHARE_PATH = ""
except ImportError:
    from distutils.core import setup
    SHARE_PATH = "share/jube"
import os


def rel_path(directory, new_root=""):
    """Return list of tuples (directory, list of files)
    recursively from directory"""
    setup_dir = os.path.join(os.path.dirname(__file__))
    cwd = os.getcwd()
    result = list()
    if setup_dir != "":
        os.chdir(setup_dir)
    for path_info in os.walk(directory):
        root = path_info[0]
        filenames = path_info[2]
        files = list()
        for filename in filenames:
            path = os.path.join(root, filename)
            if (os.path.isfile(path)) and (filename[0] != "."):
                files.append(path)
        if len(files) > 0:
            result.append((os.path.join(new_root, root), files))
    if setup_dir != "":
        os.chdir(cwd)
    return result

config = {'description': 'JUBE Benchmarking Environment',
          'author': 'Forschungszentrum Juelich GmbH',
          'url': 'www.fz-juelich.de/jube',
          'download_url': 'www.fz-juelich.de/jube',
          'author_email': 'jube.jsc@fz-juelich.de',
          'version': '2.0.3',
          'packages': ['jube2'],
          'package_data': {'jube2': ['help.txt']},
          'data_files': ([(os.path.join(SHARE_PATH, 'docu'),
                           ['docs/JUBE.pdf']),
                          (SHARE_PATH, ['LICENSE'])] +
                         rel_path("examples", SHARE_PATH) +
                         rel_path("schema", SHARE_PATH) +
                         rel_path("platform", SHARE_PATH)),
          'scripts': ['bin/jube', 'bin/jube-autorun'],
          'long_description': 'JUBE',
          'license': 'GPLv3',
          'platforms': 'Linux',
          'keywords': 'JUBE Benchmarking Environment',
          'name': 'JUBE'}

setup(**config)
