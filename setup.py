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

# For installation you can use:
#
# python setup.py install --user
#
# to install it into your .local folder. .local/bin must be inside your $PATH.
# You can also change the folder by using --prefix instead of --user

add_opt = dict()
try:
    from setuptools import setup
    import sys
    SHARE_PATH = ""
    add_opt["install_requires"] = list()
    if sys.hexversion < 0x02070000:
        add_opt["install_requires"].append("argparse")
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

config = {'name': 'JUBE',
          'description': 'JUBE Benchmarking Environment',
          'author': 'Forschungszentrum Juelich GmbH',
          'url': 'www.fz-juelich.de/jube',
          'download_url': 'www.fz-juelich.de/jube',
          'author_email': 'jube.jsc@fz-juelich.de',
          'version': '2.1.3',
          'packages': ['jube2','jube2.result_types'],
          'package_data': {'jube2': ['help.txt']},
          'data_files': ([(os.path.join(SHARE_PATH, 'docu'),
                           ['docs/JUBE.pdf']),
                          (SHARE_PATH, ['LICENSE','RELEASE_NOTES'])] +
                         rel_path("examples", SHARE_PATH) +
                         rel_path("contrib", SHARE_PATH) +
                         rel_path("platform", SHARE_PATH)),
          'scripts': ['bin/jube', 'bin/jube-autorun'],
          'long_description': (
              "Automating benchmarks is important for reproducibility and "
              "hence comparability which is the major intent when "
              "performing benchmarks. Furthermore managing different "
              "combinations of parameters is error-prone and often "
              "results in significant amounts work especially if the "
              "parameter space gets large.\n"
              "In order to alleviate these problems JUBE helps performing "
              "and analyzing benchmarks in a systematic way. It allows "
              "custom work flows to be able to adapt to new architectures.\n"
              "For each benchmark application the benchmark data is written "
              "out in a certain format that enables JUBE to deduct the "
              "desired information. This data can be parsed by automatic "
              "pre- and post-processing scripts that draw information, "
              "and store it more densely for manual interpretation.\n"
              "The JUBE benchmarking environment provides a script based "
              "framework to easily create benchmark sets, run those sets "
              "on different computer systems and evaluate the results. It "
              "is actively developed by the Juelich Supercomputing Centre "
              "of Forschungszentrum Juelich, Germany."),
          'license': 'GPLv3',
          'platforms': 'Linux',
          'classifiers': [
              "Development Status :: 5 - Production/Stable",
              "Environment :: Console",
              "Intended Audience :: End Users/Desktop",
              "Intended Audience :: Developers",
              "Intended Audience :: System Administrators",
              "License :: OSI Approved :: GNU General Public License v3 " +
              "(GPLv3)",
              "Operating System :: POSIX :: Linux",
              "Programming Language :: Python :: 2.6",
              "Topic :: System :: Monitoring",
              "Topic :: System :: Benchmark",
              "Topic :: Software Development :: Testing"],
          'keywords': 'JUBE Benchmarking Environment'}
config.update(add_opt)

setup(**config)
