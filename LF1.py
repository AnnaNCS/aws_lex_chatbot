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


# --------------------------------SQS Fun-------------------------------------#

def push_to_sqs(event):
    print(event)
    
    cuisine = check_key_error(lambda: event['sessionState']['intent']['slots']['Cuisine']['value']['interpretedValue'])
        
    city = check_key_error(lambda: event['sessionState']['intent']['slots']['City']['value']['interpretedValue'])
    
    ParticipantCount = check_key_error(lambda: event['sessionState']['intent']['slots']['People']['value']['interpretedValue'])
    
    date = check_key_error(lambda: event['sessionState']['intent']['slots']['Date']['value']['interpretedValue'])

    time = check_key_error(lambda: event['sessionState']['intent']['slots']['Time']['value']['interpretedValue'])
    
    customerEmail = check_key_error(lambda: event['sessionState']['intent']['slots']['Email']['value']['interpretedValue'])

    # Load confirmation history and track the current reservation.
    load_for_sqs = json.dumps({
        'City': city,
        'Cuisine': cuisine,
        'People': ParticipantCount,
        'Date': date,
        'Time': time,
        'Email': customerEmail
    })
    
    sqs = boto3.client('sqs')
    queue_url = "https://sqs.us-east-1.amazonaws.com/439569526489/messages"
    response = sqs.send_message(
        QueueUrl = queue_url,
        MessageBody = load_for_sqs
        )

# -----------------------Validate Slots Helper Func---------------------------#

#validates the city information
def valid_city(city, resolvedValues):
    cityList = ["manhattan", "queens", "flushing", "nyc"]
    if len(resolvedValues) > 0:
        if city in cityList:
            return True
    return False

#checks the cusine data
def valid_cuisine(cuisine, resolvedValues):
    cuisineList = ["bengali", "indian", "chinese", "thai"]
    if len(resolvedValues) > 0:
        if cuisine.lower() in cuisineList:
            return True
    return False

#check valid count
def valid_participant_count(ParticipantCount):
    try:
        count = int(ParticipantCount)
        if (count > 0 and count < 13):
            return True
        else:
            return False
    except ValueError:
        return False

#checks for the valid date    
def valid_date(date):
    date = dateutil.parser.parse(date)
    if date < dateutil.utils.today():
        return False
    return True

#check for valid time
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

# ----------------------Validate Slots----------------------------------------#

#checks for the key error
def check_key_error(func):
    try:
        return func()
    except TypeError:
        return None


#when valid is not right it asks for the slot value again
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

#validates the slots
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
    print("HELLLOOOO")
    logger.debug(f'line{150}')
    
    if customerEmail:
        logger.debug(f'line{153}')
        if valid_email(slots['Email']['value']['interpretedValue']) == False:
            logger.debug(f'line{155}')
            return ask_for_valid_slot(
                False,
                customerEmail,
                'Invalid email, please try again. (e.g. username@domain.com)'
                )
    
    print("DONE")
    response = {
        'valid': True
    }
                
    return response
    
# ----------------------------Delegate Actions--------------------------------#
def dialogAction_delegate(intent_name, slots):
    response = {
        'sessionState': {
            'dialogAction':{
                'type': 'Delegate',
            },
            'intent':{
                'name': intent_name,
                'slots': slots,
                'state': 'ReadyForfillment'
            }
        }
    }
    
    return response

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
    
def dialogAction_close(intent_name, msg):
    return {
        'messages': [msg],
        'sessionState': {
            'dialogAction': {
                'type': 'Close',
            },
            'intent': {
                'name': intent_name,
                'state': 'Fulfilled'
            }
        }
    }

# ----------------------------------------------------------------------------#
def restuarant_suggestions(intent_request):
    cuisine = check_key_error(lambda: intent_request['sessionState']['intent']['slots']['Cuisine']['value']['interpretedValue'])
        
    city = check_key_error(lambda: intent_request['sessionState']['intent']['slots']['City']['value']['interpretedValue'])
    
    ParticipantCount = check_key_error(lambda: intent_request['sessionState']['intent']['slots']['People']['value']['interpretedValue'])
    
    date = check_key_error(lambda: intent_request['sessionState']['intent']['slots']['Date']['value']['interpretedValue'])

    time = check_key_error(lambda: intent_request['sessionState']['intent']['slots']['Time']['value']['interpretedValue'])
    
    customerEmail = check_key_error(lambda: intent_request['sessionState']['intent']['slots']['Email']['value']['interpretedValue'])

    # Load confirmation history and track the current reservation.
    load_for_sqs = json.dumps({
        'City': city,
        'Cuisine': cuisine,
        'People': ParticipantCount,
        'Date': date,
        'Time': time,
        'Email': customerEmail
    })
    print("EHLOOOO")
    print(customerEmail)
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        
        # Validate any slots which have been specified. If any are invalid, re-elicit for their value
        re_validated_slot = validate_slots(intent_request['sessionState']['intent']['slots'])
        if re_validated_slot['valid'] == False:
            slots = intent_request['sessionState']['intent']['slots']
            
            #updates the slot
            slots[re_validated_slot['slot']] = None
            
            response = dialogAction_elicit_slot(
                intent_request['sessionState']['intent']['name'],
                slots,
                re_validated_slot['slot'],
                re_validated_slot['messages'])
                
            intent_request['messages'] = response['messages']
            intent_request["proposedNextState"]["dialogAction"] = response['sessionState']['dialogAction']
            return response

        
        # if city and cuisine and ParticipantCount and date and time and customerEmail:
        #     print(load_for_sqs)
        #     push_to_sqs(load_for_sqs)
            
        #     return dialogAction_delegate(
        #         intent_request['sessionState']['intent']['name'],
        #         intent_request['sessionState']['intent']['slots'])
                
# ----------------------------------------------------------------------------#
def lambda_handler(event, context):
    
    print(event)
    # Check the Cloudwatch logs to understand data inside event and
    # parse it to handle logic to validate user input and send it to Lex
    # Lex called LF1 with the user message and previous related state so
    # you can verify the user input. Validate and let Lex know what to do next.
    
    resp = {"statusCode": 200, "sessionState": event["sessionState"]}
    # Lex will propose a next state if available but if user input is not valid,
    # you will modify it to tell Lex to ask the same question again (meaning ask
    # the current slot question again)

    #set's EST as default time zone of this program
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    
    if "proposedNextState" not in event:
        resp["sessionState"]["dialogAction"] = {"type": "Close"}
        push_to_sqs(event)
        
    else:
        
        resp["sessionState"]["dialogAction"] = event["proposedNextState"]["dialogAction"]
        restuarant_suggestions(event)
    
    return resp

