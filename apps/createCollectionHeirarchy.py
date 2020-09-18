import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import os

# Environment variables
region_name = os.getenv('REGION')
collection_table_name = os.getenv('COLLECTIONTABLE_NAME')


try:
    dyndb = boto3.resource('dynamodb', region_name=region_name)
    collection_table = dyndb.Table(collection_table_name)
    
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
    raise e
    
    
def build_heirarchy_list(collection):
    heirarchy_list = []
    heirarchy_list.insert(0, collection["id"])
    
    parent_id = None
    if "parent_collection" in collection:
        parent_id = collection["parent_collection"][0]
    
    while parent_id is not None:
        parent = get_collection(parent_id)
        if parent is not None:
            parent = parent[0]
            heirarchy_list.insert(0, parent["id"])
            if "parent_collection" in parent:
                parent_id = parent["parent_collection"][0]
            else:
                parent_id = None
            
    return heirarchy_list
    
    
def get_collection(collection_id):
    ret_val = None
    try:
        response = collection_table.query(
            KeyConditionExpression=Key('id').eq(collection_id),
            Limit=1
        )
        
        ret_val = response['Items']
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e
    return ret_val
            
            
def get_collections():
    scan_kwargs = {
        'FilterExpression': Attr('id').exists(),
        'ProjectionExpression': "#id, title, parent_collection",
        'ExpressionAttributeNames': {"#id": "id"}
    }
    source_table_items = []
    try:
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = collection_table.scan(**scan_kwargs)
            source_table_items.extend(response['Items'])
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e
    return source_table_items
    

def lambda_handler(event, context):
    for collection in get_collections():
        heirarchy = build_heirarchy_list(collection)
        
        collection_table.update_item(
            Key = {
                "id": collection["id"]    
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
