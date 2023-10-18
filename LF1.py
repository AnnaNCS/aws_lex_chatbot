import json
import os
import time
import logging
import time
import boto3
import re
import dateutil.parser
import dateutil.utils
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Pushing the lex reservation message to the sqs 
def push_to_sqs(event):
    cuisine = check_key_error(lambda: event['sessionState']['intent']['slots']['Cuisine']['value']['interpretedValue'])
    city = check_key_error(lambda: event['sessionState']['intent']['slots']['City']['value']['interpretedValue'])
    ParticipantCount = check_key_error(lambda: event['sessionState']['intent']['slots']['People']['value']['interpretedValue'])
    date = check_key_error(lambda: event['sessionState']['intent']['slots']['Date']['value']['interpretedValue'])
    time = check_key_error(lambda: event['sessionState']['intent']['slots']['Time']['value']['interpretedValue'])
    customerEmail = check_key_error(lambda: event['sessionState']['intent']['slots']['Email']['value']['interpretedValue'])

    # load the reservation information
    load_for_sqs = json.dumps({
        'City': city,
        'Cuisine': cuisine,
        'People': ParticipantCount,
        'Date': date,
        'Time': time,
        'Email': customerEmail
    })
    
    # sent the message to the sqs
    sqs = boto3.client('sqs')
    queue_url = "https://sqs.us-east-1.amazonaws.com/439569526489/messages"
    response = sqs.send_message(
        QueueUrl = queue_url,
        MessageBody = load_for_sqs
        )

# Validates the city information
def valid_city(city, resolvedValues):
    cityList = ["manhattan", "queens", "flushing", "nyc"]
    
    if len(resolvedValues) > 0:
        if city in cityList:
            return True
    return False

# Validates the cuisine information
def valid_cuisine(cuisine, resolvedValues):
    cuisineList = ["indian", "italian", "ethiopian", "american", "mexican", "japanese", "french", "spanish", "chinese"]
    
    if len(resolvedValues) > 0:
        if cuisine.lower() in cuisineList:
            return True
    return False

# Validates the people information
def valid_participant_count(ParticipantCount):
    try:
        count = int(ParticipantCount)
        if (count > 0 and count < 13):
            return True
        else:
            return False
    except ValueError:
        return False

# Validates the date information  
def valid_date(date):
    date = dateutil.parser.parse(date)
    
    if date < dateutil.utils.today():
        return False
    return True

# Validates the time information  
def valid_time(time, date):
    date = dateutil.parser.parse(date).date()
    time = dateutil.parser.parse(time).time()
    
    if datetime.combine(date, time) < datetime.now():
        return False
    return True

#checks for the valid email
def valid_email(customerEmail):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if (re.fullmatch(regex, customerEmail)):
        return True
    return False


# Checks for the key error
def check_key_error(func):
    try:
        return func()
    except TypeError:
        return None

# Return in case slot is invalid
def ask_for_valid_slot(valid, slot, msg):
    response = {
        'valid': valid,
        'slot' : slot,
        'messages' : {
            'content': msg,
            'contentType': 'PlainText'
        }
    }
    return response


def validate_slots(slots):
    city = check_key_error(lambda: slots['City']['value']['interpretedValue'])
    cuisine = check_key_error(lambda: slots['Cuisine']['value']['interpretedValue'])
    ParticipantCount = check_key_error(lambda: slots['People']['value']['interpretedValue'])
    date = check_key_error(lambda: slots['Date']['value']['interpretedValue'])
    time = check_key_error(lambda: slots['Time']['value']['interpretedValue'])
    customerEmail = check_key_error(lambda: slots['Email']['value']['interpretedValue'])
    
    if city:
        if valid_city(city, slots['City']['value']['resolvedValues']) == False:
            return ask_for_valid_slot(
                False, 
                'city', 
                'Your city area is not valid, can you please try again?'
                )
    
    if cuisine:
        if valid_cuisine(cuisine, slots['Cuisine']['value']['resolvedValues']) == False:
            return ask_for_valid_slot(
                False,
                cuisine,
                'Your cusine choice is not found, can you please choose anoether one?'.format(cuisine)
                )
    
    if ParticipantCount:
        if not valid_participant_count(slots['People']['value']['interpretedValue']):
            return ask_for_valid_slot(
                False,
                ParticipantCount,
                "Please enter valid participant number. (between 1 to 12)"
                )

    if date:
        if valid_date(slots['Date']['value']['interpretedValue']) == False:
            return ask_for_valid_slot(
                False,
                'date',
                "Please enter a valid date. (e.g. mm/dd/yy)"
                )
                
    if date and time:
        if not valid_time(slots['Time']['value']['interpretedValue'], slots['Date']['value']['interpretedValue']):
            return ask_for_valid_slot(
                False,
                time,
                "Please enter a valid time. (e.g. 7:00 PM)"
                )
    
    if customerEmail:
        if valid_email(slots['Email']['value']['interpretedValue']) == False:
            return ask_for_valid_slot(
                False,
                customerEmail,
                'Invalid email, please try again. (e.g. username@domain.com)'
                )
    
    response = {
        'valid': True
    }
                
    return response

# Set slot to Elicit
def dialogAction_elicit_slot(intent_name, slots, slot_to_elicit, msg):
    return {
        'messages': [msg],
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': {
            'name': intent_name,
            'slots': slots,
            'state': 'Failed'
            }
        }
    }


# Checking the slots
def restuarant_suggestions(intent_request):
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        
        # Validate any slots which have been specified. If any are invalid, re-elicit for their value
        re_validated_slot = validate_slots(intent_request['sessionState']['intent']['slots'])
        if re_validated_slot['valid'] == False:
            slots = intent_request['sessionState']['intent']['slots']
        
            # Updates the slot
            slots[re_validated_slot['slot']] = None
            
            response = dialogAction_elicit_slot(
                intent_request['sessionState']['intent']['name'],
                slots,
                re_validated_slot['slot'],
                re_validated_slot['messages'])
                
            intent_request['messages'] = response['messages']
            intent_request["proposedNextState"]["dialogAction"] = response['sessionState']['dialogAction']

def lambda_handler(event, context):
    
    resp = {"statusCode": 200, "sessionState": event["sessionState"]}
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    
    if "proposedNextState" not in event:
        resp["sessionState"]["dialogAction"] = {"type": "Close"}
        push_to_sqs(event)
    else:
        resp["sessionState"]["dialogAction"] = event["proposedNextState"]["dialogAction"]
        restuarant_suggestions(event)
    
    return resp

