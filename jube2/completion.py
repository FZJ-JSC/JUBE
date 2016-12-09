# JUBE Benchmarking Environment
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
"""Shell Completions"""

from __future__ import (print_function,
                        unicode_literals,
                        division)


import jube2.main


BASH_CASE_SINGLE_TEMPLATE = """\
        "{command}")
            COMPREPLY=($(compgen -W "{opts}" -- ${{cur}}))
            return 0
            ;;
"""

BASH_SCRIPT_TEMPLATE = """
_{command_name} ()
{{
    local cur prev words cword comm subparsers subcom

    COMPREPLY=()

    words=(${{COMP_WORDS[@]}})
    cword=COMP_CWORD
    comm=${{words[0]}}
    cur="${{words[cword]}}"
    prev="${{words[cword-1]}}"
    subcom="${{words[1]}}"
    subparsers="{subparser}"

    if [[ ${{cur}} == -* ]] ; then
        case "${{subcom}}" in
{cases_only}
            *)
        esac
    elif [[ ${{prev}} == "$comm" ]] ; then
        COMPREPLY=( $(compgen -W "${{subparsers}}" -- ${{cur}}) )
    fi
}} &&
complete -o bashdefault -o default -F _{command_name} {command_name}
"""


def complete_function_bash(args):
    """Print completion function for bash."""

    subparser = jube2.main.gen_subparser_conf()

    command_name = args.command_name[0]

    complete_options = dict()
    # Iterate over all subparsers
    for sub_name, sub in sorted(subparser.items()):
        if "arguments" not in sub:
            continue
        # Iterate over all their options
        tmp_list = [argument
                    for key in sub["arguments"]
                    for argument in key
                    if argument.startswith("--")]
        complete_options[sub_name] = " ".join(tmp_list)

    cases_only = "".join(BASH_CASE_SINGLE_TEMPLATE.format(command=command,
                                                          opts=opts)
                         for command, opts in sorted(complete_options.items()))

    subparser_str = " ".join(sorted(subparser.keys()))
    script = BASH_SCRIPT_TEMPLATE.format(
        subparser=subparser_str, cases_only=cases_only,
        command_name=command_name)
    print(script)
