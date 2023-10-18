import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from boto3.dynamodb.conditions import Key
from botocore.vendored import requests

REGION = 'us-east-1'
HOST = 'search-domainnew-pbje5ydguhee4vwekzjjosqaby.us-east-1.es.amazonaws.com'
INDEX = 'restaurants'
db = boto3.resource('dynamodb').Table('final_db')

def query(term):
    q = {'size': 5, 'query': {'multi_match': {'query': term}}}

    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)

    res = client.search(index=INDEX, body=q)
    hits = res['hits']['hits']
    results = []
    for hit in hits:
        results.append(hit['_source'])
    return results


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
                    
                    
def queryDynamo(ids):
    results = []
    for id in ids:
        response = db.query(KeyConditionExpression = Key("Business ID").eq(id))
        results.append(response["Items"][0])
    return results


def lambda_handler(event, context):
    sqs_queue_url = 'https://sqs.us-east-1.amazonaws.com/439569526489/messages'  # Replace with your SQS queue URL
    
    # Receive a message from the SQS queue
    sqs = boto3.client('sqs')
    response = sqs.receive_message(
        QueueUrl=sqs_queue_url,
        AttributeNames=[
            'All'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0)
        
    d = response['Messages'][0]
    msg_body = json.loads(d['Body'])

    if 'Messages' in response:
        # Extract the message body from the received message
        message = msg_body
        # Extract data from the message slots
        city = msg_body.get('City')
        cuisine = msg_body.get('Cuisine')
        date = msg_body.get('Date')
        people = msg_body.get('People')
        time = msg_body.get('Time')
        email = 'ss6960@columbia.edu'
        
        # Getting the message from the open source
        query_resp = query(cuisine)
    
        ids = []
        for i in range(0,5):
            ids.append(query_resp[i]['restaurant'])
        
        # Pulling the restaurant information from the dynamoDB
        db_rest = queryDynamo(ids)
        
        # Sending the confirmation to the email
        
        client = boto3.client("ses")
        subject = "Reservation Details"
        
        # Create the HTML body using the data from the message slots
        body = f"Hello, you have a reservation for {people} people at {time} in {city} on {date} for {cuisine} cuisine."
        for i in range(0,5): 
            body += str(i) + ': ' + db_rest[i]['Name'] + 'at' + db_rest[i]['Address']+'\n'
            
        # Send the email
        email_response = client.send_email(
            Source = "ss6960@columbia.edu",
            Destination = {"ToAddresses": [email]},
            Message = {"Subject": {"Data": subject}, "Body": {"Html": {"Data": body}}}
        )
        
        # Delete the received message from the SQS queue
        receipt_handle = response['Messages'][0]['ReceiptHandle']
        sqs.delete_message(
            QueueUrl = sqs_queue_url,
            ReceiptHandle = receipt_handle
        )
        
        return email_response
    
    else:
        return "No messages available in the queue."