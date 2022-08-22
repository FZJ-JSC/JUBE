.. # JUBE Benchmarking Environment
   # Copyright (C) 2008-2022
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
To validate your *XML* based input files you can use DTD or schema validation. You will find ``jube.dtd``, ``jube.xsd``
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

.. index:: scripting, perl, python, shell

.. _scripting_parameter:

Scripting parameter
~~~~~~~~~~~~~~~~~~~
In some cases it is needed to create a parameter which is based on the value of another parameter.
In this case you can use a scripting parameter.

The files used for this example can be found inside ``examples/scripting_parameter``.

The input file ``scripting_parameter.xml``:

.. literalinclude:: ../examples/scripting_parameter/scripting_parameter.xml
   :language: xml

The input file ``scripting_parameter.yaml``:

.. literalinclude:: ../examples/scripting_parameter/scripting_parameter.yaml
   :language: yaml

In this example we see four different parameters.

* ``number`` is a normal template which will be expanded to three different :term:`workpackages <workpackage>`.
* ``additional_number`` is a scripting parameter which creates a new template and bases on ``number``. The ``mode`` is set to the scripting language (``python``, ``perl`` and ``shell`` are allowed).
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

.. index:: scripting, pattern, perl, python, shell

.. _scripting_pattern:

Scripting pattern
~~~~~~~~~~~~~~~~~

Similar to the :ref:`scripting_parameter`, also different patterns, or patterns and parameters can be combined.
For this a scripting pattern can be created by using the ``mode=`` attribute in the same way as it is used for the :ref:`scripting_parameter`.

All scripting patterns are evaluated at the end of the analyse part. Each scripting pattern is evaluated once. If there are multiple matches
as described in the :ref:`statistic_values` section, only the resulting statistical pattern is available (not each individual value). Scripting pattern
do not create statistic values by themselves.

In addition the ``default=`` attribute can be used to set a default pattern value, if the value can't be found during the analysis.

The files used for this example can be found inside ``examples/scripting_pattern``.

The input file ``scripting_pattern.xml``:

.. literalinclude:: ../examples/scripting_pattern/scripting_pattern.xml
   :language: xml

The input file ``scripting_pattern.yaml``:

.. literalinclude:: ../examples/scripting_pattern/scripting_pattern.yaml
   :language: yaml

It will create the following output:

.. code-block:: none

   | value | value_pat | dep_pat | missing_pat | missing_dep_pat | missing_pat_def | missing_def_dep_pat |
   |-------|-----------|---------|-------------|-----------------|-----------------|---------------------|
   |     0 |         0 |       0 |             |             nan |               0 |                   0 |
   |     1 |         1 |       2 |             |             nan |               0 |                   0 |
   |     2 |         2 |       4 |             |             nan |               0 |                   0 |

.. index:: statistic values

.. _statistic_values:

Statistic pattern values
~~~~~~~~~~~~~~~~~~~~~~~~

Normally a pattern should only match a single entry in your result files. But sometimes there are multiple
similar entries (e.g. if the benchmark uses some iteration feature).

*JUBE* will create the statistical values ``last``, ``min``, ``max``, ``avg``, ``std``, ``cnt`` and ``sum`` automatically.
To use these values, the user have to specify the pattern name followed by ``_<statistic_option>``,
e.g. ``pattern_name_last`` (the pattern_name itself will always be the first match).

An example for multiple matches and the statistic values can be found in ``examples/statistic``.

The input file ``statistic.xml``:

.. literalinclude:: ../examples/statistic/statistic.xml
   :language: xml

The input file ``statistic.yaml``:

.. literalinclude:: ../examples/statistic/statistic.yaml
   :language: yaml

It will create the following output:

.. code-block:: none

   | number_pat | number_pat_last | number_pat_min | number_pat_max | number_pat_sum | number_pat_cnt | number_pat_avg | number_pat_std |
   |------------|-----------------|----------------|----------------|----------------|----------------|----------------|----------------|
   |          1 |              10 |              1 |             10 |             55 |             10 |            5.5 |           3.03 |

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

The *JUBE* input file ``jobsystem.yaml``:

.. literalinclude:: ../examples/jobsystem/jobsystem.yaml
   :language: yaml

As you can see the jobfile is very general and several parameters will be used for replacement. By using a general jobfile and the substitution mechanism
you can control your jobsystem directly out of your *JUBE* input file. 
``$$`` is used for *Shell* substitutions instead of *JUBE* substitution (see :ref:`environment-handling`).

The submit command is a normal *Shell* command so there are no special *JUBE* tags to submit a job.

There are two new attributes:

  * ``done_file`` inside the ``<do>`` allows you to set a filename/path to a file which should be used by the jobfile to mark the end of execution. *JUBE* does not know when the job ends.
    Normally it will return when the *Shell* command was finished. When using a jobsystem the user usually have to wait until the jobfile is executed. If *JUBE* found a
    ``<do>`` containing a ``done_file`` attribute *JUBE* will return directly and will not continue automatically until the ``done_file`` exists. If you want to check the current status
    of your running steps and continue the benchmark process if possible you can type::

       >>> jube continue bench_run

    This will continue your benchmark execution (``bench_run`` is the benchmarks directory in this example). The position of the ``done_file`` is relatively seen towards the work directory.
  * ``work_dir`` can be used to change the sandbox work directory of a step. In normal cases *JUBE* checks that every work directory gets a unique name. When changing the directory the user must select a
    unique name by his own. For example he can use ``$jube_benchmark_id`` and ``$jube_wp_id``, which are *JUBE* :term:`internal parameters <jube_variables>` and will be expanded to the current benchmark and workpackage ids. Files and directories out of a given
    ``<fileset>`` will be copied into the new work directory. Other automatic links, like the dependency links, will not be created!

You will see this Output after running the benchmark:

.. code-block:: none

   | stepname | all | open | wait | error | done |
   |----------|-----|------|------|-------|------|
   |   submit |   3 |    0 |    3 |     0 |    0 |

and this output after running the ``continue`` command (after the jobs where executed):

.. code-block:: none

   | stepname | all | open | wait | error | done |
   |----------|-----|------|------|-------|------|
   |   submit |   3 |    0 |    0 |     0 |    3 |

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

The include file ``include_data.yaml``:

.. literalinclude:: ../examples/include/include_data.yaml
   :language: yaml

All files which contain data to be included must use the *XML*-format. The include files can have a user specific structure (there can be no valid
*JUBE* tags like ``<dos>``), but the structure must be allowed by the searching mechanism (see below). The resulting file must have a valid *JUBE* structure.

The main file ``main.xml``:

.. literalinclude:: ../examples/include/main.xml
   :language: xml

The main file ``main.yaml``:

.. literalinclude:: ../examples/include/main.yaml
   :language: yaml

In these file there are three different include types:

The ``init_with`` can be used inside any set definition. Inside the given file the search mechanism will search for the same set (same type, same name), will parse its structure (this must be *JUBE* valid) and copy the content to
``main.xml``. Inside ``main.xml`` you can add additional values or overwrite existing ones. If your include-set uses a different name inside your include file you can use ``init_with="filename.xml:old_name"``. It is possible to mix *YAML* based
include files with *XML* files and vice versa.

The second method is the ``<use from="...">``. This is mostly the same like the ``init_with`` structure, but in this case you are not able to add or overwrite some values. The external set will be used directly. There is no set-type inside the ``<use>``, because of that, the set's name must
be unique inside the include-file. The remote file can use the *YAML* or the *XML* format.

The last method is the most generic include. The include mechanic is the only element in *JUBE* which works slightly different in *YAML* and *XML* based files.

In *XML* based files by using ``<include />`` you can copy any *XML*-nodes you want to your main-*XML* file. The included file can provide tags which are not *JUBE*-conform but it must be a valid *XML*-file (e.g. only one root node allowed). The
resulting main configuration file must be completely *JUBE* valid.
The ``path`` is optional and can be used to select a specific node set (otherwise the root-node itself will be included). The ``<include />`` is the only
include-method that can be used to include any tag you want. The ``<include />`` will copy all parts without any changes. The other include types will update path names, which were relative to the include-file position.

In *YAML* based files the prefix ``! include`` is used followed by the file name. The file must be a *YAML* file, which will be opened and parsed. The second block `:["dos"]` can be used to select any subset of data of the full dictionary, any Python syntax is allowed for this selection.
Finally it is possible to also specify a third block which allows full Python list comprehensions. ``_`` is the match of the selection before, e.g.: ``!include include_data.yaml:["dos"]:[i for i in _ if "Test" in i]``. In contrast to the *XML* based include it isn't possible to mix lists
or dictionaries out of different files, each key can only handle a single include.

To run the benchmark you can use the normal command::

   >>> jube run main.xml

It will search for the files to include inside four different positions, in the following order:

* inside a directory given over the command line interface::

     >>> jube run --include-path some_path another_path -- main.xml

* inside any path given by an ``<include-path>``-tag:

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

*JUBE* stops searching as soon as it finds the file to include, or gives an error if the file is not found.

.. index:: tagging

.. _tagging:

Tagging
~~~~~~~

:term:`Tagging <tagging>` is an easy way to hide selectable parts of your input file.

The files used for this example can be found inside ``examples/tagging``.

The input file ``tagging.xml``:

.. literalinclude:: ../examples/tagging/tagging.xml
   :language: xml

The input file ``tagging.yaml``:

.. literalinclude:: ../examples/tagging/tagging.yaml
   :language: yaml

When running this example::

   >>> jube run tagging.xml

All ``<tags>`` which contain a special ``tag="..."`` attribute will be hidden if the tag results to ``false``. ``!deu`` stands for ``not deu``. 
To connect the ``tags`` ``|`` can be used as the oprator OR and ``+`` for the operator AND. Also brackets are allowed.

The result (if no ``tag`` is set on the commandline) inside the ``stdout`` file will be

.. code-block:: none

   Hallo $world_str
   
because ``!deu+eng`` and ``eng`` will be ``false`` and there is no other input available for ``$world_str``. ``deu|!eng`` will be ``true``.  

When running the same example using a specific ``tag``::

   >>> jube run tagging.xml --tag eng

the result inside the ``stdout`` file will be

.. code-block:: none

   Hello World

A ``tag`` which results to ``false`` will trigger to complety ignore the corresponding ``<tag>``! If there is no alternative this can produce a wrong execution behaviour!

Also a list of tags, separated by spaces, can be provided on the commandline.

The ``tag`` attribute can be used inside every ``<tag>`` inside the input file (except the ``<jube>``).

.. index:: platform independent

Platform independent benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to create platform independent benchmarks you can use the include features inside of *JUBE*.

All platform related sets must be declared in an includable file e.g. ``platform.xml``. There can be multiple ``platform.xml`` in different
directories to allow different platforms. By changing the ``include-path`` the benchmark changes its platform specific data.

An example benchmark structure is based on three include files:

* The main benchmark include file which contain all benchmark specific but platform independent data
* A mostly generic platform include file which contain benchmark independent but platform specific data (this can be created once and placed somewhere
  central on the system, it can be easily accessed using the ``JUBE_INCLUDE_PATH`` environment variable.
* A platform specific and benchmark specific include file which must be placed in a unique directory to allow inlcude-path usage

Inside the ``platform`` directory you will find some example benchmark independent platform configuration files for the supercomputers at
Forschungszentrum Jülich.

To avoid writing long include-paths every time you run a platform independent benchmark, you can store the include-path inside your
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

.. code-block:: yaml
   :linenos:

   - name: a
     # data for benchmark a
   - name: b
     # data for benchmark b

All benchmarks can use the same global (as a child of ``<jube>``) declared sets. Often it might be better to use an include feature instead.
*JUBE* will run every benchmark in the given order. Every benchmark gets a unique benchmark id.

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

The input file ``shared.yaml``:

.. literalinclude:: ../examples/shared/shared.yaml
   :language: yaml

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

.. _environment-handling:

Environment handling
~~~~~~~~~~~~~~~~~~~~

*Shell* environment handling can be very important to configure paths or parameter of your program.

The files used for this example can be found inside ``examples/environment``.

The input file ``environment.xml``:

.. literalinclude:: ../examples/environment/environment.xml
   :language: xml

The input file ``environment.yaml``:

.. literalinclude:: ../examples/environment/environment.yaml
   :language: yaml

In normal cases all ``<do>`` within one ``<step>`` shares the same environment. All **exported** variables of one ``<do>``
will be available inside the next ``<do>`` within the same ``<step>``.

By using ``export="true"`` inside of a ``<parameter>`` you can export additional variables to your *Shell* environment. Be aware that this example uses
``$$`` to explicitly use *Shell* substitution instead of *JUBE* substitution.

You can also export the complete environment of a step to a dependent step by using ``export="true"`` inside of ``<step>``.

.. index:: parameter dependencies

.. _parameter-dependencies:

Parameter dependencies
~~~~~~~~~~~~~~~~~~~~~~

Sometimes you need parameters which are based on other parameters or only a specific parameter combination makes sense and other combinations
are useless or wrong. For this there are several techniques inside of *JUBE* to create such a more complex workflow.

The files used for this example can be found inside ``examples/parameter_dependencies``.

The input file ``parameter_dependencies.xml``:

.. literalinclude:: ../examples/parameter_dependencies/parameter_dependencies.xml
   :language: xml

The input file ``parameter_dependencies.yaml``:

.. literalinclude:: ../examples/parameter_dependencies/parameter_dependencies.yaml
   :language: yaml

The include file ``include_file.xml``:

.. literalinclude:: ../examples/parameter_dependencies/include_file.xml
   :language: xml

The include file ``include_file.yaml``:

.. literalinclude:: ../examples/parameter_dependencies/include_file.yaml
   :language: yaml

The easiest way to handle dependencies is to define an index-parameter which can be used in other scripting parameters
to combine all dependent parameter combinations.

Also complete sets can be marked as dependent towards a specific parameter by using this parameter in the ``<use>``-tag. When using parametersets
out of an other file the correct set-name must be given within the ``from`` attribute, because these sets will be loaded in a pre-processing step before the
corresponding parameter will be evaluated. Also sets out of different files can be combined within the same ``<use>`` by using the 
``file1:set1,file2:set2`` syntax. The sets names must be unique.

.. index:: parameter update

.. _parameter_update_mode:

Parameter update
~~~~~~~~~~~~~~~~

Once a parameter is specified and evaluated the first time, its value will not change. Sometimes this behaviour can produce the wrong behaviour:

.. code-block:: xml

   <parameter name="foo">$jube_wp_id</parameter>

In this example ``foo`` should hold the ``$jube_wp_id``. If you have two steps, where one step depends on the other one ``foo`` will be available in both, but it will only be evaluated in
the first one.

There is a simple workaround to change the update behaviour of a parameter by using the attribute ``update_mode``:

* ``update_mode="never"`` No update (default behaviour)
* ``update_mode="use"`` Re-evaluate the parameter if the parameterset is explicitly used
* ``update_mode="step"`` Re-evaluate the parameter for each new step
* ``update_mode="cycle"`` Re-evaluate the parameter for each new cycleloop, but not at the begin of a new step
* ``update_mode="always"`` Combine step and cycle

Within a cycle loop no new workpackages can be created. Templates will be reevaluated, but they can not increase the number of existing workpackages within a cycle.

Within the result generation, the parameter value, which is presented in the result table is the value of the selected analysed step. If another parameter representation is needed as well,
all other steps can be reached by using ``<parameter_name>_<step_name>``.

The files used for this example can be found inside ``examples/parameter_update``.

The input file ``parameter_update.xml``:

.. literalinclude:: ../examples/parameter_update/parameter_update.xml
   :language: xml

The input file ``parameter_update.yaml``:

.. literalinclude:: ../examples/parameter_update/parameter_update.yaml
   :language: yaml

The use and influence of the three update modes ``update_mode="never"``, ``update_mode="use"`` and ``update_mode="step"`` is shown here. Keep in mind, that the steps have to be dependent
from each other leading to identical outputs otherwise.

.. index:: iteration

.. _step_iteration:

Step iteration
~~~~~~~~~~~~~~

Especially in the context of benchmarking, an application should be executed multiple times to generate some meaningful statistical values.
The handling of statistical values is described in :ref:`statistic_values`. This allows you to aggregate multiple result lines if your application 
automatically support to run multiple times.

In addition there is also an iteration feature within JUBE to run a specific step and its parametrisation multiple times.

The files used for this example can be found inside ``examples/iterations``.

The input file ``iterations.xml``:

.. literalinclude:: ../examples/iterations/iterations.xml
   :language: xml

The input file ``iterations.yaml``:

.. literalinclude:: ../examples/iterations/iterations.yaml
   :language: yaml

In this example, both steps 1 and 2 are executed 2 times for each parameter and dependency configuration. Because of the given parameter, step 1
is executed 6 times in total (3 parameter combinations x 2). Step 2 is executed 12 times (6 from the dependent step x 2). Each run will be executed in the normal way
using its individual sandbox folder.

``$jube_wp_iteration`` holds the individual iteration id. The ``update_mode`` is needed here to reevaluate the parameter ``bar`` in step 2.

In the analyser ``reduce=true`` or ``reduce=false`` can be enabled, to allow you to see all individual results or to aggregate all results of the same parameter combination.
for the given step. If ``reduce=true`` is enabled (the default behaviour) the output of the individual runs, which uses the same parametrisation, are treated like a big continuous file
before applying the statistical patterns.

.. code-block:: none

   | jube_res_analyser | jube_wp_id_first_step | jube_wp_id | jube_wp_iteration_first_step | jube_wp_iteration | foo |
   |-------------------|-----------------------|------------|------------------------------|-------------------|-----|
   | analyse_no_reduce |                     0 |          6 |                            0 |                 0 |   1 |
   | analyse_no_reduce |                     0 |          7 |                            0 |                 1 |   1 |
   | analyse_no_reduce |                     1 |          8 |                            1 |                 2 |   1 |
   | analyse_no_reduce |                     1 |          9 |                            1 |                 3 |   1 |
   | analyse_no_reduce |                     2 |         10 |                            0 |                 0 |   2 |
   | analyse_no_reduce |                     2 |         11 |                            0 |                 1 |   2 |
   | analyse_no_reduce |                     3 |         12 |                            1 |                 2 |   2 |
   | analyse_no_reduce |                     3 |         13 |                            1 |                 3 |   2 |
   | analyse_no_reduce |                     4 |         14 |                            0 |                 0 |   4 |
   | analyse_no_reduce |                     4 |         15 |                            0 |                 1 |   4 |
   | analyse_no_reduce |                     5 |         16 |                            1 |                 2 |   4 |
   | analyse_no_reduce |                     5 |         17 |                            1 |                 3 |   4 |
   |           analyse |                     5 |         16 |                            1 |                 2 |   4 |
   |           analyse |                     0 |          7 |                            0 |                 1 |   1 |
   |           analyse |                     1 |          8 |                            1 |                 2 |   1 |
   |           analyse |                     2 |         10 |                            0 |                 0 |   2 |
   |           analyse |                     3 |         12 |                            1 |                 2 |   2 |
   |           analyse |                     4 |         15 |                            0 |                 1 |   4 |

.. index:: cycle

.. _step_cycle:

Step cycle
~~~~~~~~~~

Instead of having a new workpackage you can also redo the ``<do>`` commands inside a step using the cycle-feature. 
In contrast to the iterations, all executions for the cycle feature take place inside the same folder.

The files used for this example can be found inside ``examples/cycle``.

The input file ``cycle.xml``:

.. literalinclude:: ../examples/cycle/cycle.xml
   :language: xml

The ``cycles`` attribute allows to repeat all ``<do>`` commands within a step multiple times. The ``break_file`` can be used to cancel the loop and all following commands in the current cycle (the command
itself is still executed). In the given example the output will be:

.. code-block:: none

   0
   1
   2
   3

In contrast to the iterations, all executions for the cycle feature take place inside of the same folder.

.. index:: parallel

.. _parallel_workpackage:

Parallel workpackages
~~~~~~~~~~~~~~~~~~~~~

In a standard ``jube run`` a queue is filled with workpackages and then 
processed in serial. To enable parallel execution of independent workpackages, 
which belong to the expansions of a step, the argument ``procs`` of ``<step>`` 
can be used.  

The files used for this example can be found inside ``examples/parallel_workpackages``.
The input file ``parallel_workpackages.xml``:

.. literalinclude:: ../examples/parallel_workpackages/parallel_workpackages.xml
   :language: xml

.. literalinclude:: ../examples/parallel_workpackages/parallel_workpackages.yaml
   :language: yaml

In the example above the expansion of the parameter ``i`` will lead to the 
creation of 10 workpackages of the step ``parallel_execution``. Due to the 
given argument ``procs="4"`` JUBE will start 4 worker processes which will 
distribute the execution of the workpackages among themselves. ``N`` 
within the JUBE script represents the number of computation iterations to 
simulate a computational workload at hand. The parameters ``N``, ``procs`` 
and the upper bound of ``range`` within this prototypical example can be 
alternated to study runtime, memory usage and load of CPUs.

**Important hints:**

* ``<do shared="true">`` is not supported if ``procs`` is set for the 
  corresponding step.
* If ``<step shared="...">`` is set, then the user is responsible to avoid data 
  races within the shared directory.
* Switching to an alternative ``work_dir`` for a step can also lead to data 
  races if all expansions of the step access the same ``work_dir``. 
  Recommendation: Don't use a shared ``work_dir`` in combination with ``procs``.
* This feature is implemented based on the Python package ``multiprocessing`` 
  and doesn't support inter-node communication. That's why the parallelisation 
  is limited to a single shared memory compute node.
* Be considerate when working on a multi-user system with shared resources. 
  The parallel feature of JUBE can easily exploit a whole compute node. 
* Parallel execution of a JUBE script can lead to much higher memory demand 
  compared to serial execution with ``procs=1``. In this case it is advised to 
  reduce ``procs`` leading to reduced memory usage.

.. index:: database

.. _result_database:

Result database
~~~~~~~~~~~~~~~

Results can also be stored into a database to simplify result management.

The files used for this example can be found inside ``examples/result_database``.

The input file ``result_database.xml``:

.. literalinclude:: ../examples/result_database/result_database.xml
   :language: xml

The input file ``result_database.yaml``:

.. literalinclude:: ../examples/result_database/result_database.yaml
   :language: yaml

The default database will be located as follows and has the ``database`` tag name, which is here ``results``, as root name concatenated with the appendix ``.dat``:

.. code-block:: none

   bench_run
   |
   +- 000000
      |
      +- result
         |
         +- results.dat

The ``database`` tag takes the argument ``name``. ``name`` is also the name of the table created within a database. If ``sqlite3`` is installed the contents of the database can be shown with the following command line.

.. code-block:: none

   >>> sqlite3 -header -table bench_run/000000/result/results.dat 'SELECT * FROM results'
   +--------+------------+
   | number | number_pat |
   +--------+------------+
   | 1      | 1          |
   | 2      | 2          |
   | 4      | 4          |
   +--------+------------+

The argument ``file`` states the full path of a second copy of the database file. The path can be stated relative or absolute. In this case the database file ``result_database.dat`` is created within the current working directory in which ``jube result`` was invoked. 

Invocating ``jube result`` a second time updates the database given by the ``file`` parameter. Without the parameter ``primekeys`` three additional lines to the ``results`` table would have been added which are completely identical to the previous three lines. Adding the argument ``primekeys`` ensures that only if the column values stated within ``primekeys`` are not exactly the same in the database table, a new line is added to the database table. In this example no new lines are added. All the ``primekeys`` also need to be stated as ``key``. Updating the ``primekeys`` is not supported.

The ``key`` tag adds columns to the database table having the same type as the corresponding ``parameter`` or ``pattern``. Information of columns of the database table ``results`` can be shown as follows.

.. code-block:: none

   >>> sqlite3 -header -table bench_run/000000/result/results.dat 'PRAGMA table_info(results)'
   +-----+------------+------+---------+------------+----+
   | cid |    name    | type | notnull | dflt_value | pk |
   +-----+------------+------+---------+------------+----+
   | 0   | number     | int  | 0       |            | 1  |
   | 1   | number_pat | int  | 0       |            | 2  |
   +-----+------------+------+---------+------------+----+

To have a look into a database within a python script the python modules `sqalchemy <https://www.sqlalchemy.org/>`_ or `pandas <https://pandas.pydata.org>`_ can be used.

.. index:: do log

.. _do_log:

Creating a do log
~~~~~~~~~~~~~~~~~

To increase reproducibility of the do statements within a workpackage of a step and to archive the environment during execution, a do log can be printed. A do log tries to mimic an executable script recreating the environment at execution time. The files used for this example can be found inside ``examples/do_log``.

The input file ``do_log.xml``:

.. literalinclude:: ../examples/do_log/do_log.xml
   :language: xml

The input file ``do_log.yaml``:

.. literalinclude:: ../examples/do_log/do_log.yaml
   :language: yaml

In this example a hidden string is searched for within 5 files and the name of the file containing the hidden string is printed.

For the initial execution of this example within ``bench_run/000000/00000[0-4]_execute`` each can be found a ``do_log`` file. These files can be executed manually by prefixing it with ``/bin/sh``. The scripts will reproduce the environment at execution time, the execution and the result output. Keep in mind that the shared ``grep`` will be executed by the benchmark with id 4 only.

The duplicate option
~~~~~~~~~~~~~~~~~~~~

To simplify advanced tagging and parameter concatenation the ``duplicate`` option within parametersets or parameters can be stated.

The input file ``duplicate.xml``:

.. literalinclude:: ../examples/duplicate/duplicate.xml
   :language: xml

The input file ``duplicate.yaml``:

.. literalinclude:: ../examples/duplicate/duplicate.yaml
   :language: yaml

In this example the ``duplicate`` option with the value ``concat`` is stated for a parameterset. This leads to a concatenation of parameter values of the same name. In combination with the tagging option for parameters the user can specify which options are included into the parameters. If the user states the tags ``few`` and ``many`` the parameter ``iterations`` takes the values ``1,2,3,4,20,30,40``.

The default option of ``duplicate`` for parametersets is ``replace`` which leads to a replacing of parameters if they are mentioned more than once. A third option for the ``duplicate`` option for parametersets is ``error``. In this case the execution is aborted if a parameter is defined more than once.

The option ``duplicate`` can also be stated for parameters. In this case the parameters ``duplicate`` option is prioritized over the parametersets one. The possible values for parameters ``duplicate`` option are ``none``, ``replace``, ``concat`` and ``error``. ``none`` is the default value and leads to option being ignored such that the parametersets ``duplicate`` option is taking precedence. The other three options are the same as in the parameterset.
