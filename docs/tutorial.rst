.. index:: tutorial
   
JUBE tutorial
=============

.. highlight:: bash
   :linenothreshold: 5

This tutorial is meant to give you an overview about the basic usage of *JUBE*.

.. index:: installation

Installation
~~~~~~~~~~~~

Requirements: *JUBE* needs **Python 2.7** or **Python 3.2** (or higher)
    
To use the *JUBE* commandline tool the ``PHYTONPATH`` must contain the position of the *JUBE* package

* You can use the **installation tool** to copy all files to the right position (preferred)::

   >>> python setup.py install --user
   
  This will install the *JUBE* package and the binary to your ``$HOME/.local`` directory.   

* You can also add **parent folder path** of the *JUBE* package-folder to the ``PHYTONPATH`` environment variable::
  
   >>> export PHYTONPATH=<parent folder path>:$PHYTONPATH 

* You can move the *JUBE* package by hand to an existing Python package folder like ``site-packages``

To use the *JUBE* commandline tool like a normal commandline command you can add it to the ``PATH`` environment variable::

   >>> export PATH=$HOME/.local/bin:$PATH
   
   
.. index:: hello world
   
Hello World
~~~~~~~~~~~

In this example we will show you the basic structure of a *JUBE* input file and the
basic commandline options. 

The files used for this example can be found inside ``examples/hello_world``.

The input file ``hello_world.xml``:

.. literalinclude:: ../examples/hello_world/hello_world.xml
   :language: xml
   
Every *JUBE* input file starts (after the general *XML* header line) with the root tag ``<jube>``.
This root tag must be unique. *XML* does not allow multiple root tags.

The first tag which contains benchmark specific information is ``<benchmark>``. ``hello_world`` is
the benchmarkname which can be used to identify the benchmark (e.g. when there are multiple
benchmarks inside a single input file, or when different benchmarks using the same run directory).

The ``outpath`` describes the benchmark run directory (relative to the position of the input file).
This directory will be managed by *JUBE* and will be automatically created if it doesn't exist.
The directory name and position are very important, because they are the main interface to communicate 
with your benchmark, after it was submitted.

Using the ``<comment>`` you can store some benchmark related comment inside the benchmark directory.
You can also use normal *XML*-comments to structure your input-file:

.. code-block:: xml

   <!-- your comment -->

In this benchmark a ``<parameterset>`` is used to store the single ``<parameter name="hello_str">`` parameter. 
The ``name`` of the parameterset must be unique (relative to the current benchmark). In further examples we 
will see that there are more types of sets, which can be distinguished by their names. Also the ``name`` of the
parameter must be unique (relative to the parameterset).

The ``<step>`` contains the operation tasks. The ``name`` must be unique. It can use different types of existing sets.
Only sets, which are explicitly used, are available inside the step! The ``<do>`` contains a single **shell command**.
This command will run inside of a sandbox directory environment (inside the ``outpath`` directory tree).
The step and its corresponding parameterspace is named :term:`workpackage`.

**Available** parameters can be used inside the shell commands. To use a parameter you had to write ::
   
   $parametername
   
or ::

   ${parametername}
   
The brackets must be used if you want some variable concatenation. ``$hello_strtest`` will not be replaced,
``${hello_str}test`` will be replaced. If a parameter doesn't exist or isn't available the variable will not
be replaced! If you want to use ``$`` inside your command, you had to write ``$$`` to mask the symbol. Parameter
substitution will run before the normal shell substitution!

To run the benchmark just type::

   >>> jube run hello_world.xml

This benchmark will produce the follwing output:

.. code-block:: none

   ######################################################################
   # benchmark: hello_world

   A simple hello world
   ######################################################################

   Running workpackages (#=done, 0=wait):
   ############################################################ (  1/  1)
   
      stepname | all | open | wait | done
     ----------+-----+------+------+-----
     say_hello |   1 |    0 |    0 |    1

   >>>> Benchmark information and further useful commands:
   >>>>       id: 0
   >>>>      dir: bench_run
   >>>>  analyse: jube analyse bench_run --id 0
   >>>>   result: jube result bench_run --id 0
   >>>>     info: jube info bench_run --id 0
   ######################################################################
   
You see, that inside the benchmark execution there was a single step ``say_hello``
which run one shell command ``echo $hello_str`` which will be expanded to ``echo Hello World``.

The **id** is (in addition to the benchmark directory) an important number. Every benchmark run will
get a new unique **id** inside the benchmark directory.

Inside the benchmark directory you will see the follwing structure:

.. code-block:: none
   
   bench_run               # the given outpath
   |
   +- 000000               # the benchmark id
      |
      +- configuration.xml # the stored benchmark configuration
      +- workpackages.xml  # workpackage information 
      +- 000000_say_hello  # the workpackage
         |
         +- done           # workpackage finished marker
         +- work           # user sanbox folder
            |
            +- stderr      # standard error messages of used shell commands
            +- stdout      # standard output of used shell commands
            
``stdout`` will contain ``Hello World`` in this example case.

.. index:: help

Help
~~~~

*JUBE* contains a commandline based help functionality::

   >>> jube help <keyword>
   
With this command you will have direct access to all keywords inside the :doc:`glossary <glossar>`.

Another useful command is the ``info`` command. It will show you information concerning your existing benchmarks::
   
   # display a list of existing benchmarks
   >>> jube info <benchmark-directory>
   # display information about given benchmark
   >>> jube info <benchmark-directory> -- id <id>
   # display information about a step inside the given benchmark
   >>> jube info <benchmark-directory> -- id <id> --step <stepname>
   
The third, but very important, functionality is the **logger**. Every ``run``, ``continue``, ``analyse``
and ``result`` execution will produce a new log file inside your execution directory.
This file contains much useful debugging output.

You can also use the debugging mode::

   >>> jube --debug <command> [other-args]
   
This mode avoid any *shell* execution but will generate log files.

.. index:: parameterspace creation

Parameterspace creation
~~~~~~~~~~~~~~~~~~~~~~~

In this example we will show you an important feature of *JUBE*: The automatic parameterspace generation.

The files used for this example can be found inside ``examples/parameterspace``.

The input file ``parameterspace.xml``:

.. literalinclude:: ../examples/parameterspace/parameterspace.xml
   :language: xml
   
Whenever a parameter contains a ``,`` (this can be changed using the ``separator`` attribute) this parameter becomes 
a **template**. A step which **uses the parameterset** containing this parameter will run multiple times to iterate over 
possible parameter combinations. In this example the step ``say_hello`` will run 6 times:

.. code-block:: none

    stepname | all | open | wait | done
   ----------+-----+------+------+-----
   say_hello |   6 |    0 |    0 |    6


Every parameter combination will run in its own sandbox directory.

Another new keyword is the ``type`` attribute. The parameter type isn't used inside the substitution process, but
it is used for sorting operation inside the ``result`` creation. The default type is ``string``. 
Possible basic types are ``string``, ``int`` and ``float``.

.. index::  step dependencies, dependencies

Step dependencies
~~~~~~~~~~~~~~~~~

If you start writing a complex benchmark structure, you want to have dependencies between different :term:`steps <step_tag>`. For
example between a compile and the execution step. *JUBE* can handle these dependencies and will also preserve the given 
parameterspace.

The files used for this example can be found inside ``examples/dependencies``.

The input file ``dependencies.xml``:

.. literalinclude:: ../examples/dependencies/dependencies.xml
   :language: xml
   
In this example we create a dependency between ``first_step`` and ``second_step``. After ``first_step`` finished, the 
corresponding ``second_step`` will start. You are able to have multiple dependencies (separated by ``,`` in the definition), but
circular definitions will not be resolved. A dependency is a unidirectional link! 

To communicate between a step and its dependency there is a link inside the work directory pointing to the corresponding
dependency step work directory. In this example we use ::
   
   cat first_step/stdout
   
to write the ``stdout``-file content of the dependency step into the ``stdout``-file of the current step.

Because the ``first_step`` uses a template parameter which creates three execution runs. There will also be
three ``second_step`` runs each pointing to a different ``first_step``-directory:

.. code-block:: none

      stepname | all | open | wait | done
   ------------+-----+------+------+-----
    first_step |   3 |    0 |    0 |    3
   second_step |   3 |    0 |    0 |    3
   
.. index:: substitution, loading files, external files, files
   
Loading files and substitution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every step runs inside a unique sandbox directory. In normal cases you need external files inside this directory (e.g. the source files)
and in some cases you want to change a parameter inside the file based on your current parameterspace. there are two addition set-types
which handle this behaviour inside of *JUBE*.

The files used for this example can be found inside ``examples/files_and_sub``.

The input file ``files_and_sub.xml``:

.. literalinclude:: ../examples/files_and_sub/files_and_sub.xml
   :language: xml
   
The content of file ``file.in``:

.. literalinclude:: ../examples/files_and_sub/file.in
   :language: none
  
Inside the ``<fileset>`` the current location (relativly seen towards the current input file) of files is given. ``<copy>`` specify that the
file should be copied to the sandbox directory when the fileset is used. Also a ``<link>`` option is available to create a symbolic link to the given file
inside the sandbox directory.

The ``<substituteset>`` describe the substitution process. The ``<iofile>`` contains the input and output file. The path is relativly seen
towards the sandbox directory. Because we do/should not know that location we used the fileset to copy ``file.in`` inside the directory.

The ``<sub>`` specify the substitution. All occurrence of ``source`` will be substituted by ``dest``. As you can see, you can 
use Parameter inside the substitution to use your current parametersapce. 

In the ``sub_step`` we use all available sets. The use order isn't relevant. The normal execution process will be:

#. Parameterspace expansion
#. Copy/link files
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
      +- 000000_say_hello  # the workpackage ($number = 1)
         |
         +- done           # workpackage finished marker
         +- work           # user sanbox folder
            |
            +- stderr      # standard error messages of used shell commands
            +- stdout      # standard output of used shell commands (Number: 1)
            +- file.in     # the file copy 
            +- file.out    # the substituted file
      +- 000001_say_hello  # the workpackage ($number = 2)
         |
         +- ...
      +- ...

.. index:: analyse, result, table

Creating a result table
~~~~~~~~~~~~~~~~~~~~~~~

Finally, after running the benchmark, you will get several directories. *JUBE* allows you to parse your result files to extract
relevant data (e.g. walltime information) and create a result table.

The files used for this example can be found inside ``examples/result_creation``.

The input file ``result_creation.xml``:

.. literalinclude:: ../examples/result_creation/result_creation.xml
   :language: xml
   
Using ``<parameterset>`` and ``<step>`` we create three :term:`workpackages <workpackage>`. Each writing ``Number: $number`` to ``stdout``.

Now we want to parse these stdout files to extract information (in this example case the written number). First of all we had to declare a
``<patternset>``. Here we can describe a set of ``<pattern>``. A ``<pattern>`` is a regular expression which will be used to parse your result files
and search for a given string. In this example we only have the ``<pattern>`` ``number_pat``. The name of the pattern must be unique (based on the usage of the ``<patternset>``).
The ``type`` is optional. It is used when the extracted data will be sorted. The regular expression can contain other pattern or parameter. The example uses ``$jube_pat_int`` which
is a *JUBE* given default pattern matching integer values. The pattern must contain a group, given by brackets ``(...)``, to declare the extraction part 
(``$jube_pat_int`` already contains these brackets).

To use your ``<patternset>`` you had to specify the files which should be parsed. This can be done using the ``<analyzer>``.
It uses relevant patternsets, and inside the ``<analyse>`` a step-name and a file inside this step is given. Every workpackage file combination
will create its own result entry.

To run the anlayse you had to write::

   >>> jube analyse bench_run
   
The analyse data will be stored inside the benchmark directory.

The last part is the result table creation. Here you had to used an existing analyzer. The ``<column>`` contains a pattern or a parameter name. ``sort`` is
the optioanl sorting order (separated by ``,``). The ``style`` attribute can be ``csv`` or ``pretty`` to get different ASCII representations.

To create the result table you had to write::

   >>> jube result bench_run
   
The result table will be written to ``STDOUT`` and into a ``result.dat`` file inside ``bench_run/<id>/result``.

Output of the given example:

.. code-block:: none

   number | number_pat                                                                                                                                                           
   -------+-----------                                                                                                                                                           
        1 |          1                                                                                                                                                           
        2 |          2                                                                                                                                                           
        4 |          4
        
This was the last example of the basic *JUBE* tutorial. Next you can start the :doc:`advanced tutorial <advanced>` to get more information about
including external sets, jobsystem representation and scripting parameter.
        
