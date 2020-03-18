import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

client = boto3.client('lex-runtime')
    
def lambda_handler(event, context):
    
    data = code = event['answer']
    user = code = event['user']

    response = client.post_text(
        botName='DiningConcierge',
        botAlias='$LATEST',
        userId=user,
        inputText= data)
        
    return {
        'contentType': 'PlainText',
        'statusCode': 200,
        'body': response
    }
