import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import os

# Environment variables
region_name = os.getenv('REGION')
collection_table_name = os.getenv('COLLECTIONTABLE_NAME')
collectionmap_table_name = os.getenv('COLLECTIONMAPTABLE_NAME')
archive_table_name = os.getenv('ARCHIVETABLE_NAME')


try:
    dyndb = boto3.resource('dynamodb', region_name=region_name)
    archive_table = dyndb.Table(archive_table_name)
    collection_table = dyndb.Table(collection_table_name)
    collectionmap_table = dyndb.Table(collectionmap_table_name)
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
    raise e
    
            
            
def fetch_records(table):
    scan_kwargs = {
        'FilterExpression': Attr('id').exists(),
        'ProjectionExpression': "#id, create_date, modified_date",
        'ExpressionAttributeNames': {"#id": "id"}
    }
    source_table_items = []
    try:
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            source_table_items.extend(response['Items'])
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e
    return source_table_items
    

def lambda_handler(event, context):
    
    for collectionmap in fetch_records(collectionmap_table):
        collectionmap_table.update_item(
            Key = {
                "id": collectionmap["id"]
            },
            AttributeUpdates = {
                "create_date": {
                    "Value": "2020/04/23 22:46:04",
                    "Action": "PUT"
                },
                "modified_date": {
                    "Value": "2020/04/23 22:46:04",
                    "Action": "PUT"
                },
                "createdAt": {
                    "Value": "2020-04-23T22:46:04.000Z",
                    "Action": "PUT"
                },
                "updatedAt": {
                    "Value": "2020-04-23T22:46:04.000Z",
                    "Action": "PUT"
                }
            }
        )

    for collection in fetch_records(collection_table):
        collection_table.update_item(
            Key = {
                "id": collection["id"]
            },
            AttributeUpdates = {
                "createdAt": {
                    "Value": collection["create_date"].replace("/", "-").replace(" ", "T") + ".000Z",
                    "Action": "PUT"
                },
                "updatedAt": {
                    "Value": collection["modified_date"].replace("/", "-").replace(" ", "T") + ".000Z",
                    "Action": "PUT"
                }
            }
        )

    for archive in fetch_records(archive_table):
        archive_table.update_item(
            Key = {
                "id": archive["id"]
            },
            AttributeUpdates = {
                "createdAt": {
                    "Value": archive["create_date"].replace("/", "-").replace(" ", "T") + ".000Z",
                    "Action": "PUT"
                },
                "updatedAt": {
                    "Value": archive["modified_date"].replace("/", "-").replace(" ", "T") + ".000Z",
                    "Action": "PUT"
                }
            }    
        )


    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Process completed.",
        }),
    }

