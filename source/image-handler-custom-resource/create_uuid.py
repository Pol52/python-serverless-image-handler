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
import requests
import logging
import os
import uuid
import time

log_level = str(os.environ.get('LOG_LEVEL')).upper()
if log_level not in ['DEBUG', 'INFO','WARNING', 'ERROR','CRITICAL']:
    log_level = 'ERROR'
log = logging.getLogger()
log.setLevel(log_level)


def create_unique_id():
    log.info("Creating Unique ID")
    # Generate new random Unique ID
    unique_id = uuid.uuid4()
    log.debug("UUID: %s", unique_id)
    return unique_id


def send_failed_response(event, resource_id, reason):
    responseBody = {'Status': "FAILED",
                    'PhysicalResourceId': resource_id,
                    'Reason': reason,
                    'StackId': event['StackId'],
                    'RequestId': event['RequestId'],
                    'LogicalResourceId': event['LogicalResourceId']}
    log.info('RESPONSE BODY:n' + json.dumps(responseBody))
    try:
        requests.put(event['ResponseURL'], data=json.dumps(responseBody))
        return
    except Exception as e:
        log.error(e)
        raise


def send_response(event, solution_uuid):
    response_body = {
                        'Status': 'SUCCESS',
                        'PhysicalResourceId': solution_uuid,
                        'StackId': event['StackId'],
                        'RequestId': event['RequestId'],
                        'LogicalResourceId': event['LogicalResourceId'],
                        'Data': {"UUID": solution_uuid}
                    }
    log.info('RESPONSE BODY:n' + json.dumps(response_body))
    try:
        requests.put(event['ResponseURL'], data=json.dumps(response_body))
        return
    except Exception as e:
        log.error(e)
        raise


def create_application(event, context):
    new_uuid = str(create_unique_id())
    try:
        send_response(event, new_uuid)
    except Exception as e:
        log.error(e)
        send_failed_response(event, new_uuid, "Failed to create UUID")


def delete_application(event, context):
    prev_uuid = event['PhysicalResourceId']
    try:
        send_response(event, prev_uuid)
    except Exception as e:
        # If the try fails, send failure
        log.error(e)
        time.sleep(30)
        send_failed_response(event, prev_uuid, "Failed to delete " + prev_uuid)


def update_application(event, context):
    prev_uuid = event['PhysicalResourceId']
    try:
        send_response(event, prev_uuid)
    except Exception as e:
        # If the try fails, send failure
        log.error(e)
        send_failed_response(event, prev_uuid, "Failed to update " + prev_uuid)
