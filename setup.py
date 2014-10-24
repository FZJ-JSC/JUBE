# #############################################################################
# #  JUBE Benchmarking Environment                                           ##
# #  http://www.fz-juelich.de/jsc/jube                                       ##
# #############################################################################
# #  Copyright (c) 2008-2014                                                 ##
# #  Forschungszentrum Juelich, Juelich Supercomputing Centre                ##
# #                                                                          ##
# #  See the file LICENSE in the package base directory for details          ##
# #############################################################################

# For installation you can use:
#
# python setup.py install --user
#
# to install it into your .local folder. .local/bin must be inside your $PATH.
# You can also change the folder by using --prefix instead of --user

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os


def rel_path(directory):
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
            if os.path.isfile(path):
                files.append(path)
        if len(files) > 0:
            result.append((root, files))
    if setup_dir != "":
        os.chdir(cwd)
    return result

config = {'description': 'JUBE Benchmarking Environment',
          'author': 'Forschungszentrum Juelich GmbH',
          'url': 'www.fz-juelich.de/jube',
          'download_url': 'www.fz-juelich.de/jube',
          'author_email': 'jube.jsc@fz-juelich.de',
          'version': '2.0.0',
          'install_requires': [],
          'packages': ['jube2'],
          'package_data': {'jube2': ['help.txt', '*.conf']},
          'data_files': [('doku', ['docs/_build/latex/JUBE.pdf']),
                         ('', ['LICENSE'])] +
                         rel_path("examples") +
                         rel_path("schema"),
          'scripts': ['bin/jube'],
          'long_description': 'JUBE',
          'keywords': 'JUBE Benchmarking Environment',
          'name': 'JUBE'}

setup(**config)
