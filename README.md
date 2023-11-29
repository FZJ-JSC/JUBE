# JUBE

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7534372.svg)](https://doi.org/10.5281/zenodo.7534372)

JUBE Benchmarking Environment
Copyright (C) 2008-2023
Forschungszentrum Juelich GmbH, Juelich Supercomputing Centre
http://www.fz-juelich.de/jsc/jube

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/.

----

# Prerequisites

JUBE version 2 is written in the Python programming language.

You need Python 3.2 (or a higher version) to run the program.

JUBE is not compatible to Python2.x any longer.

You will also need SQLite version 3.35.0 (or higher) to use the database as a result output.

When using YAML, it is also recommended to install the optional pip package `ruamel.yaml` to enable validation of the YAML scripts.

# Installation

After download, unpack the distribution file `JUBE-<version>.tar.gz` with:

```bash
tar -xf JUBE-<version>.tar.gz
```

You can install the files to your `$HOME/.local` directory by using:

```bash
cd JUBE-<version>
python setup.py install --user
```

`$HOME/.local/bin` must be inside your `$PATH` environment variable to use JUBE in an easy way.

Instead you can also specify a self defined path prefix:

```bash
python setup.py install --prefix=<some_path>
```

You might be asked during the installation to add your path (and some subfolders) to the `$PYTHONPATH` environment variable (this should be stored in your profile settings):

```bash
export PYTHONPATH=<needed_path>:$PYTHONPATH
```

Another option is to use `pip[3]` for installation (including download):

```bash
pip3 install http://apps.fz-juelich.de/jsc/jube/jube2/download.php?version=latest --user
# or
pip3 install http://apps.fz-juelich.de/jsc/jube/jube2/download.php?version=latest --prefix=<some_path>
```

In addition it is useful to also set the `$PATH` variable again.

To check the installation you can run:


```
jube --version
```

Without the `--user` or `--prefix` argument, JUBE will be installed in the standard system path for Python packages.

# Acknowledgments  

We gratefully acknowledge the following reserach projects and institutions for their support in the development of JUBE2 and granting compute time to develop JUBE2.

- UNSEEN (BMWi project, ID: 03EI1004A-F)
- Gauss Centre for Supercomputing e.V. (www.gauss-centre.eu) and the John von Neumann Institute for Computing (NIC) on the GCS Supercomputer JUWELS at Jülich Supercomputing Centre (JSC) 

Furthermore, we gratefully acknowledge all the people and institutions having contributed to this project with their expertise, time and passion in any way. A subset of these people and institutions can be found within the AUTHORS file.

# Further Information

For further information please see the documentation: http://www.fz-juelich.de/jsc/jube

Contact: [jube.jsc@fz-juelich.de](mailto:jube.jsc@fz-juelich.de)
