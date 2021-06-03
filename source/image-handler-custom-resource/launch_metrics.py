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


import datetime
import json
import logging
import os
import ast
import requests
import time
from urllib.request import Request
from urllib.request import urlopen
from urllib import parse


log_level = str(os.environ.get('LOG_LEVEL')).upper()
if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    log_level = 'ERROR'
log = logging.getLogger()
log.setLevel(log_level)


def send_data(event):
    log.debug('Starting send data')
    time_now = datetime.datetime.utcnow().isoformat()
    time_stamp = str(time_now)
    log.debug('CFNRequestType = %s', event['RequestType'])

    post_dict = ast.literal_eval(event['ResourceProperties']['SendAnonymousData'])
    log.debug("postDict = %s", post_dict)

    post_dict['Data'].update({'CFTemplate': event['RequestType']})
    post_dict['Data'].update({'Company': 'AWS'})
    post_dict['Data'].update({'Name': 'AWS Serverless Image Handler'})
    log.debug("postDict['Data'] = %s", post_dict['Data'])

    post_dict['TimeStamp'] = time_stamp
    post_dict['Solution'] = 'SO0023'
    log.info("Posing the following: %s", post_dict)

    # API Gateway URL to make HTTP POST call
    url = 'https://metrics.awssolutionsbuilder.com/generic'
    data = parse.urlencode(post_dict).encode("utf-8")
    headers = {'content-type': 'application/json'}
    req = Request(url, data, headers)
    rsp = urlopen(req)
    content = rsp.read()
    rsp_code = rsp.getcode()
    log.info('Response Code: {}'.format(rsp_code))
    log.debug('Response Content: {}'.format(content))


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
        log.error(e)
        raise


def send_response(event, response_id):
    responseBody = {
        'Status': 'SUCCESS',
        'PhysicalResourceId': response_id,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId']
    }
    log.info('RESPONSE BODY:n' + json.dumps(responseBody))
    try:
        requests.put(event['ResponseURL'], data=json.dumps(responseBody))
        return
    except Exception as e:
        log.error(e)
        raise


def create_application(event, context):
    resource_id = context.log_stream_name
    try:
        log.debug("Sending Create event data: %s", event)
        send_data(event)
        log.debug("Sending successful Create response")
        send_response(event, resource_id)
    except Exception as e:
        log.error(e)
        send_failed_response(event, resource_id, "Failed to send data")


def delete_application(event, context):
    resource_id = event['PhysicalResourceId']
    try:
        log.debug("Sending Delete event data: %s", event)
        send_data(event)
        log.debug("Sending successful Delete response")
        send_response(event, resource_id)
    except Exception as e:
        # If the try fails, send failure
        log.error(e)
        time.sleep(30)
        send_failed_response(event, resource_id, "Failed to delete " + resource_id)


def update_application(event, context):
    resource_id = event['PhysicalResourceId']
    try:
        log.debug("Nothing to update - sending successful Update response")
        send_response(event, resource_id)
    except Exception as e:
        # If the try fails, send failure
        log.error(e)
        send_failed_response(event, resource_id, "Failed to update " + resource_id)
