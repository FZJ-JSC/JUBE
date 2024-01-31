<div align="center">
<img src="share/jube/logo/logo.svg" alt="JUBE" height="3em"/>

</div>


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7534372.svg)](https://doi.org/10.5281/zenodo.7534372)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# What is JuBE?

The JUBE benchmarking environment provides a script based framework to easily create benchmark sets,
run those sets on different computer systems and evaluate the results. It is actively developed by
[Juelich Supercomputing Centre](https://www.fz-juelich.de/en/ias/jsc). It focuses on managing
complexity of combinatorial benchmarks and ensuring reproducibility of the benchmarks. Jube provides
support for varied workflows and ability to use vendor-supplied platform configurations. The
benchmark configuration and scripts can be specified in either a YAML or an XML format. Jube works
on linux and macOS and has first class support for supercomputer scheduling systems like Slurm and
PBS.


## Documentation

Jube is available on `pypi` and can be installed using `pip`. Jube needs **python 3.2** or higher.

```
pip(x) install jube
```

The documentation for jube consists of two parts:
- [User Guide](https://apps.fz-juelich.de/jsc/jube/jube2/docu/index.html) : The user guide explains how to use jube.
- [Example](https://github.com/FZJ-JSC/jube-configs): Curated examples of JUBE benchmarks.

For more information on the design and architecture of Jube, please refer to the [paper
paper](https://ebooks.iospress.nl/DOI/10.3233/978-1-61499-621-7-431).


## Community and Contributing

Jube is an open-source project and we welcome your questions, discussions and contributions.
Questions can be asked on the discussion forum and issues can be reported in the issue tracker. We
also welcome contributions in the form of pull requests. Contributions can be anything from
bugfixers, to documentation to new features. If you are unsure about anything, please feel free to
ask on the discussion forum first.

- **[Issue Tracker](https://issue.com)**
- **[Github Discussions](https://discussions.com)**
- **[Pull Requests](https://pull.com)**

Please ensure that your contributions  to Jube are compliant with the [developer guidelines](
        https://apps.fz-juelich.de/jsc/jube/jube2/docu/devel.html).

# Citing JuBE

If you use Jube in your work, please cite [software release](https://zenodo.org/records/7534373)
and the [paper](https://ebooks.iospress.nl/DOI/10.3233/978-1-61499-621-7-431).

# Acknowledgments

We gratefully acknowledge the following reserach projects and institutions for their support in the development of JUBE2 and granting compute time to develop JUBE2.

- UNSEEN (BMWi project, ID: 03EI1004A-F)
- Gauss Centre for Supercomputing e.V. (www.gauss-centre.eu) and the John von Neumann Institute for Computing (NIC) on the GCS Supercomputer JUWELS at Jülich Supercomputing Centre (JSC)
