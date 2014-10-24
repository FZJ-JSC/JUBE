.. index:: advanced tutorial
   
Advanced tutorial
=================

.. highlight:: bash
   :linenothreshold: 5
   
This tutorial will show more detailed functions and tools of *JUBE*. If you want a basic overview you should
read the general :doc:`tutorial` first.

.. index:: schema validation, validation

Schema validation
~~~~~~~~~~~~~~~~~
To validate your input files you can use DTD or schema validation. You will find ``jube.dtd`` and
``jube.xsd`` inside the ``schema`` folder. You had to add these schema information to your input files
which you want to be validated.

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
Sometimes you want to create parameter based on other parameter. In this cases you can use scripting parameter.

The files used for this example can be found inside ``examples/scripting_parameter``.

The input file ``scripting_parameter.xml``:

.. literalinclude:: ../examples/scripting_parameter/scripting_parameter.xml
   :language: xml
   
In this example we see four different parameter.

* ``number`` is a normal template which expands to three different :term:`workpackages <workpackage>`.
* ``additional_number`` is a scripting parameter which creates a new template and bases on ``number``. The ``mode`` is set to the scripting language (``python`` and ``perl`` are allowed).
  The additional ``type`` is optional and declare the result type after evaluating the expression. The ``int`` type is only used by the sort algorithm in the result step. It is not possible to
  create a template of different scripting parameter. Because of this second template we will get six different :term:`workpackages <workpackage>`.
* ``number_mult`` is a small calculation. You can use any other existing parameter (which is used inside the same step).
* ``text`` a normal parameter which uses the content of another parameter. For simple concatenation parameter you need no scripting
  parameter.
  
For this example we get the following output:

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

The submit command is a normal *Shell* command so there are no special tags needed.

There are two new attributes:
  
  * ``done_file`` inside the ``<do>`` allows you set a filename/path which should be used by the jobfile to mark the end of execution. *JUBE* doesn't when the job ends.
    normally it will return when the *Shell* command was finished. When using a jobsystem we had to wait until the jobfile was executed. If *JUBE* found a
    ``<do>`` containing a ``done_file`` attribute *JUBE* will return directly and will not continue automatically until the ``done_file`` exists. If you want to check the current status
    of your running steps and continue the benchmark process if possible you can type::
     
       >>> jube continue benchmark_run
    
    This will continue your benchmark execution.
  * ``work_dir`` can be used to change the sandbox work directory of a step. In normal cases *JUBE* checks that every work directory get a unique name. When changing the directory the user must select a
    unique name by his own. For example he can use ``$jube_benchmark_id`` and ``$jube_wp_id`` which are *JUBE* internal parameter and will expand to the current benchmark and workpackage id. Files and directories out of a given
    ``<fileset>`` will be copied to the new work directory. Other automatic links, like the dependency links, will not be created!

You will see this Output after running the benchmark:

.. code-block:: none

   ====== submit ======
   >>> msub job.run
   Waiting for file "ready" ...
   ====== submit ======
   >>> msub job.run
   Waiting for file "ready" ...
   ====== submit ======
   >>> msub job.run
   Waiting for file "ready" ...
   
and this output after running the ``continue`` command:
  
.. code-block:: none
   
   ====== submit ======
   ====== submit ======
   ====== submit ======

Every workpackage continue, but because there are no more additional operations there is no more work to be done.

You had to run ``continue`` multiple times if not all ``done_file`` were written when running ``continue`` for the first time.

.. index:: include

Include
~~~~~~~

As you seen in the example before a benchmark can be become very long. To structure your benchmark using multiple files and to reuse existing
sets there are three different include features inside of *JUBE*.

The files used for this example can be found inside ``examples/include``.

The include file ``include_data.xml``:

.. literalinclude:: ../examples/include/include_data.xml
   :language: xml

All files which contains data to be included use the *XML*-format.
   