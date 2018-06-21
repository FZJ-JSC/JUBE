.. # JUBE Benchmarking Environment
   # Copyright (C) 2008-2018
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

.. index:: introduction

Introduction
============

Automating benchmarks is important for reproducibility and hence
comparability which is the major intent when performing
benchmarks. Furthermore managing different combinations of parameters
is error-prone and often results in significant amounts work
especially if the parameter space gets large.

In order to alleviate these problems *JUBE* helps performing and
analyzing benchmarks in a systematic way. It allows custom work flows
to be able to adapt to new architectures.

For each benchmark application the benchmark data is written out in a certain
format that enables *JUBE* to deduct the desired information.
This data can be parsed by automatic pre- and post-processing scripts that draw
information, and store it more densely for manual interpretation.

The *JUBE* benchmarking environment provides a script based framework to easily
create benchmark sets, run those sets on different computer systems and evaluate
the results. It is actively developed by 
the Jülich Supercomputing Centre of Forschungszentrum Jülich, Germany.
