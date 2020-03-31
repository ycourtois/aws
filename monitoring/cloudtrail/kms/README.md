# Infrastructure Deployment

## Context

This POC is intended to show how analyze cloudtrail logs in a S3 bucket to track API calls.
To do so, a lambda function is triggered and send a SNS notification if a matched event is found.

## Installation

### AWS CLI installation guide

https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html

### Sceptre installation guide

It is strongly advised to create a virtual environment to install sceptre.
More information at : https://docs.aws.amazon.com/fr_fr/cli/latest/userguide/install-virtualenv.html

Run `pip install sceptre`
Run `pip install sceptre-s3-packager`

More information at https://sceptre.cloudreach.com/latest/docs/install.html and https://pypi.org/project/sceptre-s3-packager/

### Full documentation

https://sceptre.cloudreach.com/latest/

## Deployment

### Initialization

Execute the following command : `bash scripts/deploy.sh`