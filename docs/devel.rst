Developer documentation
=======================

.. highlight:: bash
   :linenothreshold: 5

Coding standards
~~~~~~~~~~~~~~~~

* *Python* code must be **pep8** conform
* do not use tabs! Use four whitespaces instead
* avoid ``map``, ``filter`` or ``lambda`` commands
* avoid very long methods
* use multiple files for completely different classes
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

* create a new repository branch for a completely new feature

Pylint
------

In the top directory

  .. code-block:: sh

     pylint --rcfile devel-utils/pylint.rc jube2


Flake8
------

In the top directory

  .. code-block:: sh

     flake8 --config devel-utils/flake8 jube2

Another possibility is to copy or link the file to the default search
path ``~/.config/flake8`` to use it globally.


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

Here you will find the *Python* package documentation of *JUBE*: :doc:`Package doku <jube2>`
