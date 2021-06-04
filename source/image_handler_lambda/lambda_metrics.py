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
import timeit
from urllib.request import Request
from urllib.request import urlopen
from pkg_resources import get_distribution
from thumbor.url import Url
from urllib import parse


def send_data(event, result, start_time):
    time_now = datetime.datetime.utcnow().isoformat()
    time_stamp = str(time_now)
    post_dict = {}
    size = '-'
    filters = Url.parse_decrypted(event['path'])
    del filters['image']
    if int(result['statusCode']) == 200:
        size = (len(result['body'] * 3)) / 4
    post_dict['Data'] = {
        'Version': get_distribution('image_handler').version,
        'Company': 'AWS',
        'Name': 'AWS Serverless Image Handler',
        'Region': os.environ.get('AWS_DEFAULT_REGION'),
        'Filters': filters,
        'StatusCode': result['statusCode'],
        'ResponseSize': size,
        'ResponseTime': round(timeit.default_timer() - start_time, 3)
    }
    post_dict['TimeStamp'] = time_stamp
    post_dict['Solution'] = 'SO0023'
    post_dict['UUID'] = os.environ.get('UUID')
    # API Gateway URL to make HTTP POST call
    url = 'https://metrics.awssolutionsbuilder.com/generic'
    data = parse.urlencode(post_dict).encode("utf-8")
    headers = {'content-type': 'application/json'}
    req = Request(url, data, headers)
    rsp = urlopen(req)
    content = rsp.read()
    rsp_code = rsp.getcode()
    logging.debug('Response Code: {}'.format(rsp_code))
    logging.debug('Response Content: {}'.format(content))
    return req
