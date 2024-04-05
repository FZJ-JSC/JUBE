<div align="center">
<img src="docs/logo/JUBE-Logo.svg" alt="JUBE" height="170em"/>
</div>

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7534372.svg)](https://doi.org/10.5281/zenodo.7534372)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# What is JUBE?

The JUBE benchmarking environment provides a script-based framework for easily
creating benchmark and workflow sets, running those sets on different computer
systems, and evaluating the results.
It is actively developed by the [Juelich Supercomputing Centre](https://www.fz-juelich.de/en/ias/jsc).
It focuses on managing the complexity of combinatorial benchmarks and ensuring reproducibility of the benchmarks.
JUBE provides support for different workflows and the ability to use vendor-supplied platform configurations.
The benchmark configuration and scripts can be specified in either YAML or XML format.
JUBE is primarily designed for use on supercomputers with *scheduding* systems
like Slurm or PBS, but also works on laptops running Linux or MacOS operating systems.

## Documentation

JUBE is not (yet) available on `pypi` (it is work in progress).
The source code can be downloaded from any of the following places:
- [GitHub](https://github.com/FZJ-JSC/JUBE)
- [JSC JUBE Webpage](https://www.fz-juelich.de/en/ias/jsc/services/user-support/software-tools/jube/download)

JUBE can be installed using `pip` or `setup.py` and needs *python 3.2* or higher.
You will also need *SQLite* version 3.35.0 (or higher) to use the database as a result output.
Installation instructions can be found [here](https://apps.fz-juelich.de/jsc/jube/jube/docu/tutorial.html#installation).

The documentation for JUBE is split into Beginner Tutorial, Advanced Tutorial, 
FAQ, CLI, and Glossary and can be found in the 
**[User Guide](https://apps.fz-juelich.de/jsc/jube/jube/docu/index.html)**.

In addition to the documentation, there are also 
[tutorial examples](examples)
which are described in the tutorials of the user guide and 
[benchmark examples](https://github.com/FZJ-JSC/jube-configs), which are curated
examples of JUBE benchmarks (the latter will be either replaced or 
updated/extended soon).

For more information on the design and architecture of JUBE, please refer to
this [paper](https://ebooks.iospress.nl/DOI/10.3233/978-1-61499-621-7-431).


## Community and Contributing

JUBE is an open-source project and we welcome your questions, discussions and contributions.
Questions can be asked directly to the JSC JUBE developers via mail to
[jube.jsc@fz-juelich.de](mailto:jube.jsc@fz-juelich.de) and issues can be
reported in the issue tracker.
We also welcome contributions in the form of pull requests.
Contributions can include anything from bug fixes and documentation to new features.

JUBE development is currently still taking place on an internal GitLab instance.
However, we are in a transition phase to move development to GitHub. The complete
move will take some time. In the meantime, we will decide individually how to
proceed with Pull Requests opened on GitHub. Before you start implementing new
features, we would recommended to contact us, as we still have several open
branches in GitLab.

- **[GitHub Issue Tracker](https://github.com/FZJ-JSC/JUBE/issues)**
- **[Github Discussions](https://github.com/FZJ-JSC/JUBE/discussions)**
- **[GitHub Pull Requests](https://github.com/FZJ-JSC/JUBE/pulls)**

Please ensure that your contributions to JUBE are compliant with the 
[contribution](CONTRIBUTING.md), 
[developer](https://apps.fz-juelich.de/jsc/jube/jube/docu/devel.html) and 
[community](CODE_OF_CONDUCT.md) guidelines.

# Citing JUBE

If you use JUBE in your work, please cite the
[software release](https://zenodo.org/records/7534372)
and the [paper](https://ebooks.iospress.nl/DOI/10.3233/978-1-61499-621-7-431).

# Acknowledgments

We gratefully acknowledge the support of the following research projects and 
institutions in the development of JUBE and for granting compute time to develop JUBE. 

- UNSEEN (BMWi project, ID: 03EI1004A-F)
- Gauss Centre for Supercomputing e.V. (www.gauss-centre.eu) and the John von
Neumann Institute for Computing (NIC) on the GCS Supercomputer JUWELS at
Jülich Supercomputing Centre (JSC)
