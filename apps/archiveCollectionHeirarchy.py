import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import os

# Environment variables
region_name = os.getenv('REGION')
collection_table_name = os.getenv('COLLECTIONTABLE_NAME')
archive_table_name = os.getenv('ARCHIVETABLE_NAME')


try:
    dyndb = boto3.resource('dynamodb', region_name=region_name)
    archive_table = dyndb.Table(archive_table_name)
    collection_table = dyndb.Table(collection_table_name)
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
    raise e
    
def get_collection(collection_id):
    ret_val = None
    try:
        response = collection_table.query(
            KeyConditionExpression=Key('id').eq(collection_id),
            Limit=1
        )
        
        ret_val = response['Items'][0]
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e
    return ret_val
    
def fetch_heirarchy_list(parent_collection):
    collection = get_collection(parent_collection)
    return collection["heirarchy_path"]
            
            
def fetch_archives():
    scan_kwargs = {
        'FilterExpression': Attr('id').exists(),
        'ProjectionExpression': "#id, parent_collection",
        'ExpressionAttributeNames': {"#id": "id"}
    }
    source_table_items = []
    try:
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = archive_table.scan(**scan_kwargs)
            source_table_items.extend(response['Items'])
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e
    return source_table_items
    

def lambda_handler(event, context):
    collection_cache = {}
    for archive in fetch_archives():
        print(archive)
        if "parent_collection" in archive:
            if archive["parent_collection"][0] in collection_cache:
                heirarchy = collection_cache[archive["parent_collection"][0]]
            else:
                heirarchy = fetch_heirarchy_list(archive["parent_collection"][0])
                collection_cache[archive["parent_collection"][0]] = heirarchy
        print(heirarchy)
        print("-------------------------------------------------------------")
        archive_table.update_item(
            Key = {
                "id": archive["id"]    
            },
            AttributeUpdates = {
                "heirarchy_path": {
                    "Value": heirarchy,
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

