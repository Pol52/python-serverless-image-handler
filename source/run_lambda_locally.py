from image_handler_lambda.lambda_function import start_server, lambda_handler
import json
import pydevd_pycharm as debugger
try:
    debugger.settrace('192.168.1.204', port=53630, stdoutToServer=True, stderrToServer=True)
except ConnectionError:
    print('Debugger unavailable')


start_server()
with open('image_handler_lambda/tests/event.json') as event_file:
    event = json.load(event_file)
    event_file.close()
    result = lambda_handler(event)
    print(f"Output status code is: {result['statusCode']}")
