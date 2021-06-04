from image_handler.lambda_function import lambda_handler
import json


with open('image_handler_lambda/tests/event.json') as event_file:
    event = json.load(event_file)
    event_file.close()
    result = lambda_handler(event, None)
    print(f"Output status code is: {result['statusCode']}")
