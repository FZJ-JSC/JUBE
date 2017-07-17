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

.. index:: advanced tutorial

Advanced tutorial
=================

.. highlight:: bash
   :linenothreshold: 5

This tutorial demonstrates more detailed functions and tools of *JUBE*. If you want a basic overview you should
read the general :doc:`tutorial` first.

.. index:: schema validation, validation, dtd

Schema validation
~~~~~~~~~~~~~~~~~
To validate your input files you can use DTD or schema validation. You will find ``jube.dtd``, ``jube.xsd``
and ``jube.rnc`` inside the ``schema`` folder. You have to add these schema information to your input files
which you want to validate.

DTD usage:

.. code-block:: xml
   :linenos:

   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE jube SYSTEM "<jube.dtd path>">
   <jube>
   ...

Schema usage:

.. code-block:: xml
   :linenos:

    <?xml version="1.0" encoding="UTF-8"?>
    <jube xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="<jube.xsd path>">
    ...

RELAX NG Compact Syntax (RNC for emacs nxml-mode) usage:

In order to use the provided rnc schema file ``schema/jube.rnc`` in
emacs open an xml file and use ``C-c C-s C-f`` or ``M-x
rng-set-schema-file-and-validate`` to choose the rnc file. You can
also use ``M-x customize-variable rng-schema-locating-files`` after
you loaded nxml-mode to customize the default search paths to include
``jube.rnc``. After successful parsing emacs offers to automatically
create a ``schema.xml`` file which looks like

.. code-block:: xml
   :linenos:

   <?xml version="1.0"?>
   <locatingRules xmlns="http://thaiopensource.com/ns/locating-rules/1.0">
      <uri resource="jube-file.xml" uri="../schema/jube.rnc"/>
   </locatingRules>

The next time you open the same xml file emacs will find the correct
rnc for the validation based on ``schema.xml``.

Example validation tools:

* eclipse (using DTD or schema)
* emacs (using RELAX NG)
* xmllint:

  * For validation (using the DTD)::

       >>> xmllint --noout --valid <xml input file>

  * For validation (using the DTD and Schema)::

       >>> xmllint --noout --valid --schema <schema file> <xml input file>

.. index:: scripting, perl, python

Scripting parameter
~~~~~~~~~~~~~~~~~~~
In some cases it is needed to create a parameter which is based on the value of another parameter.
In this case you can use a scripting parameter.

The files used for this example can be found inside ``examples/scripting_parameter``.

The input file ``scripting_parameter.xml``:

.. literalinclude:: ../examples/scripting_parameter/scripting_parameter.xml
   :language: xml

In this example we see four different parameters.

* ``number`` is a normal template which will be expanded to three different :term:`workpackages <workpackage>`.
* ``additional_number`` is a scripting parameter which creates a new template and bases on ``number``. The ``mode`` is set to the scripting language (``python`` and ``perl`` are allowed).
  The additional ``type`` is optional and declares the result type after evaluating the expression. The type is only used by the sort algorithm in the result step. It is not possible to
  create a template of different scripting parameters. Because of this second template we will get six different :term:`workpackages <workpackage>`.
* ``number_mult`` is a small calculation. You can use any other existing parameters (which are used inside the same step).
* ``text`` is a normal parameter which uses the content of another parameter. For a simple concatenation parameter you do not need a scripting
  parameter.

For this example we will find the following output inside the ``run.log``-file:

.. code-block:: none

   ====== operation ======
   >>> echo "number: 1, additional_number: 1"
   >>> echo "number_mult: 1, text: Number: 1"
   ====== operation ======
   >>> echo "number: 1, additional_number: 2"
   >>> echo "number_mult: 2, text: Number: 1"
   ====== operation ======
   >>> echo "number: 2, additional_number: 2"
   >>> echo "number_mult: 4, text: Number: 2"
   ====== operation ======
   >>> echo "number: 2, additional_number: 4"
   >>> echo "number_mult: 8, text: Number: 2"
   ====== operation ======
   >>> echo "number: 4, additional_number: 4"
   >>> echo "number_mult: 16, text: Number: 4"
   ====== operation ======
   >>> echo "number: 4, additional_number: 8"
   >>> echo "number_mult: 32, text: Number: 4"

Implicit Perl or Python scripting inside the ``<do>`` or any other position is not possible.
If you want to use some scripting expressions you have to create a new parameter.

.. index:: statistic values

.. _statistic_values:

Statistic pattern values
~~~~~~~~~~~~~~~~~~~~~~~~

Normally a pattern should only match a single entry in your result files. But sometimes there are multiple
similar entries (e.g. if the benchmark uses some iteration feature).

*JUBE* will create the statistical values ``last``, ``min``, ``max``, ``avg``, ``std``, ``cnt`` and ``sum`` automatically.
To use these values, the user had to specify the pattern name followed by ``_<statistic_option>``,
e.g. ``pattern_name_last`` (the pattern_name itself will always be the first match).

A example describing the reduce option can be found in ``examples/statistic``.

The input file ``statistic.xml``:

.. literalinclude:: ../examples/statistic/statistic.xml
   :language: xml

It will create the following output:

.. code-block:: none

   number_pat | number_pat_last | number_pat_min | number_pat_max | number_pat_sum | number_pat_cnt | number_pat_avg | number_pat_std
   -----------+-----------------+----------------+----------------+----------------+----------------+----------------+---------------
            1 |              10 |              1 |             10 |             55 |             10 |            5.5 |           3.03

.. index:: jobsystem

Jobsystem
~~~~~~~~~
In most cases you want to submit jobs by *JUBE* to your local jobsystem. You can use the normal file access and substitution system to prepare
your jobfile and send it to the jobsystem. *JUBE* also provide some additional features.

The files used for this example can be found inside ``examples/jobsystem``.

The input jobsystem file ``job.run.in`` for *Torque/Moab* (you can easily adapt your personal jobscript):

.. literalinclude:: ../examples/jobsystem/job.run.in
   :language: bash

The *JUBE* input file ``jobsystem.xml``:

.. literalinclude:: ../examples/jobsystem/jobsystem.xml
   :language: xml

As you can see the jobfile is very general and several parameters will be used for replacement. By using a general jobfile and the substitution mechanism
you can control your jobsystem directly out of your *JUBE* input file.

The submit command is a normal *Shell* command so there are no special *JUBE* tags to submit a job.

There are two new attributes:

  * ``done_file`` inside the ``<do>`` allows you to set a filename/path to a file which should be used by the jobfile to mark the end of execution. *JUBE* does not know when the job ends.
    Normally it will return when the *Shell* command was finished. When using a jobsystem we had to wait until the jobfile was executed. If *JUBE* found a
    ``<do>`` containing a ``done_file`` attribute *JUBE* will return directly and will not continue automatically until the ``done_file`` exists. If you want to check the current status
    of your running steps and continue the benchmark process if possible you can type::

       >>> jube continue bench_run

    This will continue your benchmark execution (``bench_run`` is the benchmarks directory in this example). The position of the ``done_file`` is relativly seen towards the work directory.
  * ``work_dir`` can be used to change the sandbox work directory of a step. In normal cases *JUBE* checks that every work directory gets an unique name. When changing the directory the user must select a
    unique name by his own. For example he can use ``$jube_benchmark_id`` and ``$jube_wp_id``, which are *JUBE* :term:`internal parameters <jube_variables>` and will be expanded to the current benchmark and workpackage ids. Files and directories out of a given
    ``<fileset>`` will be copied into the new work directory. Other automatic links, like the dependency links, will not be created!

You will see this Output after running the benchmark:

.. code-block:: none

   stepname | all | open | wait | error | done
   ---------+-----+------+------+-------+-----
     submit |   3 |    0 |    3 |     0 |    0

and this output after running the ``continue`` command (after the jobs where executed):

.. code-block:: none

   stepname | all | open | wait | error | done
   ---------+-----+------+------+-------+-----
     submit |   3 |    0 |    0 |     0 |    3

You have to run ``continue`` multiple times if not all ``done_file`` were written when running ``continue`` for the first time.

.. index:: include

Include external data
~~~~~~~~~~~~~~~~~~~~~

As you have seen in the example before a benchmark can become very long. To structure your benchmark you can use multiple files and reuse existing
sets. There are three different include features available.

The files used for this example can be found inside ``examples/include``.

The include file ``include_data.xml``:

.. literalinclude:: ../examples/include/include_data.xml
   :language: xml

All files which contain data to be included must use the *XML*-format. The include files can have a user specific structure (there can be none valid
*JUBE* tags like ``<dos>``), but the structure must be allowed by the searching mechanism (see below). The resulting file must have a valid *JUBE* structure.

The main file ``main.xml``:

.. literalinclude:: ../examples/include/main.xml
   :language: xml

In these file there are three different include types:

The ``init_with`` can be used inside any set definition. Inside the given file the search mechanism will search for the same set (same type, same name), will parse its structure (this must be *JUBE* valid) and copy the content to
``main.xml``. Inside ``main.xml`` you can add additional values or overwrite existing ones. If your include-set uses a different name inside your include file you can use ``init_with="filename.xml:new_name"``.

The second method is the ``<use from="...">``. This is mostly the same like the ``init_with`` structure, but in this case you are not able to add or overwrite some values. The external set will be used directly. There is no set-type inside the ``<use>``, because of that, the set's name must
be unique inside the include-file.

The last method is the most generic include. By using ``<include />`` you can copy any *XML*-nodes you want to your main-*XML* file. The included file can provide tags which are not *JUBE*-conform but it must be a valid *XML*-file (e.g. only one root node allowed). The
resulting main configuration file must be completely *JUBE* valid.
The ``path`` is optional and can be used to select a specific node set (otherwise the root-node itself will be included). The ``<include />`` is the only
include-method that can be used to include any tag you want. The ``<include />`` will copy all parts without any changes. The other include types will update path names, which were relative to the include-file position.

To run the benchmark you can use the normal command::

   >>> jube run main.xml

It will search for include files inside four different positions (in the following order):


* inside a directory given over the command line interface::

     >>> jube run --include-path some_path another_path -- main.xml

* inside any path given by a ``<include-path>``-tag:

  .. code-block:: xml
     :linenos:

     <?xml version="1.0" encoding="UTF-8"?>
     <benchmarks>
       <include-path>
         <path>some_path</path>
         <path>another_path</path>
       </include-path>
       ...

* inside any path given with the ``JUBE_INCLUDE_PATH`` environment variable (see :ref:`configuration`)::

     >>> export JUBE_INCLUDE_PATH=some_path:another_path

* inside the same directory of your ``main.xml``

.. index:: tagging

Tagging
~~~~~~~

:term:`Tagging <tagging>` is a easy way to hide selectable parts of your input file.

The files used for this example can be found inside ``examples/tagging``.

The input file ``tagging.xml``:

.. literalinclude:: ../examples/tagging/tagging.xml
   :language: xml

When running this example::

   >>> jube run tagging.xml

all ``<tags>`` which contain a special ``tag="..."`` attribute will be hidden. ``!deu`` stands for ``not deu`` so this
tag will not be hidden when running the command.

The result inside the ``stdout`` file will be

.. code-block:: none

   $hello_str World

because there was no alternative to select the ``$hello_str``.

When running this example using a specific ``tag``::

   >>> jube run tagging.xml --tag eng

the result inside the ``stdout`` file will be

.. code-block:: none

   Hello World

The ``tag`` attribute or the command line expression can also contain a list of different names. A hidden ``<tag>`` will
be ignored completely! If there is no alternative this can produce a wrong execution behaviour!

The ``tag`` attribute can be used inside every ``<tag>`` inside the input file (except the ``<jube>``).

.. index:: platform independent

Platform independent benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to create platform independent benchmarks you can use the include features inside of *JUBE*.

All platform related sets must be declared in a includable file e.g. ``platform.xml``. There can be multiple ``platform.xml`` in different
directories to allow different platforms. By changing the ``include-path`` the benchmark changes its platform specific data.

An example benchmark structure bases on three include files:

* The main benchmark include file which contain all benchmark specific but platform independent data
* A mostly generic platform include file which contain benchmark independent but platform specific data (this can be created once and placed somewhere
  central on the system, it can be easily accessed using the ``JUBE_INCLUDE_PATH`` environment variable.
* A platform specific and benchmark specific include file which must be placed in a unique directory to allow inlcude-path usage

Inside the ``platform`` directory you will find some example benchmark independent platform configuration files for the supercomputers at
Forschungszentrum Jülich.

To avoid writing long include-pathes every time you run a platform independent benchmark, you can store the include-path inside your
input file. This can be mixed using the tagging-feature:

.. code-block:: xml
   :linenos:

   <?xml version="1.0" encoding="UTF-8"?>
   <jube>
     <include-path>
       <path tag="plat1">some path</path>
       <path tag="plat2">another path</path>
       ...
     </include-path>
     ...
   </jube>

Now you can run your benchmark using::

   >>> jube run filename.xml --tag plat1

.. index:: multiple benchmarks

Multiple benchmarks
~~~~~~~~~~~~~~~~~~~

Often you only have one benchmark inside your input file. But it is also possible to store multiple benchmarks inside the same input file:

.. code-block:: xml
   :linenos:

   <?xml version="1.0" encoding="UTF-8"?>
   <jube>
     <benchmark name="a" outpath="bench_runs">...</benchmark>
     <benchmark name="b" outpath="bench_runs">...</benchmark>
     ...
   </jube>

All benchmarks can use the same global (as a child of ``<jube>``) declared sets. Often it might be better to use an include feature instead.
*JUBE* will run every benchmark in the given order. Every benchmark gets an unique benchmark id.

To select only one benchmark you can use::

   >>> jube run filename.xml --only-bench a

or::

   >>> jube run filename.xml --not-bench b

This information can also be stored inside the input file:

.. code-block:: xml
   :linenos:

   <?xml version="1.0" encoding="UTF-8"?>
   <jube>
     <selection>
       <only>a</only>
       <not>b</not>
     </selection>
     ...
   </jube>

.. index:: shared operations

Shared operations
~~~~~~~~~~~~~~~~~

Sometimes you want to communicate between the different workpackages of a single step or you want a single operation to run only once
for all workpackages. Here you can use shared steps.

The files used for this example can be found inside ``examples/shared``.

The input file ``shared.xml``:

.. literalinclude:: ../examples/shared/shared.xml
   :language: xml

The step must be marked using the ``shared`` attribute. The name, given inside this attribute, will be the name of a symbolic link, which will be created
inside every single sandbox work directory pointing to a single shared folder. Every Workpackage can access this folder by using its own link. In this example
every workpackage will write its own id into a shared file (``$jube_wp_id`` is an internal variable, more of these you will find :term:`here <jube_variables>`).

To mark an operation to be a shared operation ``shared="true"`` inside the ``<do>`` must be used. The shared operation will start after all workpackages reached its
execution position. The work directory for the shared operation is the shared folder itself.

You will get the following directory structure:

.. code-block:: none

   bench_run               # the given outpath
   |
   +- 000000               # the benchmark id
      |
      +- configuration.xml # the stored benchmark configuration
      +- workpackages.xml  # workpackage information
      +- 000000_a_step     # the first workpackage
         |
         +- done           # workpackage finished marker
         +- work           # user sandbox folder
            |
            +- stderr      # standard error messages of used shell commands
            +- stdout      # standard output of used shell commands
            +- shared      # symbolic link pointing to shared folder
      +- 000001_a_step     # workpackage information
      +- 000002_a_step     # workpackage information
      +- a_step_shared     # the shared folder
         |
         +- stdout         # standard output of used shell commands
         +- stderr         # standard error messages of used shell commands
         +- all_ids        # benchmark specific generated file

.. index:: environment handling

Environment handling
~~~~~~~~~~~~~~~~~~~~

*Shell* environment handling can be very important to configure pathes or parameter of your program.

The files used for this example can be found inside ``examples/environment``.

The input file ``environment.xml``:

.. literalinclude:: ../examples/environment/environment.xml
   :language: xml

In normal cases all ``<do>`` within one ``<step>`` shares the same environment. All **exported** variables of one ``<do>``
will be available inside the next ``<do>`` within the same ``<step>``.

By using ``export="true"`` inside of a ``<parameter>`` you can export additional variables to your *Shell* environment. Be aware that this example uses
``$$`` to explicitly use *Shell* substitution instead of *JUBE* substitution.

You can also export the complete environment of a step to a dependent step by using ``export="true"`` inside of ``<step>``.

.. index:: parameter dependencies

.. _parameter-dependencies:

Parameter dependencies
~~~~~~~~~~~~~~~~~~~~~~

Sometimes you need parameters which based on other parameters or only a specific parameter combination make sense and other combinations
are useless or wrong. For this there are several techniques inside of *JUBE* to create such a more complex workflow.

The files used for this example can be found inside ``examples/parameter_dependencies``.

The input file ``parameter_dependencies.xml``:

.. literalinclude:: ../examples/parameter_dependencies/parameter_dependencies.xml
   :language: xml

The include file ``include_file.xml``:

.. literalinclude:: ../examples/parameter_dependencies/include_file.xml
   :language: xml

The easiest way to handle dependencies is to define an index-parameter which can be used in other scripting parameters
to combine all dependent parameter combinations.

Also complete sets can be marked as dependent towards a specific parameter by using this parameter in the ``<use>``-tag. When using parametersets
out of an other file the correct set-name must be given within the ``from`` attribute, because these sets will be loaded in a pre-processing step before the
corresponding parameter will be evaluated. Also sets out of different files can be combined within the same ``<use>`` by using the 
``file1:set1,file2:set2`` syntax. The sets' names must be unique.
