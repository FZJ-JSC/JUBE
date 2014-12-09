.. # JUBE Benchmarking Environment
   # Copyright (C) 2008-2014
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

.. index:: release notes

Release notes
=============

Version 2.0.2
~~~~~~~~~~~~~
Release: 2014-12-09

* fix a bug when using ``init-with`` to initialize a ``<copy>``-tag
* use ``cp -p`` behaviour to copy files
* fix error message when using an empty ``<do>``
* added error return code, if there was an error message

Version 2.0.1
~~~~~~~~~~~~~
Release: 2014-11-25

* ``--debug`` option should work now
* fixes problem when including an external ``<prepare>``
* update *Python 2.6* compatibility
* all ``<do>`` within a single ``<step>`` now shares the same environment (including all exported variables)
* a ``<step>`` can export its environment to a dependent ``<step>`` by using the new ``export="true"`` attribute (see new environment handling example)
* update analyse behaviour when scanning multiple files (new ``analyse`` run needed for existing benchmarks)
* in and out substitution files (given by ``<iofile>``) can now be the same
* ``<sub>`` now also supports multiline expressions inside the tag instead of the ``dest``-attribute: ``<sub source="..."></sub>``

Version 2.0.0
~~~~~~~~~~~~~
Release: 2014-11-14

* complete new **Python** kernel
* new input file format
* please see new documentation to get further information

Older JUBE Version
~~~~~~~~~~~~~~~~~~

* please see our website `www.fz-juelich.de/jsc/jube <http://www.fz-juelich.de/jsc/jube>`_ to get further information concerning *JUBE* 1.
