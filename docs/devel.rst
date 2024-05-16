.. # JUBE Benchmarking Environment
   # Copyright (C) 2008-2024
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

Developer documentation
=======================

.. highlight:: bash
   :linenothreshold: 5

Contributing
~~~~~~~~~~~~

We welcome contributions in the form of
`pull requests <https://github.com/FZJ-JSC/JUBE/pulls>`_. Contributions can
be anything from bug fixes to documentation to new features. Please ensure
that your contributions to JUBE comply with the
`CONTRIBUTING.md <https://github.com/FZJ-JSC/JUBE/blob/master/CONTRIBUTING.md>`_
and the following developer guidelines.

Coding standards
~~~~~~~~~~~~~~~~

* *Python* code must be **pep8** conform
* check your code using **pylint**
* do not use tabs! Use four whitespaces instead
* avoid ``map``, ``filter`` or ``lambda`` commands
* use ``format`` instead of ``%``
* avoid very long methods
* use multiple files for completely different classes
* try to stay **Python3.2** conform
* ``import`` of package files should use the complete path (avoid ``from``)
* all files must include the **Python3** compatible header:

  .. code-block:: xml

      from __future__ import (print_function,
                              unicode_literals,
                              division)

* new include file features:

  * must be downward compatible
  * must be added to schema files
  * must be documented and there must be a small example
  * must be covered by tests

Pylint
------

In the top directory

  .. code-block:: sh

     pylint --rcfile devel-utils/pylint.rc jube


Flake8
------

In the top directory

  .. code-block:: sh

     flake8 --config devel-utils/flake8 jube

Another possibility is to copy or link the file to the default search
path ``~/.config/flake8`` to use it globally.


Coverage and testing
--------------------

To produce a coverage report the ``coverage`` packet must be
installed. Run

  .. code-block:: sh

     python -m coverage run ./run_all_tests.py
     python -m coverage html

in the ``test`` directory. The first command creates a coverage report
``.coverage`` in the current directory and the second one creates a
folder ``htmlcov`` with html files visualizing the code coverage by
adding colors for covered and uncovered regions of the code. The
summary can be viewed in ``index.html``.

Testing for multiprocessing parts need to be performed manually. The 
corresponding file is located in ``tests/multiprocessing_tests.py``

Make sure to add tests for your developments.


Documentation creation
~~~~~~~~~~~~~~~~~~~~~~

Inside the ``docs`` directory you can use::

   >>> make html        #create html docu files
   >>> make pdflatex    #create pdf  docu file
   >>> make update_help #update jube command line help

Create distribution
~~~~~~~~~~~~~~~~~~~

Inside the main *JUBE* directory you can use::

   >>> python setup.py sdist

to update the ``tar.gz`` file inside the dist directory.

* Check version before running ``sdist``
* Store a completely new mayor version inside the tags area of the repository

Python package documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here you will find the *Python* package documentation of *JUBE*: :doc:`Package doku <jube>`
