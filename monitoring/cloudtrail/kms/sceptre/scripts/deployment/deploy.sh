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
        *) echo >&2 "Invalid option: $opt"; exit 1;;
   esac
done

if [[ ! -z ${NO_COLOUR-} ]] ; then
    NO_COLOUR_CMD=--no-colour
fi

if [[ ! -z ${DEBUG-} ]] ; then
    DEBUG_CMD=--debug
fi

echo '--------------------------------------------------'
echo '--------------------------------------------------'
echo ~~~~~~~~~~~~~~~~ Deploying resources ~~~~~~~~~~~~~~~
echo '--------------------------------------------------'
echo '--------------------------------------------------'

echo -e '\n'
echo '--------------------'
echo 'Creating Principals '
echo '--------------------'
bash scripts/deployment/sceptre.sh ${NO_COLOUR_CMD-} ${DEBUG_CMD-} \
    --cmd="launch -y principals"

echo -e '\n'
echo '--------------------'
echo 'Creating SNS topic'
echo '--------------------'
bash scripts/deployment/sceptre.sh ${NO_COLOUR_CMD-} ${DEBUG_CMD-} \
    --cmd="launch -y sns"

echo -e '\n'
echo '--------------------'
echo 'Creating KMS CMK'
echo '--------------------'
bash scripts/deployment/sceptre.sh ${NO_COLOUR_CMD-} ${DEBUG_CMD-} \
    --cmd="launch -y kms"

echo -e '\n'
echo '-------------------------'
echo 'Deploying lambda function'
echo '-------------------------'
bash scripts/deployment/sceptre.sh ${NO_COLOUR_CMD-} ${DEBUG_CMD-} \
    --cmd="launch -y lambda"

echo -e '\n'
echo '---------------------------------------'
echo 'Creating CloudTrail trail and S3 Bucket'
echo '---------------------------------------'
bash scripts/deployment/sceptre.sh ${NO_COLOUR_CMD-} ${DEBUG_CMD-} \
    --cmd="launch -y cloudtrail"

echo '-------------------------------------------------------------------------------'
echo '-------------------------------------------------------------------------------'
echo '****************************** Congratulations ! ******************************'
echo "~~~~~~~~~~~~~~~~~~~~~~~~  Resources have been deployed. ~~~~~~~~~~~~~~~~~~~~~~~"
echo '-------------------------------------------------------------------------------'
echo '-------------------------------------------------------------------------------'