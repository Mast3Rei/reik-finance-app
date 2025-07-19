from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import decimal, base64
from boto3.dynamodb.types import DYNAMODB_CONTEXT

#Abstract Base Model
class BaseModel(models.Model):
    #convert given items into regular fields
    # record_id = models.CharField(max_length=255)
    # amount_date = models.CharField(max_length=255)
    # amount_sum = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(999999)])
    # spend_limit = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(999999)])
    all_data = models.JSONField(default=dict, blank=True)
    class Meta:
        abstract = False

class DynamoDBModel:

    table = settings.DYNAMODB_TABLE

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


    @classmethod
    def putItem(cls, **kwargs):
        try:
            cls.table.put_item(Item=kwargs)
        except Exception as e:
            print(f'PutItem exception: {e}')

    @classmethod
    def updateItem(cls, **kwargs):
        if 'record_id' not in kwargs:
            raise ValueError("Missing 'record_id' in updateItem call")
        
        other_fields = {k: v for k,v in kwargs.items() if k!='record_id'}
        update_expression_parts = []
        attr_names = {}
        attr_values = {}

        # This is the format to create an update expression --> UpdateExpression = 'SET #name = :newName, #age = :newAge'
        # It needs to be built so dynamoDB knows what values to map with the names
        for i, (key, val) in enumerate(other_fields.items()):
            name_placeholder = f'#key{i}'
            value_placeholder = f':val{i}'

            update_expression_parts.append(f"{name_placeholder} = {value_placeholder}")
            attr_names[name_placeholder] = key
            attr_values[value_placeholder] = val
        
        update_expression = "SET " + ", ".join(update_expression_parts)

        # Now the update expression is built and ready to update to dynamoDB
        try:
            response = cls.table.update_item(
                Key={'record_id': kwargs.get('record_id')},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=attr_names,
                ExpressionAttributeValues=attr_values,
                ReturnValues="UPDATED_NEW"
            )
            print("updateItem response:", response['Attributes'])
        except Exception as e:
            print(f'updateItem exception: {e}')


    @classmethod
    def getItem(cls, id):
        response = cls.table.get_item(Key={'record_id':id})
        item = response.get('Item')
        if item:
            return cls(**item)
        return None
    
    @classmethod
    def allItems(cls):
        # DYNAMODB_CONTEXT.traps[decimal.Inexact] = False #
        # DYNAMODB_CONTEXT.traps[decimal.Rounded] = False

        response = cls.table.scan()
        items = response.get('Items', [])
        return [cls(**item) for item in items]
    

    @classmethod
    def encrypt_item(cls, message):
        try:
            response = settings.KMS_CLIENT.encrypt(
                KeyId='alias/reik-key',
                Plaintext=message.encode('utf-8'),
            )
            ciphertext_blob = response['CiphertextBlob']
            encoded = base64.b64encode(ciphertext_blob).decode('utf-8')
            return encoded
        except Exception as e:
            print(f'encryption malfunctioned: {e}')
        

    @classmethod
    def decrypt_item(cls, encrypted_message):
        try:
            decoded = base64.b64decode(encrypted_message.encode('utf-8'))
            response = settings.KMS_CLIENT.decrypt(
                KeyId='alias/reik-key',
                CiphertextBlob=decoded
            )
            decrypted = response['Plaintext'].decode('utf-8')
            print(f'decrypt response: {decrypted}')
            return decrypted
        except Exception as e:
            print(f'decryption malfunctioned: {e}')


class BankAccount(DynamoDBModel): #Inheritance
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.record_id = kwargs.get('record_id')
        # self.amount_date = kwargs.get('amount_date')
        # self.amount_sum = kwargs.get('amount_sum')
        # self.spend_limit = kwargs.get('spend_limit')
        self.all_data = kwargs


#create a proxy class that will work in the middle between the BankAccount Model and the regular models.Model class.
# - this proxy needs a manager class that grabs all the items from BankAccount 
# - and a regular model that creates objects based off the Manager class so that a regular query can be made
# for proxy's: https://docs.djangoproject.com/en/5.0/topics/db/models/
class DynamoDBManager(models.Manager):
    def all(self):
        items = BankAccount.allItems()
        # return [BankAccountProxy(**item.__dict__) for item in items]
        return [BankAccountProxy(all_data=item.all_data) for item in items]
    
class BankAccountProxy(BaseModel):
    objects = DynamoDBManager()
    class Meta:
        proxy = True
        managed = False

    @classmethod
    def allItems(cls):
        return BankAccount.allItems()

