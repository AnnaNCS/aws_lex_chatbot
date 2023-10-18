import json
import boto3

# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    
    msg_from_user = event['messages'][0]['unstructured']['text']

    # Initiate conversation with Lex
    response = client.recognize_text(
        botId='WJCAHC7ISV',         
        botAliasId='TSTALIASID',    
        localeId='en_US',
        sessionId='439569526489737',
        text=msg_from_user)
    
    # Get message from Lex
    msg_from_lex = response.get('messages', [])
  
    unstructured_message = {
        'type': 'unstructured',
        'unstructured': {
            'text': msg_from_lex[0]['content']
        }
    }
    
    resp = {
        'statusCode': 200,
        'messages': [unstructured_message]
    }
    return resp