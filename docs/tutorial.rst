.. # JUBE Benchmarking Environment
   # Copyright (C) 2008-2020
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

.. index:: tutorial

JUBE tutorial
=============

.. highlight:: bash
   :linenothreshold: 5

This tutorial is meant to give you an overview about the basic usage of *JUBE*.

.. index:: installation

Installation
~~~~~~~~~~~~

Requirements: *JUBE* needs **Python 2.7** or **Python 3.2** (or any higher version)

You also can use **Python 2.6** to run *JUBE*. In this case you have to add the `argparse-module <https://pypi.python.org/pypi/argparse>`_ to
your *Python* module library on your own.

If you plan to use *YAML* based *JUBE* input files, you have to add the `pyyaml-module <https://pyyaml.org>`_ to
your *Python* module library.

To use the *JUBE* command line tool, the ``PYTHONPATH`` must contain the position of the *JUBE* package. This can be achieved in three different ways:

* You can use the **installation script** to copy all files to the right position (preferred)::

   >>> python setup.py install --user

  This will install the *JUBE* package files and executables to your ``$HOME/.local`` directory. Instead of ``--user`` also a user
  specific ``--prefix`` option is available. Here you might have to set the ``PYTHONPATH`` environment variable first
  (this will be mentioned during the install process).

* You can add the **parent folder path** of the *JUBE* package-folder (``jube2`` directory) to the ``PYTHONPATH`` environment variable::

   >>> export PYTHONPATH=<parent folder path>:$PYTHONPATH

* You can move the *JUBE* package by hand to an existing Python package folder like ``site-packages``

To use the *JUBE* command line tool like a normal command line command you can add it to the ``PATH`` environment variable::

   >>> export PATH=$HOME/.local/bin:$PATH

To check your final installation, you can use

   >>> jube --version

which should highlight the current version number.


.. index:: configuration

.. _configuration:

Configuration
~~~~~~~~~~~~~

The main *JUBE* configuration bases on the given input configuration file. But in addition, some
shell environment variables are available which can be used to set system specific options:

* ``JUBE_INCLUDE_PATH``: Can contain a list of paths (seperated by ``:``) pointing to directories, which contain
  system relevant include configuration files. This technique can be used to store platform specific parameter
  in a platform specific directory.
* ``JUBE_EXEC_SHELL``: *JUBE* normally uses ``/bin/sh`` to execute the given shell commands. This default shell can be changed
  by using this environment variable.
* ``JUBE_GROUP_NAME``: *JUBE* will use the given *UNIX* groupname to share benchmarks between different users.
  The group must exist and the *JUBE* user must be part of this group.
  The given group will be the owner of new benchmark runs. By default (without setting the environment variable)
  all file and directory permissions are defined by the normal *UNIX* rules.

*BASH* autocompletion can be enabled by using the ``eval "$(jube complete)"`` command. You can store the command in your bash profile
settings if needed.

.. index:: input format

Input format
~~~~~~~~~~~~

*JUBE* supports two different types of input formats: *XML* based files and *YAML* based files. Both formats support the same amount of *JUBE*
features and you can select your more preffered input format.

The following sections will always show all examples using both formats. However the explanations will mostly stick to the *XML* format but can be easily transfered 
to the *YAML* solution.

Both formats depends on a specifc special scharacter handling. More details can be found in the following FAQ sections:

* :ref:`XML_character_handling`
* :ref:`YAML_character_handling`

Internally *JUBE* always uses the *XML* based format, by converting *YAML* based configuration files into *XML* if necessary. This is why parsing error messages might point 
to *XML* errors even if the *YAML* format was used.

.. index:: hello world

Hello World
~~~~~~~~~~~

In this example we will show you the basic structure of a *JUBE* input file and the
basic command line options.

The files used for this example can be found inside ``examples/hello_world``.

The input file ``hello_world.xml``:

.. literalinclude:: ../examples/hello_world/hello_world.xml
   :language: xml

The input file ``hello_world.yaml``:

.. literalinclude:: ../examples/hello_world/hello_world.yaml
   :language: yaml

Every *JUBE* input file starts (after the general *XML* header line) with the root tag ``<jube>``.
This root tag must be unique. *XML* does not allow multiple root tags.

The first tag which contains benchmark specific information is ``<benchmark>``. ``hello_world`` is
the benchmarkname which can be used to identify the benchmark (e.g. when there are multiple
benchmarks inside a single input file, or when different benchmarks use the same run directory).

The ``outpath`` describes the benchmark run directory (relative to the position of the input file).
This directory will be managed by *JUBE* and will be automatically created if it does not exist.
The directory name and position are very important, because they are the main interface to communicate
with your benchmark, after it was submitted.

Using the ``<comment>`` you can store some benchmark related comments inside the benchmark directory.
You can also use normal *XML*-comments to structure your input-file:

.. code-block:: xml

   <!-- your comment -->

In this benchmark a ``<parameterset>`` is used to store the single ``<parameter name="hello_str">``.
The ``name`` of the parameter should contain only letters, numbers (should not be the first character) or the ``_`` (like a normal *Python* identifier). 
The ``name`` of the parameterset must be unique (relative to the current benchmark). In further examples we
will see that there are more types of sets, which can be distinguished by their names. Also the ``name`` of the
parameter must be unique (relative to the parameterset).

The ``<step>`` contains the operation tasks. The ``name`` must be unique.
It can use different types of existing sets. All used sets must be given by name using the ``<use>``. There can be
multiple ``<use>`` inside the same ``<step>`` and also multiple names within the same ``<use>`` are allowed (separated by ``,``).
Only sets, which are explicitly used, are available inside the step! The ``<do>`` contains a single **shell command**.
This command will run inside of a sandbox directory environment (inside the ``outpath`` directory tree).
The step and its corresponding :term:`parameter space <parameter_space>` is named :term:`workpackage`.

**Available** parameters can be used inside the shell commands. To use a parameter you have to write ::

   $parametername

or ::

   ${parametername}

The brackets must be used if you want variable concatenation. ``$hello_strtest`` will not be replaced,
``${hello_str}test`` will be replaced. If a parameter does not exist or isn't available the variable will not
be replaced! If you want to use ``$`` inside your command, you have to write ``$$`` to mask the symbol. Parameter
substitution will be done before the normal shell substitution!

To run the benchmark just type::

   >>> jube run hello_world.xml

This benchmark will produce the follwing output:

.. code-block:: none

   ######################################################################
   # benchmark: hello_world
   # id: 0
   #
   # A simple hello world
   ######################################################################

   Running workpackages (#=done, 0=wait, E=error):
   ############################################################ (  1/  1)

      stepname | all | open | wait | error | done
     ----------+-----+------+------+-------+-----
     say_hello |   1 |    0 |    0 |     0 |    1

   >>>> Benchmark information and further useful commands:
   >>>>       id: 0
   >>>>   handle: bench_run
   >>>>      dir: bench_run/000000
   >>>>  analyse: jube analyse bench_run --id 0
   >>>>   result: jube result bench_run --id 0
   >>>>     info: jube info bench_run --id 0
   >>>>      log: jube log bench_run --id 0
   ######################################################################

As you can see, there was a single step ``say_hello``,
which runs one shell command ``echo $hello_str`` that will be expanded to ``echo Hello World``.

The **id** is (in addition to the benchmark directory handle) an important number.
Every benchmark run will get a new unique **id** inside the benchmark directory.

Inside the benchmark directory you will see the follwing structure:

.. code-block:: none

   bench_run               # the given outpath
   |
   +- 000000               # the benchmark id
      |
      +- configuration.xml # the stored benchmark configuration
      +- workpackages.xml  # workpackage information
      +- run.log           # log information
      +- 000000_say_hello  # the workpackage
         |
         +- done           # workpackage finished marker
         +- work           # user sandbox folder
            |
            +- stderr      # standard error messages of used shell commands
            +- stdout      # standard output of used shell commands

``stdout`` will contain ``Hello World`` in this example case.

.. index:: help, logging

Help
~~~~

*JUBE* contains a command line based help functionality::

   >>> jube help <keyword>

By using this command you will have direct access to all keywords inside the :doc:`glossary <glossar>`.

Another useful command is the ``info`` command. It will show you information concerning your existing benchmarks::

   # display a list of existing benchmarks
   >>> jube info <benchmark-directory>
   # display information about given benchmark
   >>> jube info <benchmark-directory> -- id <id>
   # display information about a step inside the given benchmark
   >>> jube info <benchmark-directory> -- id <id> --step <stepname>

The third, also very important, functionality is the **logger**. Every ``run``, ``continue``, ``analyse``
and ``result`` execution will produce log information inside your benchmark directory.
This file contains much useful debugging output.

You can easily access these log files by using the *JUBE* log viewer command::

   >>> jube log [benchmark-directory] [--id id] [--command cmd]

e.g.::

   >>> jube log bench_runs --command run

will display the ``run.log`` of the last benchmark found inside of ``bench_runs``.

Log output can also be displayed during runtime by using the verbose output::

   >>> jube -v run <input-file>

``-vv`` can be used to display stdout output during runtime and ``-vvv`` will display the
stdout output as well as the log output at the same time.

Since the parsing step is done before creating the benchmark directory, there will be a
``jube-parse.log`` inside your current working directory, which contains the parser log information.

Errors within a ``<do>`` command will create a log entry and stop further execution of the corresponding parameter
combination. Other parameter combinations will still be executed by default. *JUBE* can also stop automatically any
further execution by using the ``-e`` option::

   >>> jube run -e <input-file>

There is also a debugging mode integrated in *JUBE*::

   >>> jube --debug <command> [other-args]

This mode avoids any *shell* execution but will generate a single log file (``jube-debug.log``) in your current working directory.

.. index:: parameter space creation

Parameter space creation
~~~~~~~~~~~~~~~~~~~~~~~~

In this example we will show you an important feature of *JUBE*: The automatic :term:`parameter space <parameter_space>` generation.

The files used for this example can be found inside ``examples/parameterspace``.

The input file ``parameterspace.xml``:

.. literalinclude:: ../examples/parameterspace/parameterspace.xml
   :language: xml

The input file ``parameterspace.yaml``:

.. literalinclude:: ../examples/parameterspace/parameterspace.yaml
   :language: yaml

Whenever a parameter contains a ``,`` (this can be changed using the ``separator`` attribute) this parameter becomes
a **template**. A step which **uses the parameterset** containing this parameter will run multiple times to iterate over
all possible parameter combinations. In this example the step ``say_hello`` will run 6 times:

.. code-block:: none

    stepname | all | open | wait | error | done
   ----------+-----+------+------+-------+-----
   say_hello |   6 |    0 |    0 |     0 |    6


Every parameter combination will run in its own sandbox directory.

Another new keyword is the ``type`` attribute. The parameter type is not used inside the substitution process, but
for sorting operations inside the ``result`` creation. The default type is ``string``.
Possible basic types are ``string``, ``int`` and ``float``.

.. index::  step dependencies, dependencies

Step dependencies
~~~~~~~~~~~~~~~~~

If you start writing a complex benchmark structure, you might want to have dependencies between different :term:`steps <step_tag>`, for
example between a compile and the execution step. *JUBE* can handle these dependencies and will also preserve the given
:term:`parameter space <parameter_space>`.

The files used for this example can be found inside ``examples/dependencies``.

The input file ``dependencies.xml``:

.. literalinclude:: ../examples/dependencies/dependencies.xml
   :language: xml

In this example we create a dependency between ``first_step`` and ``second_step``. After ``first_step`` is finished, the
corresponding ``second_step`` will start. Steps can also have multiple dependencies (separated by ``,`` in the definition), but
circular definitions will not be resolved. A dependency is a unidirectional link!

To communicate between a step and its dependency there is a link inside the work directory pointing to the corresponding
dependency step work directory. In this example we use ::

   cat first_step/stdout

to write the ``stdout``-file content of the dependency step into the ``stdout``-file of the current step.

Because the ``first_step`` uses a template parameter which creates three execution runs, there will also be
three ``second_step`` runs each pointing to different ``first_step``-directories:

.. code-block:: none

      stepname | all | open | wait | error | done
   ------------+-----+------+------+-------+-----
    first_step |   3 |    0 |    0 |     0 |    3
   second_step |   3 |    0 |    0 |     0 |    3

.. index:: substitution, loading files, external files, files

Loading files and substitution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every step runs inside a unique sandbox directory. Usually, you will need to have external files inside this directory (e.g. the source files)
and in some cases you want to change a parameter inside the file based on your current :term:`parameter space <parameter_space>`. There are two additional set-types
which handle this behaviour inside of *JUBE*.

The files used for this example can be found inside ``examples/files_and_sub``.

The input file ``files_and_sub.xml``:

.. literalinclude:: ../examples/files_and_sub/files_and_sub.xml
   :language: xml

The content of file ``file.in``:

.. literalinclude:: ../examples/files_and_sub/file.in
   :language: none

Inside the ``<fileset>`` the current location (relative to the current input file; also absolute paths are allowed) of files is defined. ``<copy>`` specifies that the
file should be copied to the sandbox directory when the fileset is used. Also a ``<link>`` option is available to create a symbolic link to the given file
inside the sandbox directory.

If there are additional operations needed to :term:`prepare <prepare_tag>` your files (e.g. expand a tar-file). You can use the ``<prepare>``-tag inside your ``<fileset>``.

The ``<substituteset>`` describes the substitution process. The ``<iofile>`` contains the input and output filename. The path is relative to
the sandbox directory. Because we do/should not know that location we use the fileset to copy ``file.in`` to this directory.

The ``<sub>`` specifies the substitution. All occurrences of ``source`` will be substituted by ``dest``. As you can see, you can
use parameters inside the substitution.

There is no ``<use>`` inside any set. The combination of all sets will be done inside the ``<step>``. So if you use a parameter inside a
``<sub>`` you must also add the corresponding ``<parameterset>`` inside the ``<step>`` where you use the ``<substituteset>``!

In the ``sub_step`` we use all available sets. The use order is not relevant. The normal execution process will be:

#. Parameter space expansion
#. Copy/link files
#. Prepare operations
#. File substitution
#. Run shell operations

The resulting directory-tree will be:

.. code-block:: none

   bench_run               # the given outpath
   |
   +- 000000               # the benchmark id
      |
      +- configuration.xml # the stored benchmark configuration
      +- workpackages.xml  # workpackage information
      +- 000000_sub_step   # the workpackage ($number = 1)
         |
         +- done           # workpackage finished marker
         +- work           # user sandbox folder
            |
            +- stderr      # standard error messages of used shell commands
            +- stdout      # standard output of used shell commands (Number: 1)
            +- file.in     # the file copy
            +- file.out    # the substituted file
      +- 000001_sub_step   # the workpackage ($number = 2)
         |
         +- ...
      +- ...

.. index:: analyse, result, table

Creating a result table
~~~~~~~~~~~~~~~~~~~~~~~

Finally, after running the benchmark, you will get several directories. *JUBE* allows you to parse your result files distributed over these directories to extract
relevant data (e.g. walltime information) and create a result table.

The files used for this example can be found inside ``examples/result_creation``.

The input file ``result_creation.xml``:

.. literalinclude:: ../examples/result_creation/result_creation.xml
   :language: xml

Using ``<parameterset>`` and ``<step>`` we create three :term:`workpackages <workpackage>`. Each writing ``Number: $number`` to ``stdout``.

Now we want to parse these ``stdout`` files to extract information (in this example case the written number). First of all we have to declare a
``<patternset>``. Here we can describe a set of ``<pattern>``. A ``<pattern>`` is a regular expression which will be used to parse your result files
and search for a given string. In this example we only have the ``<pattern>`` ``number_pat``. The name of the pattern must be unique (based on the usage of the ``<patternset>``).
The ``type`` is optional. It is used when the extracted data will be sorted. The regular expression can contain other patterns or parameters. The example uses ``$jube_pat_int`` which
is a *JUBE* :term:`default pattern <jube_pattern>` matching integer values. The pattern can contain a group, given by brackets ``(...)``, to declare the extraction part
(``$jube_pat_int`` already contains these brackets).

E.g. ``$jube_pat_int`` and ``$jube_pat_fp`` are defined in the following way:

.. code-block:: xml

   <pattern name="jube_pat_int" type="int">([+-]?\d+)</pattern>
   <pattern name="jube_pat_fp" type="float">([+-]?\d*\.?\d+(?:[eE][-+]?\d+)?)</pattern>

If there are multiple matches inside a single file you can add a :term:`reduce option <analyser_tag>`. By default, only the first match will be extracted.

To use your ``<patternset>`` you have to specify the files which should be parsed. This can be done using the ``<analyser>``.
It uses relevant patternsets. Inside the ``<analyse>`` a step-name and a file inside this step is given. Every workpackage file combination
will create its own result entry.

The analyser automatically knows all parameters which were used in the given step and in depending steps. There is no ``<use>`` option to include additional ``<parameterset>`` 
that have not been already used within the analysed ``<step>``.

To run the anlayse you have to write::

   >>> jube analyse bench_run

The analyse data will be stored inside the benchmark directory.

The last part is the result table creation. Here you have to use an existing analyser. The ``<column>`` contains a pattern or a parameter name. ``sort`` is
the optional sorting order (separated by ``,``). The ``style`` attribute can be ``csv``, ``pretty`` or ``aligned`` to get different ASCII representations.

To create the result table you have to write::

   >>> jube result bench_run -i last

If you run the ``result`` command for the first time, the ``analyse`` step will be executed automatically, if it wasn't executed before. So it is not necessary to run the separate ``analyse`` step all the time. However you need the separate ``analyse`` 
if you want to force a re-run of the ``analyse`` step, otherwise only the stored values of the first ``analyse`` will be used in the ``result`` step.

The result table will be written to ``STDOUT`` and into a ``result.dat`` file inside ``bench_run/<id>/result``. The ``last`` is the default option and can also be replaced by a specific benchmark id.
If the id selection is missing a combined result table of all available benchmark runs from the ``bench_run`` directory will be created.

Output of the given example:

.. code-block:: none

   number | number_pat
   -------+-----------
        1 |          1
        2 |          2
        4 |          4

The analyse and result instructions can be combined within one single command:

   >>> jube result bench_run -a

This was the last example of the basic *JUBE* tutorial. Next you can start the :doc:`advanced tutorial <advanced>` to get more information about
including external sets, jobsystem representation and scripting parameter.
