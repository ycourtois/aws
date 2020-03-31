import gzip
import io
import json
import logging
import os

import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# environment variables array list separator is a comma
ENV_VARS_ARRAY_SEPARATOR = ","
KMS_FILTERED_ACTIONS = ["Encrypt", "Decrypt", "ReEncrypt"]


def get_records(session, bucket, key):
    """
    Loads a CloudTrail log file, decompresses it, and extracts its records.
    :param session: Boto3 session
    :param bucket: Bucket where log file is located
    :param key: Key to the log file object in the bucket
    :return: list of CloudTrail records
    """
    s3 = session.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)

    with io.BytesIO(response['Body'].read()) as obj:
        with gzip.GzipFile(fileobj=obj) as logfile:
            records = json.load(logfile)['Records']
            sorted_records = sorted(records, key=lambda r: r['eventTime'])
            return sorted_records


def get_log_file_location(event):
    """
    Generator for the bucket and key names of each CloudTrail log
    file contained in the event sent to this function from S3.
    (usually only one but this ensures we process them all).
    :param event: S3:ObjectCreated:Put notification event
    :return: yields bucket and key names
    """
    for event_record in event['Records']:
        bucket = event_record['s3']['bucket']['name']
        key = event_record['s3']['object']['key']
        yield bucket, key


def should_raise_alert(event) -> bool:
    # retrieved from environment variables
    restricted_kms_cmk_arn = os.environ['RESTRICTED_KMS_CMK_ARN'].split(ENV_VARS_ARRAY_SEPARATOR)
    is_restricted_kms_cmk = False

    is_kms_event = event['eventSource'] == 'kms.amazonaws.com'
    if is_kms_event:
        is_filtered_kms_action = event['eventName'] in KMS_FILTERED_ACTIONS
        if 'resources' in event:
            for resource in event['resources']:
                is_restricted_kms_cmk = is_restricted_kms_cmk or resource['ARN'] in restricted_kms_cmk_arn

    is_iam_principal_allowed = is_principal_allowed(event)

    status = is_kms_event and is_filtered_kms_action and is_restricted_kms_cmk and not is_iam_principal_allowed

    return status


def is_principal_allowed(event) -> bool:
    # retrieved from environment variables
    allowed_principals = os.environ['ALLOWED_PRINCIPALS'].split(ENV_VARS_ARRAY_SEPARATOR)
    logger.info('## ALLOWED PRINCIPALS')
    logger.info(allowed_principals)

    # Since user identity type may be other than 'IAMUser' and 'AssumedRole',
    # by default we assume that principal is allowed
    is_allowed = True

    if event['userIdentity']:
        if event['userIdentity']['type'] == 'IAMUser':
            is_allowed = event['userIdentity']['arn'] in allowed_principals
        elif event['userIdentity']['type'] == 'AssumedRole':
            is_allowed = event['userIdentity']['sessionContext'] and event['userIdentity']['sessionContext'][
                'sessionIssuer']['arn'] in allowed_principals

    return is_allowed


def sns_publish(session, message) -> None:
    sns = session.client('sns')

    sns.publish(
        TargetArn=os.environ['SNS_TOPIC_ARN'],
        Message=json.dumps({'default': json.dumps(message)}),
        MessageStructure='json'
    )


def handler(event, context):
    logger.info("Starting cloudtrail logs analyzer ...")
    logger.info('## EVENT')
    logger.info(event)

    mandatory_env_vars = ["ALLOWED_PRINCIPALS", "SNS_TOPIC_ARN", "RESTRICTED_KMS_CMK_ARN"]
    for var in mandatory_env_vars:
        if var not in os.environ:
            raise EnvironmentError("Failed because {} is not set.".format(var))

    # Create a Boto3 session that can be used to construct clients
    session = boto3.session.Session()

    # Get the S3 bucket and key for each log file contained in the event
    for bucket, key in get_log_file_location(event):
        # Load the CloudTrail log file and extract its records
        logger.info('Loading CloudTrail log file s3://%s/%s', bucket, key)
        records = get_records(session, bucket, key)
        logger.info('Number of records in log file: %s', len(records))

        alert_records = []
        # Process the CloudTrail records
        for record in records:
            if should_raise_alert(record):
                alert_records.append(record)

        if len(alert_records):
            logger.warning('Found %s kms actions from not allowed principal, sending notification ...',
                           len(alert_records))
            sns_publish(session, alert_records)
