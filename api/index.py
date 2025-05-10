from http.server import BaseHTTPRequestHandler
from app.main import app
import json

def handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Script Generator Service'})
    } 