import os

import boto3
import botocore
from moto import mock_s3, mock_sns

from app import handler
from .utils import UtilTestCase

S3_BUCKET = "trail_bucket"
S3_KEY_KMS_EVENTS = "kms_events.json.gz"
S3_KEY_OTHER_EVENTS = "other_events.json.gz"
SNS_TOPIC_NAME = "alert_topic"


@mock_s3
@mock_sns
class TestApp(UtilTestCase):

    def setUp(self):
        self._populate_s3_bucket()
        self._create_sns_topic()

    def tearDown(self):
        self._empty_s3_bucket()
        self._delete_sns_topic()

    def _empty_s3_bucket(self):
        s3 = boto3.resource(
            "s3",
            region_name="eu-west-1",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
        )
        bucket = s3.Bucket(S3_BUCKET)
        for key in bucket.objects.all():
            key.delete()
        bucket.delete()

    def _populate_s3_bucket(self):
        s3_client = boto3.client(
            "s3",
            region_name="eu-west-1",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
        )
        try:
            s3 = boto3.resource(
                "s3",
                region_name="eu-west-1",
                aws_access_key_id="fake_access_key",
                aws_secret_access_key="fake_secret_key",
            )
            s3.meta.client.head_bucket(Bucket=S3_BUCKET)
        except botocore.exceptions.ClientError:
            pass
        else:
            err = "{bucket} should not exist.".format(bucket=S3_BUCKET)
            raise EnvironmentError(err)
        s3_client.create_bucket(Bucket=S3_BUCKET)
        current_dir = os.path.dirname(__file__)
        cloudtrail_events_dir = os.path.join(current_dir, "cloudtrail_events", "gzip")
        self._upload_cloudtrail_events(S3_BUCKET, cloudtrail_events_dir)

    def _create_sns_topic(self):
        self.sns_client = boto3.client(
            "sns",
            region_name="eu-west-1",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
        )

        self.topic_arn = self.sns_client.create_topic(Name=SNS_TOPIC_NAME)['TopicArn']

    def _delete_sns_topic(self):
        self.sns_client.delete_topic(TopicArn=self.topic_arn)

    @staticmethod
    def _upload_cloudtrail_events(bucket: str, cloudtrail_events_dir: str) -> None:
        client = boto3.client("s3")
        fixtures_paths = [
            os.path.join(path, filename)
            for path, _, files in os.walk(cloudtrail_events_dir)
            for filename in files
        ]
        for path in fixtures_paths:
            key = os.path.relpath(path, cloudtrail_events_dir)
            client.upload_file(Filename=path, Bucket=bucket, Key=key)

    @staticmethod
    def _get_s3_event_kms():
        return {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": "eu-west-1",
                    "eventTime": "2019-11-03T19:37:27.192Z",
                    "eventName": "ObjectCreated:Put",
                    "userIdentity": {
                        "principalId": "AWS:AIDAINPONIXQXGT5NGHY6"
                    },
                    "requestParameters": {
                        "sourceIPAddress": "192.168.0.1"
                    },
                    "responseElements": {
                        "x-amz-request-id": "D82B88E5F771F645",
                        "x-amz-id-2": "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "828aa6fc-f7b5-4305-8584-487c791949c1",
                        "bucket": {
                            "name": S3_BUCKET,
                            "ownerIdentity": {
                                "principalId": "A3I5XTEXAMAI3E"
                            },
                            "arn": "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
                        },
                        "object": {
                            "key": S3_KEY_KMS_EVENTS,
                            "size": 1305107,
                            "eTag": "b21b84d653bb07b05b1e6b33684dc11b",
                            "sequencer": "0C0F6F405D6ED209E1"
                        }
                    }
                }
            ]
        }

    @staticmethod
    def _get_s3_event_other():
        return {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": "eu-west-1",
                    "eventTime": "2019-11-03T19:37:27.192Z",
                    "eventName": "ObjectCreated:Put",
                    "userIdentity": {
                        "principalId": "AWS:AIDAINPONIXQXGT5NGHY6"
                    },
                    "requestParameters": {
                        "sourceIPAddress": "192.168.0.1"
                    },
                    "responseElements": {
                        "x-amz-request-id": "D82B88E5F771F645",
                        "x-amz-id-2": "vlR7PnpV2Ce81l0PRw6jlUpck7Jo5ZsQjryTjKlc5aLWGVHPZLj5NeC6qMa0emYBDXOo6QBU0Wo="
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "828aa6fc-f7b5-4305-8584-487c791949c1",
                        "bucket": {
                            "name": S3_BUCKET,
                            "ownerIdentity": {
                                "principalId": "A3I5XTEXAMAI3E"
                            },
                            "arn": "arn:aws:s3:::lambda-artifacts-deafc19498e3f2df"
                        },
                        "object": {
                            "key": S3_KEY_OTHER_EVENTS,
                            "size": 1305107,
                            "eTag": "b21b84d653bb07b05b1e6b33684dc11b",
                            "sequencer": "0C0F6F405D6ED209E1"
                        }
                    }
                }
            ]
        }

    def test_handler_kms_event_allowed_principal_should_not_send_notification(self):
        # given
        os.environ[
            'ALLOWED_PRINCIPALS'] = "arn:aws:iam::123456789012:user/MyAllowedUser,arn:aws:iam::123456789012:role/MyAllowedRoleToBeAssumed"
        os.environ['SNS_TOPIC_ARN'] = self.topic_arn
        os.environ[
            'RESTRICTED_KMS_CMK_ARN'] = "arn:aws:kms:us-east-1:012345678901:key/8d3acf57-6bba-480a-9459-ed1b8e79d3d0"

        event = self._get_s3_event_kms()

        # when
        handler(event, None)

    def test_handler_kms_event_not_allowed_principal_should_send_notification(self):
        # given
        os.environ[
            'ALLOWED_PRINCIPALS'] = "arn:aws:iam::123456789012:user/MyAllowedUser2,arn:aws:iam::123456789012:role/MyAllowedRole2ToBeAssumed"
        os.environ['SNS_TOPIC_ARN'] = self.topic_arn
        os.environ[
            'RESTRICTED_KMS_CMK_ARN'] = "arn:aws:kms:us-east-1:012345678901:key/8d3acf57-6bba-480a-9459-ed1b8e79d3d0"

        event = self._get_s3_event_kms()

        # when
        handler(event, None)

    def test_handler_no_kms_event_should_not_send_notification(self):
        # given
        os.environ[
            'ALLOWED_PRINCIPALS'] = "arn:aws:iam::123456789012:user/MyAllowedUser,arn:aws:iam::123456789012:role/MyAllowedRoleToBeAssumed"
        os.environ['SNS_TOPIC_ARN'] = self.topic_arn
        os.environ[
            'RESTRICTED_KMS_CMK_ARN'] = "arn:aws:kms:us-east-1:012345678901:key/8d3acf57-6bba-480a-9459-ed1b8e79d3d0"

        event = self._get_s3_event_other()

        # when
        handler(event, None)
