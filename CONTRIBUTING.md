# Contributing to JUBE

If you are interested in doing so, you can:

- [Send feedback](#send-feedback)
- [Contribute to Code](#contribute-to-code)

We are happy to receive them!

## Send Feedback

Report any bugs or send us requests [here](https://github.com/FZJ-JSC/JUBE/issues).
Please try to avoid duplications and describe your feedback as best as possible.
Alternatively, you can contact the JSC JUBE developers via the following email address:
[jube.jsc@fz-juelich.de](mailto:jube.jsc@fz-juelich.de)

## Contribute to Code

You are welcome to contribute to JUBE's code! To do so, please fork the repository on [GitHub](https://github.com/FZJ-JSC/JUBE) and create a pull request (PR). Contributions should follow the following rules:

1.  We suggest to follow some [Guidelines for Contributions](#guidelines-for-contributions) (we also try to follow them, although not always successfully)
2.  The code is currently distributed under the GPLv3 License
3.  You should **agree to the [Contributors License Agreement](#jube-contributor-license-agreement)**


### Guidelines for Contributions

Please, try to follow these guidelines for your code contributions:

- Add comments when possible
- Use clean code
- Use 4 spaces for indentation
- Update the documentation in `docs` and make sure it is properly formatted
- Update the `docs/glossar.rst` file (Don't forget to update the `general structure` section if necessary)
- Update the `docs/commandline.rst` file if you have modified or added command line options
- Adapt `contrib/schema/*` files and yaml converter corresponding to newly developed options
- Conform the source code to pep8, for example with `autopep8`
- Add new examples within `examples`, if there are new features
- Extend `docs/release_notes.rst` with small sentence about new feature, change or fix information
- Extend and execute testsuite `tests/run_all_tests.py` and debug if necessary
- Update the `AUTHORS` file if necessary
- Prefer to use `git rebase` instead of `git merge`, to keep a cleaner commit history
- Test your code before sending a PR

### JUBE Contributor License Agreement

Thank you for your interest in contributing to JUBE ("We" or "Us").

The purpose of this contributor agreement is to clarify and document the rights granted by contributors to Us.
To make this document effective, please follow the instructions below.

#### How to use this CLA

If You do not own the Copyright in the entire work of authorship, any other author of the Contribution must also sign this.

If you contribute outside of any legal obligations towards third parties, you may do so without the additional steps below.

If You are an employee and have created the Contribution as part of your employment, You need to have Your employers approval as a Legal Entity.

If you are a Legal Entity you must provide and update a list of your employees that will contribute to the Material, as well as your contact information. All contributions of employees must be individualy attributable to each one.

#### Definitions

"You" means the individual Copyright owner who Submits a Contribution to Us.

"Legal Entity" means an entity that is not a natural person.

"Contribution" means any original work of authorship, including any original modifications or additions to an existing work of authorship, Submitted by You to Us, in which You own the Copyright.

"Copyright" means all rights protecting works of authorship, including copyright, moral and neighboring rights, as appropriate, for the full term of their existence.

"Material" means the software or documentation made available by Us to third parties. When this Agreement covers more than one software project, the Material means the software or documentation to which the Contribution was Submitted. After You Submit the Contribution, it may be included in the Material.

"Submit" means any act by which a Contribution is transferred to Us by You by means of tangible or intangible media, including but not limited to electronic mailing lists, source code control systems, and issue tracking systems that are managed by, or on behalf of, Us, but excluding any transfer that is conspicuously marked or otherwise designated in writing by You as "Not a Contribution."

"Documentation" means any non-software portion of a Contribution.

#### Rights and Obligations

You hereby grant to Us a worldwide, royalty-free, non-exclusive, perpetual and irrevocable license, with the right to transfer an unlimited number of licenses or to grant sublicenses to third parties, under the Copyright covering the Contribution to use the Contribution by all means.

We agree to (sub)license the Contribution or any Materials containing it, based on or derived from your Contribution non-exclusively under the terms of any licenses the Free Software Foundation classifies as Free Software License, and which are approved by the Open Source Initiative as Open Source licenses.

#### Copyright

You warrant, that you are legitimated to license the Contribution to us.

#### Acceptance of the CLA

By submitting your Contribution via the Repository you accept this agreement.

#### Liability

Except in cases of willful misconduct or physical damage directly caused to natural persons, the Parties will not be liable for any direct or indirect, material or moral, damages of any kind, arising out of the Licence or of the use of the Material, including, without limitation, damages for loss of goodwill, work stoppage, computer failure or malfunction, loss of data or any commercial damage. However, the Licensor will be liable under statutory product liability laws as far such laws apply to the Material.

#### Warranty

The Material is a work in progress, which is continuously being improved by numerous Contributors. It is not a finished work and may therefore contain defects or "bugs" inherent to this type of development. For the above reason, the Material is provided on an "as is" basis and without warranties of any kind concerning the Material, including without limitation, merchantability, fitness for a particular purpose, absence of defects or errors, accuracy, non-infringement of intellectual property rights other than copyright.

#### Miscellaneous

This Agreement and all disputes, claims, actions, suits or other proceedings arising out of this agreement or relating in any way to it shall be governed by the laws of Germany excluding its private international law provisions. If any provision of this Agreement is found void and unenforceable, such provision will be replaced to the extent possible with a provision that comes closest to the meaning of the original provision and that is enforceable. The terms and conditions set forth in this Agreement shall apply notwithstanding any failure of essential purpose of this Agreement or any limited remedy to the maximum extent possible under law. You agree to notify Us of any facts or circumstances of which You become aware that would make this Agreement inaccurate in any respect.