#!/bin/bash

set -euo pipefail

while [[ "${1-}" == "--"* ]] ;
do
    opt="$1";
    shift;              #expose next argument
    case "$opt" in
        "--no-colour" )
           NO_COLOUR=true;;
        "--debug" )
           DEBUG=true;;
        *) echo >&2 "deploy.sh: Invalid option: $opt"; exit 1;;
    esac
done

if [[ ! -z ${NO_COLOUR-} ]] ; then
    NO_COLOUR_CMD="--no-colour"
fi

if [[ ! -z ${DEBUG-} ]] ; then
    DEBUG_CMD="--debug"
fi

cd sceptre
bash ./scripts/deployment/deploy.sh ${NO_COLOUR_CMD-} ${DEBUG_CMD-}