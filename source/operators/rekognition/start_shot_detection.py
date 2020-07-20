# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# PURPOSE:
#   Lambda function to perform Rekognition tasks on image and video files
#
###############################################################################

import os
import json
import urllib
import boto3
from botocore import config

from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane

operator_name = os.environ['OPERATOR_NAME']
output_object = OutputHelper(operator_name)


mie_config = json.loads(os.environ['botoConfig'])
config = config.Config(**mie_config)
rek = boto3.client('rekognition-segment-detection')


# Recognizes labels in an image
def detect_labels(bucket, key):
    try:
        response = rek.detect_labels(Image={'S3Object':{'Bucket':bucket, 'Name':key}})
    except Exception as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(LabelDetectionError=str(e))
        raise MasExecutionError(output_object.return_output_object())
    return response


# Recognizes labels in a video
def start_label_detection(bucket, key):
    try:
        response = rek.start_segment_detection(
            Video={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            NotificationChannel={
                'SNSTopicArn': os.environ['REKOGNITION_SNS_TOPIC_ARN'],
                'RoleArn': os.environ['REKOGNITION_ROLE_ARN']
            },
            SegmentTypes=['SHOT'],
            Filters={
                'ShotFilter': {
                    'MinSegmentConfidence': 50
                }
            }
        )
        print('Job Id (shot_detection): ' + response['JobId'])
        return response['JobId']
    except Exception as e:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(LabelDetectionError=str(e))
        raise MasExecutionError(output_object.return_output_object())


# Lambda function entrypoint:
def lambda_handler(event, context):
    print("We got the following event:\n", event)
    try:
        if "Video" in event["Input"]["Media"]:
            s3bucket = event["Input"]["Media"]["ProxyEncode"]["S3Bucket"]
            s3key = event["Input"]["Media"]["ProxyEncode"]["S3Key"]
        elif "Image" in event["Input"]["Media"]:
            s3bucket = event["Input"]["Media"]["Image"]["S3Bucket"]
            s3key = event["Input"]["Media"]["Image"]["S3Key"]
        workflow_id = str(event["WorkflowExecutionId"])
        asset_id = event['AssetId']
    except Exception:
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(LabelDetectionError="No valid inputs")
        raise MasExecutionError(output_object.return_output_object())
    print("Processing s3://"+s3bucket+"/"+s3key)
    valid_video_types = [".avi", ".mp4", ".mov"]
    valid_image_types = [".png", ".jpg", ".jpeg"]
    file_type = os.path.splitext(s3key)[1].lower()
    if file_type in valid_image_types:
        # Image processing is synchronous.
        response = detect_labels(s3bucket, urllib.parse.unquote_plus(s3key))
        output_object.add_workflow_metadata(AssetId=asset_id,WorkflowExecutionId=workflow_id)
        dataplane = DataPlane()
        metadata_upload = dataplane.store_asset_metadata(asset_id, operator_name, workflow_id, response)
        if "Status" not in metadata_upload:
            output_object.update_workflow_status("Error")
            output_object.add_workflow_metadata(
                LabelDetectionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
            raise MasExecutionError(output_object.return_output_object())
        else:
            if metadata_upload["Status"] == "Success":
                print("Uploaded metadata for asset: {asset}".format(asset=asset_id))
                output_object.update_workflow_status("Complete")
                return output_object.return_output_object()
            elif metadata_upload["Status"] == "Failed":
                output_object.update_workflow_status("Error")
                output_object.add_workflow_metadata(
                    LabelDetectionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                raise MasExecutionError(output_object.return_output_object())
            else:
                output_object.update_workflow_status("Error")
                output_object.add_workflow_metadata(
                    LabelDetectionError="Unable to upload metadata for asset: {asset}".format(asset=asset_id))
                raise MasExecutionError(output_object.return_output_object())
    elif file_type in valid_video_types:
        # Video processing is asynchronous.
        job_id = start_label_detection(s3bucket, urllib.parse.unquote_plus(s3key))
        output_object.update_workflow_status("Executing")
        output_object.add_workflow_metadata(JobId=job_id, AssetId=asset_id, WorkflowExecutionId=workflow_id)
        return output_object.return_output_object()
    else:
        print("ERROR: invalid file type")
        output_object.update_workflow_status("Error")
        output_object.add_workflow_metadata(LabelDetectionError="Not a valid file type")
        raise MasExecutionError(output_object.return_output_object())
