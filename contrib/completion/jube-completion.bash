# FIXME: extend basic structure to full functionality

_jube ()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--version --verbose --debug --force --devel"
    subparsers="run continue analyse result info status comment remove
                convert update log help"

    case "${prev}" in
        run)
            COMPREPLY=($(compgen -f ${cur}))
            return 0
            ;;
        "continue")
            COMPREPLY="mycontinue"
            return 0
            ;;
        *)
    esac

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    else
        COMPREPLY=( $(compgen -W "${subparsers}" -- ${cur}) )
    fi
} &&
complete -F _jube jube
