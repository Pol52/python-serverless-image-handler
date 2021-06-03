from image_handler_lambda.lambda_function import start_server, lambda_handler
import json


start_server()
with open('image_handler_lambda/tests/event.json') as event_file:
    event = json.load(event_file)
    event_file.close()
    result = lambda_handler(event)
    print(f"Output status code is: {result['statusCode']}")
