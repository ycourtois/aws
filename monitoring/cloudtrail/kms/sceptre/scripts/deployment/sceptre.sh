#!/bin/bash

set -euo pipefail

display_usage() {
    echo
    echo "Usage: $0"
    echo
    echo " --debug to enable verbose mode "
    echo " --no-colour to turn off output colouring "
    echo " --env env-name or --env=env-name "
    echo " --profile profile-name or --profile=profile-name "
    echo " --cmd commands or --cmd=\"commands\" "
    echo
}

raise_error() {
    local error_message="$@"
    echo "${error_message}" 1>&2;
}

exec_cmd() {
    if [[ -z $@ ]] ; then
        raise_error "Commands instructions are missing"
        exit 1
    fi

    if [[ ! -z ${PROFILE-} ]] ; then
        echo "Specific profile detected: ${PROFILE}"
        PROFILE_CMD="--var "profile=${PROFILE}""
    fi

    if [[ ! -z ${DEBUG-} ]] ; then
        echo "Debug mode enabled"
        DEBUG_CMD=--debug
    fi

    if [[ ! -z ${NO_COLOUR-} ]] ; then
        echo "Colouring turned off"
        NO_COLOUR_CMD=--no-colour
    fi

    if [[ ! -z ${IGNORE_DEP-} ]] ; then
        echo "Dependencies will be ignored"
        IGNORE_DEP_CMD=--ignore-dependencies
    fi

    exec sceptre ${DEBUG_CMD-} ${NO_COLOUR_CMD-} ${IGNORE_DEP_CMD-} \
        --var-file=varfiles/settings.yaml \
        --var-file=varfiles/cloudtrail.yaml \
        ${PROFILE_CMD-} \
        "$@"

}

check_parameter_value() {
    if [[ -z "$1" ]] ; then
        raise_error "Missing parameter value"
        exit 1
    fi
}

if [[ -z "${1-}" ]] ; then
    raise_error "Expected arguments to be present"
    display_usage
else
    if [[ "$1" != "--"*  ]] ; then
        raise_error "Parameters must begin with '--'"
        exit 1
    fi
    while [[ "${1-}" == "--"* ]] ;
    do
        opt="$1";
        shift;              #expose next argument
        case "$opt" in
            "--debug" )
               DEBUG=true;;
            "--no-colour" )
               NO_COLOUR=true;;
            "--ignore-dependencies" )
               IGNORE_DEP=true;;
            "--profile" )
               check_parameter_value "${1-}"
               PROFILE="$1"; shift;;
            "--profile="* )     # alternate format: --profile=profile-name
               PROFILE="${opt#*=}";;
            "--cmd" )
               check_parameter_value "${1-}"
               CMD_ARGS="$@"; break;;
            "--cmd="* )     # alternate format: --cmd=cmd
               CMD_ARGS="${opt#*=}"; break;;
            *) echo >&2 "Invalid option: $opt"; exit 1;;
       esac
    done
    exec_cmd ${CMD_ARGS-}
fi

