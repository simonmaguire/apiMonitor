import json
import boto3
import requests
import datetime
import os

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

    headers ={'authority': os.getenv('API-AUTHORITY'),
                  'content-type': 'application/json; charset=utf-8',
                  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
                  }
    try:
        issueAPIs = []
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
            if(len(availableDates) > 3):
                for day in availableDates:
                    if(x[day]['remaining'] == x[day]['total']):
                        issueAPIs.append({'id': id, 'res' : x})
                        break

    except:
         print('callAllApis Exception')
    return allPermitDates, issueAPIs

def checkForNew(curr, prev):
    if(len(curr) == 0):
        return False
    for day in curr:
        if day not in prev:
            return True
    return False

def composeEmail(storedApiInfo, currentDates, issues):
    built_text = 'Avalable Dates \n\n'
    unavailable = []
    for api_id in storedApiInfo.keys():
        if(len(currentDates[api_id]) == 0):
            unavailable.append(api_id)
            continue
        built_text += f"{storedApiInfo[api_id]['name']}\n"
        built_text += f"{storedApiInfo[api_id]['signup_url']}\n"
        for date in currentDates[api_id]:
            built_text += f"{date.split('T')[0]}, "
        built_text += "\n\n"
    for api_id in unavailable:
        built_text += f"{storedApiInfo[api_id]['name']} is unavailable\n\n"
    for issue in issues:
        built_text += f"{storedApiInfo[issue['id']]['name']} has some issues with checking availability\n"
        built_text += f"{issue['res']}\n"
    return built_text

def sendEmail(built_text, recipients): 
    print('sending email')
    to = ''
    for recipient in recipients:
        to += f"{recipient['first_name']} <{recipient['email']}>, "
    today = datetime.date.today()
    res = requests.post(
        "https://api.mailgun.net/v3/simonmaguire.com/messages",
        auth=("api", os.getenv('MAILGUN_API_KEY')),
        data={"from": "API Monitor <postmaster@simonmaguire.com>",
        "to": to,
        "subject": f"Available Permits {today}",
        "text": built_text}
        )
    print(res.reason)

def hasUnsentDays(curr, sent):
    for day in curr:
        if day not in sent:
            return True
    return False

def lambda_handler(event, context):
    try:
        session = boto3.Session()
        client = session.resource("dynamodb", region_name='us-east-2')
        
        apis = getApis(client)
        currentDates, issues = callAllApis(apis)
        hasIssues = len(issues) > 0
        if(hasIssues):
            return{'statusCode': 200}

        table_name = "apis-to-monitor"      
        table = client.Table(table_name)
        hasNewDates = False
        for permit in currentDates.keys():
            hasNewDates = hasNewDates or checkForNew(currentDates[permit], apis[permit]['available_days'])
            hasNewDates = hasNewDates and hasUnsentDays(currentDates[permit], apis[permit]['sent_today'])

            response = table.update_item(
                Key={"api_id": permit},
                UpdateExpression="set #available_days = :l",
                ExpressionAttributeNames={
                    "#available_days": "available_days",
                },
                ExpressionAttributeValues={
                    ":l": currentDates[permit],
                },
                ReturnValues="UPDATED_NEW",
            )
        
        print(hasNewDates)
        if(hasNewDates):
            people_table_name = "permit-people"
            people_table = client.Table(people_table_name)
            people_response = people_table.scan()
            recipients = []
            for person in people_response['Items']:
                if('tester' not in person.keys()): continue
                recipients.append({'email' : person['email'], 'first_name': person['first_name']})
            
            sendEmail(composeEmail(apis, currentDates, issues), recipients)

            for permit in currentDates.keys():
                if(currentDates[permit] == []):
                    continue
                response = table.update_item(
                    Key={"api_id": permit},
                    UpdateExpression="add #sent_today :l",
                    ExpressionAttributeNames={
                        "#sent_today": "sent_today",
                    },
                    ExpressionAttributeValues={
                        ":l": set(currentDates[permit]),
                    },
                    ReturnValues="UPDATED_NEW",
                )


    except Exception as e:
        print('exception')
        print(e)

    return {
        'statusCode': 200
    }

print('Running test func')
lambda_handler({}, {})