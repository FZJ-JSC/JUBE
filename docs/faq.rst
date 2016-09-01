.. # JUBE Benchmarking Environment
   # Copyright (C) 2008-2016
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

E.g. you have are two parameters:

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
   
Instead of using a numerical index, you can also use a string value for selction:

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

*JUBE* does not create any symbolic links inside the changed work dirctories. If you want to access files, out of
a dependend step, you can use a ``<fileset>`` and the ``rel_path_ref``-attribute.

.. code-block:: xml

   <fileset name="needed_files">
      <link rel_path_ref="internal">dependent_step_name/a_file</link>
   </files>

This will create a link inside your alternative working dir and the link target path will be seen relative towards
the original *JUBE* directory structure. So here you can use the normal automatic created link to access all
dependend files.

To access files out of a alternative working directory in a following step and if you created this working directory by
using the :term:`jube_variables`, you can use ``jube_wp_parent_<parent_name>_id`` to get the id of the parent step to
use it within a path definition.

.. index:: XML character handling

XML character handling
~~~~~~~~~~~~~~~~~~~~~~

The *JUBE* input format bases on the general *XML* rules. Here some hints for typical *XML* problems:

Linebreaks are not allowed inside a tag-option (e.g. ``<sub ... dest="...\n...">`` is not possible). Inside a tag
multiple lines are now problem (e.g. inside of ``<parameter>...</parameter>``). Often multiple lines are also needed
inside a ``<sub>``. Linebreaks are possible for the ``dest=""`` part, by switching to the alternative ``<sub>`` syntax:

.. code-block:: xml

   <sub source="...">
   ...
   </sub>

Whitespaces will only be removed in the beginning and in the end of the whole string. So indentation of a multiline string
can create some problems.

Some characters are not allowed inside a *XML* script or at least not inside a tag-option. Here some of the typcial replacments:

* ``<`` : ``&lt;``
* ``>`` : ``&gt;``
* ``&`` : ``&amp;``
* ``"`` : ``&quot;``
* ``'`` : ``&apos;``



