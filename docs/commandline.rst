.. index:: commandline
   
Command line documentation
==========================

.. highlight:: bash
   :linenothreshold: 5

Here you will find a list of all available *JUBE* command line options. You can also use::

   jube -h
   
to get a list of all available commands. 

Because of the *shell* parsing mechanism take care if you write your optional arguments after the command name before the positional
arguments. You **must** use ``--`` to split the ending of an optional (if the optional argument takes multiple input elements) and the start of the positional argument.

.. index:: run

run
~~~

Run a new benchmark.

.. code-block:: none

   jube run [-h] [--only-bench ONLY_BENCH [ONLY_BENCH ...]] 
            [--not-bench NOT_BENCH [NOT_BENCH ...]] [-t TAG [TAG ...]] 
            [--hide-animation] [--include-path INCLUDE_PATH [INCLUDE_PATH ...]]
            [-a] [-r] [-m COMMENT] FILE [FILE ...]

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
    
``-m COMMENT``, ``--comment COMMENT`` 
   overwrite benchmark specific comment
    
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

   jube continue [-h] [-i ID [ID ...]] [--hide-animation] [-a] [-r] [DIRECTORY]

``-h``, ``--help``
   show command help information
    
``-i ID [ID ...]``, ``--id ID [ID ...]`` 
   select benchmark id, default: last found inside the benchmarks directory
    
``--hide-animation`` 
   hide the progress bar animation (if you want to use *JUBE* inside a scripting environment)
    
``-a``, ``--analyse``
   run analyse after finishing run command
    
``-r``, ``--result`` 
   run result after finishing run command (this will also start analyse)
        
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
   select benchmark id, default: last found inside the benchmarks directory
    
``-u UPDATE_FILE``, ``--update UPDATE_FILE``
   use given input *XML* file to update ``patternsets``, ``analyzer`` and ``result`` before running the analyse 

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

   jube result [-h] [-i ID [ID ...]] [-a] [-u UPDATE_FILE] 
               [--include-path INCLUDE_PATH [INCLUDE_PATH ...]]
               [-t TAG [TAG ...]] [-o RESULT_NAME [RESULT_NAME ...]] [DIRECTORY]



``-h``, ``--help``
   show command help information
    
``-i ID [ID ...]``, ``--id ID [ID ...]`` 
   select benchmark id, default: last found inside the benchmarks directory
    
``-a``, ``--analyse``
   run analyse before running result command
    
``-u UPDATE_FILE``, ``--update UPDATE_FILE``
   use given input *XML* file to update ``patternsets``, ``analyzer`` and ``result`` before running the analyse 

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
   select benchmark id, default: last found inside the benchmarks directory
    
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
   select benchmark id, default: last found inside the benchmarks directory
    
``-f``, ``--force``
   do not prompt
            
``DIRECTORY``
   directory which contain benchmarks, default: ``.``

.. index:: info

info
~~~~

Get benchmark specific information

.. code-block:: none

   jube info [-h] [-i ID [ID ...]] [-s STEP [STEP ...]] [DIRECTORY]
   
``-h``, ``--help``
   show command help information
    
``-i ID [ID ...]``, ``--id ID [ID ...]`` 
   show benchmark specific information
    
``-s STEP [STEP ...]``, ``--step STEP [STEP ...]``
   show step specific information
            
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
   select benchmark id, default: last found inside the benchmarks directory
    
``-c COMMAND [COMMAND ...]``, ``--command COMMAND [COMMAND ...]``
   show only logs for specified commands
            
``DIRECTORY``
   directory which contain benchmarks, default: .

..index:: status

status
~~~~~~

Show benchmark status RUNNING or FINISHED.

.. code-block:: none

   jube status [-h] [-i ID [ID ...]] [DIRECTORY]
   
``-h``, ``--help``
   show command help information
   
``-i ID [ID ...]``, ``--id ID [ID ...]`` 
   select benchmark id, default: last found inside the benchmarks directory
            
``DIRECTORY``
   directory which contain benchmarks, default: .

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
       
