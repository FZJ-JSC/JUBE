.. # JUBE Benchmarking Environment
   # Copyright (C) 2008-2017
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

.. index:: commandline

.. |ID_DESCRIPTION| replace:: select benchmark id, negative ids count backwards
   from the end, default: last found inside the benchmarks directory

Command line documentation
==========================

.. highlight:: bash
   :linenothreshold: 5

Here you will find a list of all available *JUBE* command line options. You can also use::

   jube -h

to get a list of all available commands.

Because of the *shell* parsing mechanism take care if you write your optional arguments after the command name before the positional
arguments. You **must** use ``--`` to split the ending of an optional (if the optional argument takes multiple input elements) and the start of the positional argument.

When using *BASH* you can use the ``jube complete`` mechanism to enable a command line autocompletion.

.. index:: general commandline options

general
~~~~~~~

General commandline options (can also be used in front of a subcommand)

.. code-block:: none

   jube [-h] [-V] [-v] [--debug] [--force] [--devel] {...}

``-h``, ``--help``
   show general help information

``-V``, ``--version``
   show version information

``-v``, ``--verbose``
   enable verbose console output (use ``-vv`` to show stdout during execution and ``-vvv`` to show log and stdout)

``--debug``
   use debugging mode (no shell script execution)

``--force``
   ignore any *JUBE* version conflict

``--devel``
   developer mode (show complete error messages)

.. index:: run

run
~~~

Run a new benchmark.

.. code-block:: none

   jube run [-h] [--only-bench ONLY_BENCH [ONLY_BENCH ...]]
            [--not-bench NOT_BENCH [NOT_BENCH ...]] [-t TAG [TAG ...]]
            [--hide-animation] [--include-path INCLUDE_PATH [INCLUDE_PATH ...]]
            [-a] [-r] [-e] [-m COMMENT] [--id ID [ID ...]] FILE [FILE ...]

``-h``, ``--help``
   show command help information

``--only-bench ONLY_BENCH [ONLY_BENCH ...]``
   only run specific benchmarks given by benchmark name

``--not-bench NOT_BENCH [NOT_BENCH ...]]``
   do not run specific benchmarks given by benchmark name

``-t TAG [TAG ...]``, ``--tag TAG [TAG ...]``
   use specific tags when running this file. This will be used for :term:`tagging`

``--hide-animation``
   hide the progress bar animation (if you want to use *JUBE* inside a scripting environment)

``--include-path INCLUDE_PATH [INCLUDE_PATH ...]``
   add additional include pathes where to search for include files

``-a``, ``--analyse``
   run analyse after finishing run command

``-r``, ``--result``
   run result after finishing run command (this will also start analyse)

``-e``, ``--exit``
   run will exit if there is an error

``-m COMMENT``, ``--comment COMMENT``
   overwrite benchmark specific comment

``-i ID [ID ...]``, ``--id ID [ID ...]``
   use specific benchmark id (must be >= 0)

``FILE [FILE ...]``
   input *XML* file

.. index:: convert

convert
~~~~~~~

Convert jube version 1 files to jube version 2 files.

.. code-block:: none

   jube convert [-h] [-i INPUT_PATH] main_xml_file

``-h``, ``--help``
   show command help information

``-i INPUT_PATH main_xml_file``
  select root directory of jube version 1 benchmark along with the corresponding main XML file

.. index:: continue

continue
~~~~~~~~

Continue an existing benchmark.

.. code-block:: none

   jube continue [-h] [-i ID [ID ...]] [--hide-animation] [-a] [-r] [-e] [DIRECTORY]

``-h``, ``--help``
   show command help information

``-i ID [ID ...]``, ``--id ID [ID ...]``
   |ID_DESCRIPTION|

``--hide-animation``
   hide the progress bar animation (if you want to use *JUBE* inside a scripting environment)

``-a``, ``--analyse``
   run analyse after finishing run command

``-r``, ``--result``
   run result after finishing run command (this will also start analyse)

``-e``, ``--exit``
   run will exit if there is an error

``DIRECTORY``
   directory which contain benchmarks, default: ``.``

.. index:: analyse

analyse
~~~~~~~

Run the analyse procedure.

.. code-block:: none

   jube analyse [-h] [-i ID [ID ...]] [-u UPDATE_FILE]
                [--include-path INCLUDE_PATH [INCLUDE_PATH ...]]
                [-t TAG [TAG ...]] [DIRECTORY]


``-h``, ``--help``
   show command help information

``-i ID [ID ...]``, ``--id ID [ID ...]``
   |ID_DESCRIPTION|

``-u UPDATE_FILE``, ``--update UPDATE_FILE``
   use given input *XML* file to update ``patternsets``, ``analyser`` and ``result`` before running the analyse

``--include-path INCLUDE_PATH [INCLUDE_PATH ...]``
   add additional include pathes where to search for include files (when using ``--update``)

``-t TAG [TAG ...]``, ``--tag TAG [TAG ...]``
   use specific tags when running this file. This will be used for :term:`tagging` (when using ``--update``)

``DIRECTORY``
   directory which contain benchmarks, default: ``.``

.. index:: result

result
~~~~~~

Run the result creation.

.. code-block:: none

   jube result [-h] [-i ID [ID ...]] [-a] [-r] [-u UPDATE_FILE] [-n NUM]
               [--include-path INCLUDE_PATH [INCLUDE_PATH ...]]
               [-t TAG [TAG ...]] [-o RESULT_NAME [RESULT_NAME ...]] [DIRECTORY]



``-h``, ``--help``
   show command help information

``-i ID [ID ...]``, ``--id ID [ID ...]``
   select benchmark id, if no id is given, output of all available benchmarks will be shown

``-a``, ``--analyse``
   run analyse before running result command

``-r``, ``--reverse``
   reverse benchmark output order when multiple benchmarks are given

``-n``, ``--num``
   show only last N benchmarks

``-u UPDATE_FILE``, ``--update UPDATE_FILE``
   use given input *XML* file to update ``patternsets``, ``analyser`` and ``result`` before running the analyse

``--include-path INCLUDE_PATH [INCLUDE_PATH ...]``
   add additional include pathes where to search for include files (when using ``--update``)

``-t TAG [TAG ...]``, ``--tag TAG [TAG ...]``
   use specific tags when running this file. This will be used for :term:`tagging` (when using ``--update``)

``-o RESULT_NAME [RESULT_NAME ...]``, ``-only RESULT_NAME [RESULT_NAME ...]``
   only create specific results given by name

``DIRECTORY``
   directory which contain benchmarks, default: ``.``

.. index:: comment

comment
~~~~~~~

Add or manipulate the benchmark comment.

.. code-block:: none

   jube comment [-h] [-i ID [ID ...]] [-a] comment [DIRECTORY]

``-h``, ``--help``
   show command help information

``-i ID [ID ...]``, ``--id ID [ID ...]``
   |ID_DESCRIPTION|

``-a``, ``--append``
   append new comment instead of overwrite existing one

``comment``
   new comment

``DIRECTORY``
   directory which contain benchmarks, default: ``.``

.. index:: remove

remove
~~~~~~

Remove an existing benchmark

.. code-block:: none

   jube remove [-h] [-i ID [ID ...]] [-f] [DIRECTORY]

``-h``, ``--help``
   show command help information

``-i ID [ID ...]``, ``--id ID [ID ...]``
   |ID_DESCRIPTION|

``-f``, ``--force``
   do not prompt

``DIRECTORY``
   directory which contain benchmarks, default: ``.``

.. index:: info

info
~~~~

Get benchmark specific information

.. code-block:: none

   jube info [-h] [-i ID [ID ...]] [-s STEP [STEP ...]] [-p] [DIRECTORY]

``-h``, ``--help``
   show command help information

``-i ID [ID ...]``, ``--id ID [ID ...]``
   show benchmark specific information

``-s STEP [STEP ...]``, ``--step STEP [STEP ...]``
   show step specific information

``-c``, ``--csv-parametrization``
   display only parametrization of given step using *csv* format

``-p``, ``--parametrization``
   display only parametrization of given step

``DIRECTORY``
   show directory specific information

.. index:: log

log
~~~

Show logs for benchmark

.. code-block:: none

   jube log [-h] [-i ID [ID ...]] [-c COMMAND [COMMAND ...]] [DIRECTORY]

``-h``, ``--help``
   show command help information

``-i ID [ID ...]``, ``--id ID [ID ...]``
   |ID_DESCRIPTION|

``-c COMMAND [COMMAND ...]``, ``--command COMMAND [COMMAND ...]``
   show only logs for specified commands

``DIRECTORY``
   directory which contain benchmarks, default: .

.. index:: status

status
~~~~~~

Show benchmark status RUNNING or FINISHED.

.. code-block:: none

   jube status [-h] [-i ID [ID ...]] [DIRECTORY]

``-h``, ``--help``
   show command help information

``-i ID [ID ...]``, ``--id ID [ID ...]``
   |ID_DESCRIPTION|

``DIRECTORY``
   directory which contain benchmarks, default: .

.. index:: complete

complete
~~~~~~~~

Generate shell completion. Usage: ``eval "$(jube complete)"``

.. code-block:: none

   jube complete [-h] [--command-name COMMAND_NAME]

``-h``, ``--help``
   show command help information

``--command-name COMMAND_NAME``, ``-c COMMAND_NAME``
   name of command to be complete, default: programname which was used to run the ``complete`` command

.. index:: help

help
~~~~

Command help

.. code-block:: none

   jube help [-h] [command]

``-h``, ``--help``
   show command help information

``command``
   command to get help about

.. index:: update

update
~~~~~~

Check *JUBE* version

.. code-block:: none

   jube update [-h]

``-h``, ``--help``
   show command help information
