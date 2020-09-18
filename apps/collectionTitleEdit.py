import boto3
import json
import os

region = os.getenv('REGION')
collection_table_name = os.getenv('COLLECTIONTABLE_NAME')

try:
    dyndb = boto3.resource('dynamodb', region_name=region)
    collection_table = dyndb.Table(collection_table_name)

    response = collection_table.scan()
    collection_items = response['Items']

    while response.get('LastEvaluatedKey', False):
        response = collection_table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey'])
        collection_items.extend(response['Items'])

except Exception as e:
    print(f"An error occurred: {str(e)}")
    raise e

def item_needs_updating(item):
    ret_val = False
    if(item['collection_category'] == "IAWA" and 'parent_collection' in item ):
        ret_val = True
    return ret_val
    
def get_top_level_parent(parent_id):
    parent = None
    while(parent_id):
        parent = get_item_parent(parent_id)
        if('parent_collection' in parent):
            parent_id = parent['parent_collection'][0]
        else:
            parent_id = False
    return parent            

def get_item_parent(parent_id):
    parent = collection_table.get_item(Key={'id': parent_id})
    return parent['Item']
    
    
def updated_item_title(item):
    item_title_string = ""
    item_title_array = item['title'].split("||")
    title_last = item_title_array[len(item_title_array) - 1]
    title_last_array = title_last.split('_')
    current = title_last_array[ len(title_last_array) - 1 ]
    
    if current.find('Box') > -1:
        item_title_string = current[current.find('Box'):].replace("Box", "Box ").strip()
    elif current.find('Folder') > -1:
        item_title_string = current[current.find('Folder'):].replace("Folder", "Folder ").strip()
                
    return item_title_string
    
def lambda_handler(event, context):
    for item in collection_items:
        try:
            if(item_needs_updating(item)):
                item_title = updated_item_title(item)
                
                collection_table.update_item(
                    Key={
                        'id': item['id'],
                    },
                    UpdateExpression="set title = :val",
                    ExpressionAttributeValues={
                        ':val': item_title
                    },
                    ReturnValues="UPDATED_NEW"
                )

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Process completed.",
        }),
    }
