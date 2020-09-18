import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import os

# Environment variables
region_name = os.getenv('REGION')
collection_table_name = os.getenv('COLLECTIONTABLE_NAME')
collectionmap_table_name = os.getenv('COLLECTIONMAPTABLE_NAME')
bucket_name = os.getenv("COLLECTIONMAP_BUCKETNAME")


try:
    dyndb = boto3.resource('dynamodb', region_name=region_name)
    collection_table = dyndb.Table(collection_table_name)
    collectionmap_table = dyndb.Table(collectionmap_table_name)
    
    s3 = boto3.client('s3')
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
    raise e
    
    
def set_deepest(event, level):
    if(level > event["deepest"]):
        event["deepest"] = level
    
    
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
    
    
def walk_collection(collection, map_location, event, level):
    set_deepest(event, level)
    children = get_collection_children(collection['id'])
    if(len(children) > 0):
        map_location['children'] = []
        child_id = 0
        for child in children:
            custom_key = child["custom_key"].replace("ark:/53696/", "")
            map_location["children"].append({"id": child["id"], "name": child["title"], "custom_key": custom_key })
            walk_collection(child, map_location['children'][child_id], event,  level + 1)
            child_id += 1
            
            
def get_top_level_collections():
    scan_kwargs = {
        'FilterExpression': Attr('parent_collection').not_exists(),
        'ProjectionExpression': "#id, title, custom_key",
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
    
    
def get_collection_children(parent_id):
    scan_kwargs = {
        'FilterExpression': Attr('parent_collection').contains(parent_id),
        'ProjectionExpression': "#id, title, custom_key",
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
    
    all_top_level = get_top_level_collections()
    map_id = 1
    
    for parent in all_top_level:
        level = 1
        collection_obj = {}
        event["deepest"] = 1
        custom_key = parent["custom_key"].replace("ark:/53696/", "")
        
        collection_obj[parent["id"]] = {"id": parent["id"], "name": parent["title"], "custom_key": custom_key}
    
        walk_collection(parent, collection_obj[parent["id"]], event, level)
        
        s3_response = s3.put_object(
            Bucket=bucket_name,
            Key=('collections/' + parent['id'] + '.json'),
            Body=json.dumps(collection_obj[parent["id"]])
        )
        
        collectionmap_table.put_item(
            Item = {
                "id": str(map_id),
                "map_object": json.dumps(collection_obj[parent["id"]]),
                "collection_id": parent["id"]
            }    
        )
        
        collection_table.update_item(
            Key = {
                "id": parent["id"]    
            },
            AttributeUpdates = {
                "collectionmap_id": {
                    "Value": str(map_id),
                    "Action": "PUT"
                }
            }    
        )
        
        
        map_id += 1
         
        print(parent["id"] + " level: " + str(event["deepest"]))
                

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Process completed.",
        }),
    }
