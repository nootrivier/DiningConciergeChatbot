import json
import boto3
import urllib3
import logging
from boto3.dynamodb.conditions import Key, Attr

http = urllib3.PoolManager()

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def get_all_sqs(messages):
    result = []          # analyse query in sqs
    for message in messages:
        body = json.loads(message['Body'])
        item = {}
        main_part = body['message']
        item['cuisine']  = main_part['cuisine']
        item['time']  = main_part['time']
        item['people']  = main_part['people']
        item['location']  = main_part['location']
        item['date'] =main_part['date']
        item['phone_number']  = main_part['phone']
        result.append(item)
    return result

def search_ES(headers,all_queue,esURL,max_recommand_num):
    
    result = []
    for item in all_queue:

        json_data = {
            "size": 3,
            "query": {
            "match": {
                "Restaurant.cuisine":item['cuisine']
                }
            },
            "highlight": {
              "fields": {
              "id": {}
                }
            }
        }
        response = http.request('POST',                          # search in ES
                        esURL,
                        body = json.dumps(json_data),
                        headers=headers,
                        retries = False)
        respon = response.data.decode('utf-8')
        respons = str(respon).replace("\"", '\'')
        resp = json.loads(respon)
        num = min(max_recommand_num, len(resp['hits']['hits']) )
        rests = []
        for i in range( num  ):
            rests.append(resp['hits']['hits'][i]['_source']['Restaurant']['restaurant_id'])         ##  id set 
        result.append(rests)
    return result

def search_dynamo(rests_set,table):
    
    result = []
    for rests in rests_set:

        res_dets=[]
        for r in rests:
            try:
                resp = table.scan(
                    FilterExpression=Key('id').eq(r)      #  get by id in dynamoDb
                )
            except Exception as e:
                print("Error in query"+str(e))
                continue
            rest_js = json.loads(json.dumps(resp['Items']))    #      
            t = {}
            t['name'] = rest_js[0]['name']                        #  
            t["address"] = rest_js[0]['address'].replace("'","")
            res_dets.append(t)
        result.append(res_dets)

    return result

def send_sms(res_dets_set,all_queue):

    for x in range(0,len(res_dets_set)):

    # for res_dets in res_dets_set:
        res_dets = res_dets_set[x]
        queue = all_queue[x]
        # sms = "Hello. Here are my {} restaurant suggestions for {} people , for {} at {}".format(queue[] cuisine,people,date,time) + "\n"  #
        sms = "Hello. Here are my {} restaurant suggestions for {} people , for {} at {}".format(queue['cuisine'], queue['people'], queue['date'], queue['time'] ) + "\n"  #
        i=1
        for entries in res_dets:                      # edit cell phone message
            sms+=str(i)+". "
            sms+= entries["name"]+", located at "

            address = json.loads(entries["address"])['display_address']
            sms+=address[0]+", "+address[1]
            print(address)
            sms+="\n"
            i+=1    

        ph= queue['phone_number'] if '+1' in queue['phone_number'] else "+1"+ queue['phone_number']
        smsClient.publish(PhoneNumber=ph, Message=sms)
        print(sms)
        # smsClient.publish(PhoneNumber=ph, Message=sms)


def lambda_handler(event, context):
    logger.debug(event)
    max_recommand_num = 3
    sqsClient = boto3.client('sqs')
    smsClient = boto3.client('sns')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('yelp-restaurants')
    queueUrl = "https://sqs.us-east-1.amazonaws.com/306885591589/DiningConcierge"
    queue = sqsClient.receive_message(QueueUrl = queueUrl)
    url = "https://search-diningconcierge-rawwf5iwcizbl6vi2li664aagi.us-east-2.es.amazonaws.com/"
    index = "restaurants/"
    headers = { "Content-Type" : "application/json" }
    search = "_search"
    esURL = url + index + search
    try:
        messages = queue['Messages']
    except KeyError:
        return        
    
    if queue['Messages'] is not None: 
        all_queue = get_all_sqs(queue['Messages'])
    print(len(all_queue),'all_queue')
    rests_set = search_ES(headers,all_queue,esURL,max_recommand_num)

    print(len(rests_set ),'rests_set')

    print(rests_set)

    res_dets_set = search_dynamo(rests_set,table)

    print(len(res_dets_set),'res_dets_set')

    send_sms(res_dets_set,all_queue)    