#!/usr/bin/python
# -*- coding: utf-8 -*-

##############################################################################
#  Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Amazon Software License (the 'License'). You may not   #
#  use this file except in compliance with the License. A copy of the        #
#  License is located at                                                     #
#                                                                            #
#      http://aws.amazon.com/asl/                                            #
#                                                                            #
#  or in the 'license' file accompanying this file. This file is distributed #
#  on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,        #
#  express or implied. See the License for the specific language governing   #
#  permissions and limitations under the License.                            #
##############################################################################
import json
import logging
import os
import ast
import requests
import time
import boto3
from botocore.client import Config
from zipfile import ZipFile
import shutil


log_level = str(os.environ.get('LOG_LEVEL')).upper()
if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    log_level = 'ERROR'
log = logging.getLogger()
log.setLevel(log_level)


def deploy_image_handler_ui(deploy_config):
    # Expected dict entries
    # deploy_config['UISourceURL']
    # deploy_config['UIBucket']
    # deploy_config['UIBucketRegion']
    # deploy_config['UIPrefix']
    # deploy_config['UIPublicRead']
    # deploy_config['FindReplace']
    # deploy_config['Deliminator']
    try:
        src_bucket, src_key = deploy_config['UISourceURL'].split("/", 1)
        file_name = src_key.rsplit("/", 1)[1]
        tmpdir = '/tmp/ui/'
        log.info("%s/%s - downloading to %s%s", src_bucket, src_key, tmpdir, file_name)

        # Clean up existing directories or files
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)
        file_path = "{}{}".format(tmpdir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

        s3 = boto3.client("s3", config=Config(signature_version='s3v4'))
        s3.download_file(src_bucket, src_key, file_path)
        log.info("File downloaded to %s", file_path)
        log.info("Extracting %s to %s", file_path, tmpdir)
        zip_file = ZipFile(file_path, 'r')
        zip_file.extractall(tmpdir)
        zip_file.close()
        log.info("Deleting %s", file_path)
        os.remove(file_path)

        if 'FindReplace' in deploy_config:
            file_path = tmpdir + "index.html"
            index_html = ''
            log.info("Opening %s", file_path)
            index_file = open(file_path, 'r')
            log.info("Reading %s", file_path)
            for line in index_file:
                for fr in deploy_config['FindReplace'].split(','):
                    f, r = fr.split(deploy_config['Deliminator'])
                    line = line.replace(f, r)
                index_html += line
            index_file.close()
            log.info("Writing changed file")
            index_file = open(file_path, 'w')
            index_file.write(index_html)
            index_file.close()

            log.info("Uploading %s/* to %s/%s", tmpdir, deploy_config['UIBucket'], deploy_config['UIPrefix'])
            # Grant bucket owner full control of objects (in case this is deployed to another account's bucket)
            extra_args = {'ACL': 'bucket-owner-full-control'}
            log.debug("ExtraArgs = %s", extra_args)
            for root, dirs, files in os.walk(tmpdir):
                for filename in files:
                    # construct the full local path
                    local_path = os.path.join(root, filename)
                    # construct the full UI path
                    relative_path = os.path.relpath(local_path, tmpdir)
                    s3_path = os.path.join(deploy_config['UIPrefix'], relative_path)
                    log.debug("local_path = %s; relative_path = %s", local_path, relative_path)
                    log.info("Uploading %s...", s3_path)
                    # Setting content type
                    if filename.endswith('.htm') or filename.endswith('.html'):
                        extra_args.update({"ContentType": "text/html"})
                    if filename.endswith('.css'):
                        extra_args.update({"ContentType": "text/css"})
                    if filename.endswith('.js'):
                        extra_args.update({"ContentType": "application/javascript"})
                    if filename.endswith('.png'):
                        extra_args.update({"ContentType": "image/png"})
                    if filename.endswith('.jpeg') or filename.endswith('.jpg'):
                        extra_args.update({"ContentType": "image/jpeg"})
                    if filename.endswith('.gif'):
                        extra_args.update({"ContentType": "image/gif"})
                    s3.upload_file(Filename=local_path, Bucket=deploy_config['UIBucket'], Key=s3_path,
                                   ExtraArgs=extra_args)
    except Exception as e:
        log.error("Error uploading UI. Error: %s", e)
        raise


def delete_image_handler_ui(deploy_config):
    # Expected dict entries
    # deploy_config['UIBucket']
    # deploy_config['UIPrefix']
    log.info("Deleting Serverless Image Handler UI from %s/%s", deploy_config['UIBucket'], deploy_config['UIPrefix'])
    try:
        s3 = boto3.client("s3", config=Config(signature_version='s3v4'))
        log.info("Listing UI objects in %s/%s", deploy_config['UIBucket'], deploy_config['UIPrefix'])
        for s3object in s3.list_objects(Bucket=deploy_config['UIBucket'], Prefix=deploy_config['UIPrefix'])['Contents']:
            log.info("Deleting %s/%s", deploy_config['UIBucket'], s3object['Key'])
            s3.delete_object(Bucket=deploy_config['UIBucket'], Key=s3object['Key'])
        log.info("Deleting %s/%s", deploy_config['UIBucket'], deploy_config['UIPrefix'])
        s3.delete_object(Bucket=deploy_config['UIBucket'], Key=deploy_config['UIPrefix'])
    except Exception as e:
        log.error("Error deleting UI. Error: %s", e)
        raise


def send_failed_response(event, resource_id, reason):
    response_body = {'Status': "FAILED",
                    'PhysicalResourceId': resource_id,
                    'Reason': reason,
                    'StackId': event['StackId'],
                    'RequestId': event['RequestId'],
                    'LogicalResourceId': event['LogicalResourceId']}
    log.info('RESPONSE BODY:n' + json.dumps(response_body))
    try:
        requests.put(event['ResponseURL'], data=json.dumps(response_body))
        return
    except Exception as e:
        log.error("Error sending FAILED response message: %s", e)
        raise


def send_response(event, resource_id):
    response_body = {
        'Status': 'SUCCESS',
        'PhysicalResourceId': resource_id,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId']
    }
    log.info('RESPONSE BODY:n' + json.dumps(response_body))
    try:
        requests.put(event['ResponseURL'], data=json.dumps(response_body))
        return
    except Exception as e:
        log.error("Error sending SUCCESS response", e)
        raise


def create_application(event, context):
    # Create S3 client, download the UI, and push it to the customer's bucket
    resourceId = ""
    try:
        deploy = ast.literal_eval(event['ResourceProperties']['DeployUI'])
        resourceId = deploy['UIBucket'] + '/' + deploy['UIPrefix']
        deploy_image_handler_ui(deploy)
        # Only send response if the RequestType was a Create
        if event['RequestType'] == 'Create':
            send_response(event, resourceId)
    except Exception as e:
        log.error(e)
        send_failed_response(event, resourceId, "Failed to deploy Image Handler UI")


def delete_application(event, context):
    resource_id = event['PhysicalResourceId']
    # Create an S3 client and remove UI
    try:
        deploy = ast.literal_eval(event['ResourceProperties']['DeployUI'])
        delete_image_handler_ui(deploy)
        if event['RequestType'] == 'Delete':
            send_response(event, resource_id)
    except Exception as e:
        # If the try fails, send failure
        log.error(e)
        time.sleep(30)
        send_failed_response(event, resource_id, "Failed to delete " + resource_id)


def update_application(event, context):
    resource_id = event['PhysicalResourceId']
    # When called to update, we will simply replace old with new
    try:
        delete_application(event, context)
        create_application(event, context)
        send_response(event, resource_id)
    except Exception as e:
        # If the try fails, send failure
        log.error(e)
        send_failed_response(event, resource_id, "Failed to update " + resource_id)
