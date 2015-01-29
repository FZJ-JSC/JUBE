.. # JUBE Benchmarking Environment
   # Copyright (C) 2008-2015
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

Version 2.0.3
~~~~~~~~~~~~~
Release: 2015-01-29

* missing files given in a fileset will now raise an error message
* ``jube info <benchmark-dir> --id <id> --step <step_name>`` now also shows
  the current parametrization
* ``jube info <benchmark-dir> --id <id> --step <step_name> -p`` only shows the
  current parametrization using a csv table format
* add new (optional) attribute ``max_async="..."`` to ``<step>``: Maximum number of parallel workpackages
  of the correspondig step will run at the same time (default: 0, means no limitation)
* switch ``<analyzer>`` to ``<analyser>`` (also ``<analyzer>`` will be available) to avoid mixing of "s" and "z" versions
* fix bug when using ``,`` inside of a ``<pattern>``
* *JUBE* now return a none zero error code if it sends an error message
* update platform files to allow easier environment handling: ``<parameter ... export="true">`` will 
  be automatically used inside of the corresponding jobscript
* update platform jobscript templates to keep error code of running program
* fix bug when adding ``;`` at the end of a ``<do>``
* last five lines of stderr message will now be copied to user error message (if shell return code <> 0)
* fix *Python2.6* compatibility bug in converter module
* fix bug when using an evaluable parameter inside of another parameter

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
