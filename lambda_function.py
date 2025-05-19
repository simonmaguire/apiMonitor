import json
import boto3
import requests

def getApis(client):
    table_name = "apis-to-monitor"
    table = client.Table(table_name)
    
    tblResponse = table.scan()
    result = {}
    if "Items" in tblResponse:
            for item in tblResponse['Items']:
                 result[item['api_id']] = item

    return result


def callAllApis(apis):
    allPermitDates = {}

    headers ={'authority': 'www.recreation.gov',
                  'content-type': 'application/json; charset=utf-8',
                  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
                  }
    try:
        for id in apis.keys():
            url = apis[id]['url']
            response = requests.get(
                url,
                headers=headers)
            x = response.json()['payload']['date_availability']

            availableDates = []
            for day in x.keys():
                if(x[day]['remaining'] == 0): continue
                availableDates.append(day)
            allPermitDates[id] = availableDates

    except:
         print('callAllApis Exception')
    return allPermitDates

def checkForNew(curr, prev):
    if(len(curr) == 0):
        return False
    for day in curr:
        if day not in prev:
            return True
    return False

def lambda_handler(event, context):
    try:
        session = boto3.Session()
        client = session.resource("dynamodb", region_name='us-east-2')
        
        apis = getApis(client)
        currentDates = callAllApis(apis)

        hasNewDates = False
        for date in currentDates.keys():
             hasNewDates = hasNewDates or checkForNew(currentDates[date], apis[date]['available_days'])

        print(hasNewDates)

    except Exception as e:
        print('exception')
        print(e)

    return {
        'statusCode': 200
    }

print('Running test func')
lambda_handler({}, {})