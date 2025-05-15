import json
import boto3

def getApis(client):
    table_name = "apis-to-monitor"
    table = client.Table(table_name)
    
    tblResponse = table.scan()
    result = {}
    if "Items" in tblResponse:
            for item in tblResponse['Items']:
                 result[item['api_id']] = item

    return result


def lambda_handler(event, context):
    try:
        session = boto3.Session()
        client = session.resource("dynamodb", region_name='us-east-2')
        
        apis = getApis(client)
        print(apis)


    except Exception as e:
        print('exception')
        print(e)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from!')
    }

print('Running test func')
lambda_handler({}, {})