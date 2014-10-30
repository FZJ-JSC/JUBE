.. index:: advanced tutorial
   
Advanced tutorial
=================

.. highlight:: bash
   :linenothreshold: 5
   
This tutorial will show you more detailed functions and tools of *JUBE*. If you want a basic overview you should
read the general :doc:`tutorial` first.

.. index:: schema validation, validation, dtd

Schema validation
~~~~~~~~~~~~~~~~~
To validate your input files you can use DTD or schema validation. You will find ``jube.dtd`` and
``jube.xsd`` inside the ``schema`` folder. You had to add these schema information to your input files
which you want to validate.

DTD usage:

.. code-block:: xml
   :linenos:

   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE benchmarks SYSTEM "<jube.dtd path>">
   <benchmark>
   ...

Schema usage:

.. code-block:: xml
   :linenos:

    <?xml version="1.0" encoding="UTF-8"?>
    <benchmarks xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="<jube.xsd path>">
    ...
 
Example validation tools:

* eclipse
* xmllint:
  
  * For validation (using the DTD)::
  
       >>> xmllint --noout --valid <xml input file>
       
  * For validation (using the DTD and Schema)::
  
       >>> xmllint --noout --valid --schema <schema file> <xml input file>

.. index:: scripting, perl, python

Scripting parameter
~~~~~~~~~~~~~~~~~~~
Sometimes you want to create a parameter which based on the value of another paramter. In this case you can use scripting parameter.

The files used for this example can be found inside ``examples/scripting_parameter``.

The input file ``scripting_parameter.xml``:

.. literalinclude:: ../examples/scripting_parameter/scripting_parameter.xml
   :language: xml
   
In this example we see four different parameter.

* ``number`` is a normal template which will be expanded to three different :term:`workpackages <workpackage>`.
* ``additional_number`` is a scripting parameter which creates a new template and bases on ``number``. The ``mode`` is set to the scripting language (``python`` and ``perl`` are allowed).
  The additional ``type`` is optional and declare the result type after evaluating the expression. The type is only used by the sort algorithm in the result step. It is not possible to
  create a template of different scripting parameter. Because of this second template we will get six different :term:`workpackages <workpackage>`.
* ``number_mult`` is a small calculation. You can use any other existing parameter (which is used inside the same step).
* ``text`` a normal parameter which uses the content of another parameter. For simple concatenation parameter you do not need scripting
  parameter.
  
For this example we will find the following output inside the ``jube.log``-file:

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

Scripting inside the ``<do>`` or any other position is not possible. If you want to use some scripting expressions you had to create a new parameter.

.. index:: jobsystem

Jobsystem
~~~~~~~~~
In most cases you want to submit jobs by *JUBE* to your local machines jobsystem. You can use the normal file access and substitution system to prepare 
your jobfile and send it to the jobsystem. *JUBE* also provide some additional features.

The files used for this example can be found inside ``examples/jobsystem``.

The input jobsystem file ``job.run.in`` for *Torque/Moab* (you can easily adapt your personal jobscript):

.. literalinclude:: ../examples/jobsystem/job.run.in
   :language: bash
   
The *JUBE* input file ``jobsystem.xml``:

.. literalinclude:: ../examples/jobsystem/jobsystem.xml
   :language: xml
   
As you can see the jobfile is very general and several parameter will be used for replacement. By using a general jobfile and the substitution mechanism 
you can control your jobsystem directly out of your *JUBE* input file.

The submit command is a normal *Shell* command so there are no special *JUBE* tags to submit a job.

There are two new attributes:
  
  * ``done_file`` inside the ``<do>`` allows you set a filename/path to a file which should be used by the jobfile to mark the end of execution. *JUBE* doesn't know when the job ends.
    Normally it will return when the *Shell* command was finished. When using a jobsystem we had to wait until the jobfile was executed. If *JUBE* found a
    ``<do>`` containing a ``done_file`` attribute *JUBE* will return directly and will not continue automatically until the ``done_file`` exists. If you want to check the current status
    of your running steps and continue the benchmark process if possible you can type::
     
       >>> jube continue benchmark_run
    
    This will continue your benchmark execution. the position of the ``done_file`` is relativly seen to the work directory.
  * ``work_dir`` can be used to change the sandbox work directory of a step. In normal cases *JUBE* checks that every work directory get a unique name. When changing the directory the user must select a
    unique name by his own. For example he can use ``$jube_benchmark_id`` and ``$jube_wp_id`` which are *JUBE* internal parameter and will expand to the current benchmark and workpackage id. Files and directories out of a given
    ``<fileset>`` will be copied to the new work directory. Other automatic links, like the dependency links, will not be created!

You will see this Output after running the benchmark:

.. code-block:: none

   stepname | all | open | wait | done
   ---------+-----+------+------+-----
     submit |   3 |    0 |    3 |    0
   
and this output after running the ``continue`` command (after the jobs where executed):
  
.. code-block:: none
   
   stepname | all | open | wait | done
   ---------+-----+------+------+-----
     submit |   3 |    0 |    0 |    3

Every workpackage continue, but because there are no more additional operations there is no more work to be done.

You had to run ``continue`` multiple times if not all ``done_file`` were written when running ``continue`` for the first time.

.. index:: include

Include external data
~~~~~~~~~~~~~~~~~~~~~

As you seen in the example before a benchmark can become very long. To structure your benchmark youe can use multiple files and reuse existing
sets. There are three different include features inside of *JUBE*.

The files used for this example can be found inside ``examples/include``.

The include file ``include_data.xml``:

.. literalinclude:: ../examples/include/include_data.xml
   :language: xml

All files which contains data that should be included must use the *XML*-format. The include files can have a user specific structure (there can be none valid
*JUBE* tags like ``<dos>``), but the structure must be allowed by the searching mechanism (see below). The resulting file must have a valid *JUBE* structure.

The main file ``main.xml``:

.. literalinclude:: ../examples/include/main.xml
   :language: xml
   
In these file there are three different inlcude types.

The ``init_with`` can be used inside any set definition. Inside the given file the searching mechanism will search for the same set (same type, same name), will parse its structure (this must be *JUBE* valid) and copy the content to
``main.xml``. Inside ``main.xml`` you can add additional values or can overwrite existing ones. If your include-set use a different name inside your include file you can use ``init_with="filename.xml:new_name"``.

The second method is the ``<use from="...">``. This is mostly the same like the ``init_with`` structure but in this case you are not able to add or overwrite some values. The external set will be used directly. There is no set-type inside the ``<use>``, because of that, the setname must
be unique inside the include-file.

The last method is the most generic include. By using ``<include />`` you can copy any nodes you want to your main-*XML* file. The ``path`` is optional and can be used to select a specific nodeset (otherwise the root-node will be included). The ``<include />`` is the only
include-method that can be used to include any tag you want. The ``<include />`` will copy all parts without any changes. The other include types will update pathnames, which were relative to the include-file position.

To run the benchmark you can use the normal command::

   >>> jube run main.xml
   
It will search for include files inside four different positions (in the following order):

* inside the same directory of your ``main.xml``
* inside a directory given over the commandline::
   
     >>> jube run --include-path some_path another_path -- main.xml
   
* inside any path given with the ``JUBE_INCLUDE_PATH`` environment variable::

     >>> export JUBE_INCLUDE_PATH=some_path:another_path

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

The ``tag`` attribute or the commandline expression can also contain a list of different names. A hidden ``<tag>`` will
be ignored completely! If there is no alternative this can produce a wrong execution behaviour!

The ``tag`` attribute can be used inside every ``<tag>`` inside the input file (except the ``<jube>``).

.. index:: platform independent

Platform independent benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to create platform independent benchmarks you can use the include features inside *JUBE*.

All platform related sets must be declared in a includeable file e.g. ``platform.xml``. There can be multiple ``platform.xml`` in different
directories to allow different platforms. By changing the ``include-path`` the benchmark changes its platform specific data.

An example benchmark structure bases on three include files:

* The main benchmark include file which contain all benchmark specific but platform independent data
* A mostly generic platform include file which contain benchmark independent but platform specific data (this can be created once and placed somewhere
  central on the system, it can be easily accessed using the ``JUBE_INCLUDE_PATH`` environment variable.
* A platform specific and benchmark specific include file which must be placed in a unique directory to allow inlcude-path usage
  
To avoid writting of long include-pathes every time you run a platform independent benchmark you can store the include-path inside your 
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
   