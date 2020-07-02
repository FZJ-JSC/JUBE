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

.. index:: faq

Frequently Asked Questions
==========================

.. index:: parameter groups

Parameter groups
~~~~~~~~~~~~~~~~

Within *JUBE* you can define parameter groups to allow only specific parameter
combinations.

E.g. you have two parameters:

.. code-block:: xml

   <parameter name="foo">10,100</parameter>
   <parameter name="bar">20,200</parameter>
   
Without any additional change, *JUBE* will run four paramater combinations (
``foo=10,bar=20``, ``foo=100,bar=20``, ``foo=10,bar=200``, ``foo=100,bar=200``).
But maybe within your configuration only ``foo=10,bar=20`` and ``foo=100,bar=200`` make sense.
For this you can use the parameter dependencies feature and small *Python* snippets 
(:ref:`parameter-dependencies`) to split the four combinations into two groups, by using a dummy index value:

.. code-block:: xml

   <parameter name="i">0,1</parameter>
   <parameter name="foo" mode="python">[10,100][$i]</parameter>
   <parameter name="bar" mode="python">[20,200][$i]</parameter>
   
Instead of using a numerical index, you can also use a string value for selection:

.. code-block:: xml

   <parameter name="key">tick,tock</parameter>
   <parameter name="foo" mode="python">
      {"tick" : 10,
       "tock" : 100}["${key}"]
   </parameter>
   <parameter name="bar" mode="python">
      {"tick" : 20,
       "tock" : 200}["${key}"]
   </parameter>

Also default values are possible:

.. code-block:: xml

   <parameter name="foo" mode="python">
      {"tick" : 10,
       "tock" : 100}.get("${key}",0)
   </parameter>

.. index:: workdir change

Workdir change
~~~~~~~~~~~~~~

Sometimes you want to execute a step outside of the normal *JUBE* directory structure. This can be done
by using the ``work_dir``-attribute inside the ``<step>``-tag. If you use the ``work_dir`` *JUBE* does not
create a unique directory structure. So you have to create this structure on your own if you need unique
directories e.g. by using the :term:`jube_variables`.

.. code-block:: xml

   <step name="a_step" work_dir="path_to_dir/${jube_benchmark_padid}/${jube_wp_padid}_${jube_step_name}">
      ...
   </step>

Using the ``*_padid`` variables will help to create a sorted directory structure.

*JUBE* does not create any symbolic links inside the changed work directories. If you want to access files, out of
a dependend step, you can use a ``<fileset>`` and the ``rel_path_ref``-attribute.

.. code-block:: xml

   <fileset name="needed_files">
      <link rel_path_ref="internal">dependent_step_name/a_file</link>
   </files>

This will create a link inside your alternative working dir and the link target path will be seen relative towards
the original *JUBE* directory structure. So here you can use the normal automatic created link to access all
dependend files.

To access files out of an alternative working directory in a following step and if you created this working directory by
using the :term:`jube_variables`, you can use ``jube_wp_parent_<parent_name>_id`` to get the id of the parent step to
use it within a path definition.

.. index:: XML character handling

.. _XML_character_handling:

XML character handling
~~~~~~~~~~~~~~~~~~~~~~

The *JUBE* *XML* based input format bases on the general *XML* rules. Here some hints for typical *XML* problems:

Linebreaks are not allowed inside a tag-option (e.g. ``<sub ... dest="...\n...">`` is not possible). Inside a tag
multiple lines are no problem (e.g. inside of ``<parameter>...</parameter>``). Often multiple lines are also needed
inside a ``<sub>``. Linebreaks are possible for the ``dest=""`` part, by switching to the alternative ``<sub>`` syntax:

.. code-block:: xml

   <sub source="...">
   ...
   </sub>

Whitespaces will only be removed in the beginning and in the end of the whole string. So indentation of a multiline string
can create some problems.

Some characters are not allowed inside an *XML* script or at least not inside a tag-option. Here are some of the typcial replacments:

* ``<`` : ``&lt;``
* ``>`` : ``&gt;``
* ``&`` : ``&amp;``
* ``"`` : ``&quot;``
* ``'`` : ``&apos;``

.. index:: YAML character handling

.. _YAML_character_handling:

YAML character handling
~~~~~~~~~~~~~~~~~~~~~~~

The *JUBE* *YAML* based input format bases on the general *YAML* rules.
   
Instead of tags in the *XML* format the *YAML* format uses keys which values are a list of elements or other keys.

The files used for this example can be found inside ``examples/yaml``.

The input file ``hello_world.yaml``:

.. literalinclude:: ../examples/yaml/hello_world.yaml
   :language: yaml

You can use different styles of writing key value pairs:
In the example, the ``parameter`` is declared in one line using ``{}``.
Mutliple key value pairs can be stored per element. The main content attribute is marked by using ``_``.
As an alternative you can write the key value pairs amongst multiple lines using the same indent as the preceding line, 
like the key ``do`` in the example.
If a key like ``use`` has only a value, you can write it in one line without using the special ``_`` key.

Is list of elements can be specifiec by using ``[]`` or by using ``-`` amongst multiple lines (always keeping the same indent).

*YAML* also has a number of spcial characters which can be integrated by using quotation marks:

The input file ``special_values.yaml``:

.. literalinclude:: ../examples/yaml/special_values.yaml
   :language: yaml
   
Anytime you have a symbol like ``#``, ``'``, ``,``, ``:`` or ``{}`` you have to enclose the entire value in quotation marks. 

.. index:: analyse multiple files

Analyse multiple output files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This FAQ entry is only relevant for *JUBE* versions prior version 2.2. Since version 2.2 *JUBE* automatically creates a combined
result table.

Within an ``<analyser>`` you can analyse multiple files. Each ``<analyser>`` ``<analyse>`` combination will create 
independent result entries:

.. code-block:: xml

   <analyser name="analyse">
      <use>a_patternset</use>
      <analyse step="step_A">
         <file>stdout</file>
      </analyse>
      <analyse step="step_B">
         <file>stdout</file>
      </analyse>
   </analyser>

In this example the ``<patternset>`` a_patternset will be used for both files. This is ok if there are only patterns which 
match either the step_A stdout file or the step_B stdout file.

If you want to use a file dependent patternset you can move the use to a ``<file>`` attribute instead:

.. code-block:: xml

   <analyser name="analyse">
      <analyse step="step_A">
         <file use="a_patternset_A">stdout</file>
      </analyse>
      <analyse step="step_B">
         <file use="a_patternset_B">stdout</file>
      </analyse>
   </analyser>

This avoids the generation of incorrect result entries. A ``from=...`` option is not available in this case. Instead you
can copy the patternset first to your local file by using the ``init_with`` attribute.

Due to the independet result_entries, you will end up with the following result table if you mix the extracted pattern:

.. code-block:: none

   pattern1_of_A | pattern2_of_A | pattern1_of_B
   --------------+---------------+--------------
               1 |             A |
               2 |             B |
                 |               |           10
                 |               |           11
                 |               |           12
                 |               |           13

The different ``<analyse>`` were not combined. So you end up with independet result lines for each workpackage. *JUBE*
does not see possible step dependencies in this point the user has to set the dependcies manually:

.. code-block:: xml

   <analyser name="analyse">
      <analyse step="step_B">
         <file use="a_patternset_B">stdout</file>
         <file use="a_patternset_A">step_A/stdout</file>
      </analyse>
   </analyser>

Now we only have one ``<analyse>`` and we are using the autogenerated link to access the dependent step. This will create the
correct result:

.. code-block:: none

   pattern1_of_A | pattern2_of_A | pattern1_of_B
   --------------+---------------+--------------
              1  |             A |           10
              2  |             B |           11
              1  |             A |           12
              2  |             B |           13

.. index:: extract specifc block

.. _extract_specifc_block:

Extract data from a specifc text block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In many cases the standard program output is structured into multiple blocks:

.. code-block:: none

   blockA:
   ...
   time=20

   blockB:
   ...
   time=30

Using a simple ``<pattern>`` like ``time=$jube_pat_int`` will match all ``time=`` lines (the default match will be the first one,
and :ref:`statistic_values` are available as well). However in many cases a specifc value from a sepcifc block should be extracted.
This is possible by using ``\s`` within the pattern for each individual newline character within the block, or by using the ``dotall`` option:

.. code-block:: xml

   <pattern name="a_pattern" dotall="true">blockB:.*?time=$jube_pat_int</pattern>

This only extracts ``30`` from ``blockB``. Setting ``dotall="true"`` allows to use the ``.`` to take care of all newline characters in between (by default newline characters are 
not matched by ``.``).

.. index:: restart workpackage

.. _restart_workpackage:

Restart a workpackage execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a problem occurs outside of the general *JUBE* handling (e.g. a crashed HPC job or a broken dependency) it might be necessary to restart a specific workpackage.
*JUBE* allows this restart by removing the problematic workpackage entry and using the ``jube continue`` command afterwards:

.. code-block:: none

   jube remove bechmark_directory --id <id> --workpackage <workpackage_id>
   ...
   jube continue bechmark_directory

This will rerun the specific workpackage. The *JUBE* configuration will stay unchanged. It is not possible to change the ``<paramter>`` or ``<step>`` configuration later on. Shared ``<do>``
operations (``shared=true``) will be ignored within such a rerun scenario except if all workpackages of a specifc step were removed and the full step is re-executed.
