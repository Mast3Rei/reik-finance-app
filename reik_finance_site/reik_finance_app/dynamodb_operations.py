from django.conf import settings
from boto3.dynamodb.conditions import Key


table = settings.DYNAMODB_TABLE

def dynamodb_get_item():
    response = table.get_item(Key={'user_id': 'jake123'})
    return response.get('Item')