import boto3
import json
import math
import dateutil.parser
import datetime
import time
import os
import re
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

validationError = None
sqs = boto3.client('sqs')

def send_message(message):
    queue_url = 'https://sqs.us-east-1.amazonaws.com/306885591589/DiningConcierge'
    sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageBody=(json.dumps({'message': message}))
)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
            }
    }
    return response
    
def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }
    
def build_validate_result(isvalid, violated_slot, content):
    if content is None:
        return {
            "isValid" : isvalid,
            "violatedSlot" : violated_slot
        }
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': content}
    }
  
def is_valid_city(city):
    return city.lower() == 'manhattan'

def is_valid_cuisine(cuisine):
    cuisine_list = ['american', 'chinese', 'indian', 'korean', 'thai', 'japanese','vietnamese','turkish','italian']
    return cuisine.lower() in cuisine_list

def is_valid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')
        
def is_valid_people(people):
    if parse_int(people) < 0 or parse_int(people) > 10:
        return False
    return True
    
def is_valid_time(time):
    if re.match('\d{1,2}:\d{1,2}',time):
        hours, minutes = time.split(':')
        hours = parse_int(hours)
        minutes = parse_int(minutes)
        if math.isnan(hours) or math.isnan(minutes):
            return False
        if hours < 0 or hours > 24:
            return False
        if minutes < 0 or minutes > 60:
            return False
        return True
    return False
    

def validate(slots):
    location = slots['location']
    cuisine = slots['cuisine']
    people = slots['people']
    date = slots['date']
    time = slots['time']
    phone = slots['phone']
    
    if location is not None and not is_valid_city(location):
        return build_validate_result(
            False,
            'location',
            'We only support Manhattan area right now, so sorry! Please input the right area again.'
        )
        
    if cuisine is not None and not is_valid_cuisine(cuisine):
        return build_validate_result(
            False,
            'cuisine',
            'We do not support {} as a valid cuisine right now, so sorry! Please input the right type of cuisine again.'.format(cuisine)
        )
        
        
    if people is not None and not is_valid_people(people):
        return build_validate_result(
            False,
            'people',
            'Please input the right number of people!'
        )
        
    
    if date is not None:
        if not is_valid_date(date):
            return build_validate_result(
                False,
                'date',
                'Please input the right date for your order.'
            )
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validate_result(
                False, 
                'date', 
                'You can only book your orders for the future days'
            )
        
    if time is not None and not is_valid_time(time):
        return build_validate_result(
            False,
            'time',
            'Please input the right time for your order.'
        )
    return {'isValid' : True}
def close(sessionAttributes, fulfillment_state, message):
    response = {
        'sessionAttributes': sessionAttributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': {'contentType': 'PlainText',
                  'content': message}
        }
    }

    return response

def diningSuggestionIntent(intent_request):
    logger.debug(get_slots(intent_request))
    cuisine = get_slots(intent_request)['cuisine']
    date = get_slots(intent_request)['date']
    time = get_slots(intent_request)['time']
    numberOfPeople = get_slots(intent_request)['people']
    location = get_slots(intent_request)['location']
    phone_number = get_slots(intent_request)['phone']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    currentIntentName = intent_request['currentIntent']['name']
   
    order = json.dumps({
        'location' : location,
        'cuisine' : cuisine,
        'people' : numberOfPeople,
        'date' : date,
        'time' : time,
        'phone' : phone_number
    })
    
    session_attributes['order'] = order
    if intent_request['invocationSource'] == 'DialogCodeHook':
        slots = get_slots(intent_request)
        validate_result = validate(slots)
        if not validate_result['isValid']:
            slots[validate_result['violatedSlot']] = None
            return elicit_slot(
                            session_attributes, 
                            currentIntentName,
                            slots,
                            validate_result['violatedSlot'],
                            validate_result['message']
            ) 
        else:
            return delegate(session_attributes, intent_request['currentIntent']['slots'])
            
        
    send_message(get_slots(intent_request))

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 'Thank you, I have gathered your information')

def dispatch(intent_request):
    intent_name = intent_request['currentIntent']['name']

    if intent_name == 'GreetingIntent':
        return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 'Hello, I am your dining assistance. How can I help you today?')
        
    elif intent_name == 'ThankYouIntent':
        return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 'You\'re welcome')
        
    elif intent_name == 'DiningSuggestionIntent':
        return diningSuggestionIntent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')

def lambda_handler(event, context):
    logger.debug(event)
    return dispatch(event)