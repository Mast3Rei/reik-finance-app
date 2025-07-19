from typing import Any
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import plaid.model
import plaid.model.link_token_create_request
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
import json
import datetime
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from django.views.generic import ListView
from .plaid_client import client
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from .models import BankAccount, BankAccountProxy
from .serializers import BankAccountSerializer

# Inspiration: https://www.reddit.com/r/dataisbeautiful/comments/e35yr7/oc_my_personal_finance_dashboard_database_using/
# https://www.thenahum.com/nfi/demo/



# ------------------------------
# Instead of this we will use dynamic routing
# 
# def sports_view(request):
#     return HttpResponse(articles['sports'])
# def finance_view(request):
#     return HttpResponse(articles['finance'])

# articles = {
#     'sports':'Sports Page',
#     'finance':'Finance Page',
#     'politics':'Politics Page'
# }

# def page_views(request, topic):
#     return HttpResponse(articles[topic])

# ---------------------------------

# def example_view(request):
#         # reik_finance_app/templates/reik_finance_app/example.html
#     return render(request, 'reik_finance_app/example.html')

# def variable_view(request):
#     #we can send a variable over to the render by adding a third arg 'context=my_var'
#     my_var = dynamodb_get_item()
#     _data_dict = dynamodb_json.loads(my_var)
#     return HttpResponse(_data_dict.values())
#     #render(request, 'reik_finance_app/variable.html',context=my_var)


# ---------PLAID---------------------------------------------------------------------------------------------------------------------
@csrf_exempt
def create_link_token(request):
    decode_body = request.body.decode('utf-8')
    user = json.loads(decode_body)['user_id']
    link_request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=str(user)),
        client_name='Reik Finance App',
        products=[Products('transactions')],
        country_codes=[CountryCode('US')],
        language='en'
    )

    link_response = client.link_token_create(link_request)
    return JsonResponse(link_response.to_dict(), status=201)




# @csrf_exempt
# # @require_POST
# def exchange_token(request):
#     decode_body = request.body.decode('utf-8')
#     pub_tok= json.loads(decode_body)['public_token'] #grabs the public token directly
#     print("public token:", pub_tok)
#     request = ItemPublicTokenExchangeRequest(
#         public_token=pub_tok
#     )
#     response = client.item_public_token_exchange(request)


#     access_token = response['access_token']

#     upload_access_token({'bank_access':response['access_token'], 'credit_access':'abcdefg654321'})
#     item_id = response['item_id']

#     try:
#         a_tokens = get_access_token()
#         print("DynamoDB access tokens:", a_tokens)
#     except Exception as e:
#         print("DynamoDB access token retrieval fail:", e)
#     # return JsonResponse({"message":"exchange token working!", "access_token": access_token, "item_id": item_id})

@csrf_exempt
# @require_POST
def exchange_token(pub_tok):
    print("public token:", pub_tok)
    request = ItemPublicTokenExchangeRequest(
        public_token=pub_tok
    )
    response = client.item_public_token_exchange(request)
    access_token = response['access_token']
    return access_token



# @csrf_exempt
# def upload_fake_access_token(request):
#     try:
#         fake_tok = 'access-sandbox-123-fake-token'
#         id = '2' #access tokens are stored at this id
#         data = {'record_id':id}
#         data.update({"credit_access":encrypt_access_token(fake_tok)}) #, "bank_access":encrypt_access_token(fake_tok)
#         BankAccount().updateItem(**data)
#         return JsonResponse({'status': 200})
#     except Exception as e:
#         print(f'inject fake tok fail: {e}')


def encrypt_token(token):
    print(f'encrypt this token: {token}')
    encrypted_token = BankAccount().encrypt_item(token)
    return encrypted_token

def decrypt_token(enc_token):
    decrypted_token = BankAccount().decrypt_item(enc_token)
    # print(f'Decrypted access token final: {decrypted_token}')
    return decrypted_token

def upload_access_token(access_token_data): 
    new_account = BankAccount()
    id = '2' #access tokens are stored at this id
    data = {'record_id':id}

    print('upload_access_token data:', access_token_data)
    encrypted_tok = encrypt_token(list(access_token_data.values())[0]) #encrypt access tokens with AWS KMS
    print(f"Upload encrypted access token: {encrypted_tok}")
    data.update({list(access_token_data.keys())[0] : encrypted_tok})
    new_account.updateItem(**data)
    return None


@csrf_exempt
def exchange_bank_access(request):
    decode_body = request.body.decode('utf-8')
    pub_tok= json.loads(decode_body)['public_token']
    access_tok = exchange_token(pub_tok)
    upload_access_token({"bank_access": access_tok})
    return HttpResponse("Exchange successful and bank access token stored!")

@csrf_exempt
def exchange_credit_access(request):
    decode_body = request.body.decode('utf-8')
    pub_tok= json.loads(decode_body)['public_token']
    access_tok = exchange_token(pub_tok)
    upload_access_token({"credit_access": access_tok})
    return HttpResponse("Exchange successful and credit access token stored!")


@csrf_exempt
def get_bank_account(request):
    bank_access_token = get_bank_access() #get the access tokens from secure storage
    try:
        bank_account_request = AccountsGetRequest(
            access_token=bank_access_token
        )
        bank_account_response = client.accounts_get(bank_account_request)
        print("My bank info response:", bank_account_response)
        return JsonResponse(bank_account_response.to_dict())
    
    # except Exception as e:
    #     print(f"get_bank_account exception: {e}")
    except Exception as e:
        error_body = json.loads(e.body) if hasattr(e, 'body') else {}
        error_code = error_body.get('error_code', 'UNKNOWN_ERROR')
        print(f'get_bank_account error: {error_code}')
        return JsonResponse({"error_code": error_code}, status=400)

@csrf_exempt
def get_credit_account(request):
    credit_access_token = get_credit_access() #get the access tokens from secure storage
    try:
        credit_account_request = AccountsGetRequest(
            access_token=credit_access_token
        )
        credit_account_response = client.accounts_get(credit_account_request)
        print("My credit card info response:", credit_account_response)
        return JsonResponse(credit_account_response.to_dict())
    except Exception as e:
        error_body = json.loads(e.body) if hasattr(e, 'body') else {}
        error_code = error_body.get('error_code', 'UNKNOWN_ERROR')
        print(f'get_credit_account error: {error_code}')
        return JsonResponse({"error_code": error_code}, status=400)


def get_bank_access():
    id = '2' #access tokens are stored at this id
    new_account = BankAccount()
    bank_account_item = new_account.getItem(id).__dict__
    access_token = decrypt_token(bank_account_item['bank_access'])
    return access_token

def get_credit_access():
    id = '2' #access tokens are stored at this id
    new_account = BankAccount()
    bank_account_item = new_account.getItem(id).__dict__
    access_token = decrypt_token(bank_account_item['credit_access'])
    return access_token


@csrf_exempt
def get_transactions_curr_month(request):
    # decode_request = request.body.decode('utf-8')
    
    access_token = get_credit_access() #either bank_access or credit_access

    print('Trans access token and og_access_token:', access_token)
    start = [int(i) for i in datetime.datetime.now().strftime("%Y-%m-%d").split('-')]
    start[2] = 1
    end = [int(i) for i in datetime.datetime.now().strftime("%Y-%m-%d").split('-')]

    try:
        new_request = TransactionsGetRequest(
            access_token=access_token,
            start_date=datetime.date(start[0],start[1],start[2]),
            end_date=datetime.date(end[0],end[1],end[2])
        )
        response = client.transactions_get(new_request)

        # print('get_trans_curr_month response trans:', response['transactions'])
        result = [item.to_dict() for item in response['transactions'] if (float(item['amount']) > float(0))]
        return JsonResponse({'transactions': result})
    except Exception as e:
        error_body = json.loads(e.body) if hasattr(e, 'body') else {}
        error_code = error_body.get('error_code', 'UNKNOWN_ERROR')
        print(f'get_transactions_curr_month error: {error_code}')
        return JsonResponse({"error_code": error_code}, status=400)
    

@csrf_exempt
def get_transactions_prev_month(request):
    access_token = get_credit_access() #either bank_access or credit_access

    start = [int(i) for i in datetime.datetime.now().strftime("%Y-%m-%d").split('-')]
    start[2] = 1
    if start[1] == 1:
        start[0]-=1 #reduces the year before setting the correct month
    start[1] = start[1]-1 if start[1]>1 else 12 #sets the correct month
    end_last_month = datetime.datetime.today().replace(day=1) - relativedelta(days=1) #takes todays date, sets it to day 1, and 
                                                                                    # subtracts a day relative to the given month
    end = [int(i) for i in end_last_month.strftime('%Y-%m-%d').split('-')]

    try:
        new_request = TransactionsGetRequest(
            access_token=access_token,
            start_date=datetime.date(start[0],start[1],start[2]),
            end_date=datetime.date(end[0],end[1],end[2])
        )
        response = client.transactions_get(new_request)

        # print('get_trans_curr_month response trans:', response['transactions'])
        result = [item.to_dict() for item in response['transactions'] if (float(item['amount']) > float(0))]
        return JsonResponse({'transactions': result})
    except Exception as e:
        error_body = json.loads(e.body) if hasattr(e, 'body') else {}
        error_code = error_body.get('error_code', 'UNKNOWN_ERROR')
        print(f'get_transactions_prev_month error: {error_code}')
        return JsonResponse({"error_code": error_code}, status=400)

@csrf_exempt
def group_transactions(request):
    decode_request = request.body.decode('utf-8')
    transaction_data = json.loads(decode_request)

    amounts = [float(tran['amount']) for tran in transaction_data['transactions']]
    total_amount = sum(amounts)
    return JsonResponse({'amount': total_amount})

@csrf_exempt
def get_transaction_categories(request):
    decode_request = request.body.decode('utf-8')
    transaction_data = json.loads(decode_request)
    # take in transaction data and get all the unique categories in a separate array

    # loop through these unique categories and get a count of the matches inside the transaction data
    categories = set([cat['category'] for cat in transaction_data])

    print("Categories existing: ", categories)

    count_categories = []
    for category in categories:
        # cat_count = transaction_data.filter(lambda i : i['category']==category, transaction_data).count()
        cat_filtered = list(filter(lambda i : i['category']==category, transaction_data))
        cat_count = len(cat_filtered)
        cat_tran_total = Decimal(str(round(sum([c['amount'] for c in cat_filtered]), 2)))
        #get the count and update the count_categories

        count_categories.append({'tran_category':category, 'tran_count':cat_count, 'tran_total':cat_tran_total, 
                                 'tran_spt':Decimal(str(round((cat_tran_total/cat_count), 2)))})
    print("Categories count: ", count_categories)

    # Sort to get the top 3 categories at the front of the array
    count_categories = sorted(count_categories, key=lambda x: float(x['tran_total']), reverse=True)

    print('Categories count Sorted list:', count_categories)

    return JsonResponse({'categories':count_categories[0:3]})




# ---------------------------------------------------------------------------------------------------------------------------------------------------


from decimal import Decimal
@csrf_exempt
def BankAccountPutItem(request):
    new_account = BankAccount()
    decode_request = request.body.decode('utf-8')
    data = json.loads(decode_request)['record']
    print("BankAccount put item request:", data)

    TWO_PLACES = Decimal("0.01") #rounds decimal to two places using quantize
    data = {k: Decimal(str(v)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP) if type(v)==float else v for k,v in data.items()} #change any floats to decimal so they can enter DynamoDB

    new_account.putItem(**data)

    return HttpResponse("Item successfully added!")

@csrf_exempt
def BankAccountItem(request): #USE THIS ----------------------------------
    new_account = BankAccount()
    decode_request = request.body.decode('utf-8')
    id = json.loads(decode_request)['record_id']
    bank_account_item = new_account.getItem(id).__dict__
    # print('Bank account get item:', bank_account.__dict__)
    return JsonResponse(bank_account_item)

@csrf_exempt
def BankAccountUpdateItem(request):
    new_account = BankAccount()
    decode_request = request.body.decode('utf-8')
    data = json.loads(decode_request)['record']

    TWO_PLACES = Decimal("0.01") #rounds decimal to two places using quantize
    data = {k: Decimal(str(v)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP) if type(v)==float else v for k,v in data.items()} #change any floats to decimal so they can enter DynamoDB

    new_account.updateItem(**data)
    return HttpResponse("Item successfully updated!")


# @csrf_exempt
# def upload_fake_access_token(request):
#     try:
#         fake_tok = 'access-sandbox-123-fake-token'
#         id = '2' #access tokens are stored at this id
#         data = {'record_id':id}
#         data.update({"credit_access":encrypt_access_token(fake_tok)}) #, "bank_access":encrypt_access_token(fake_tok)
#         BankAccount().updateItem(**data)
#         return JsonResponse({'status': 200})
#     except Exception as e:
#         print(f'inject fake tok fail: {e}')

def BankAccountAll(request): #THIS WORKS ------------------------------------------------------------------------------
    new_account = BankAccount()
    items = new_account.allItems()
    return HttpResponse(str(items))

class BankAccountListView(ListView): 
    #model_list.html
    model = BankAccount
    template_name = 'reik_finance_app/bankaccount_list.html'
    context_object_name = 'bankaccounts'

    def get_queryset(self):
        return self.model.allItems()
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = self.get_queryset()
        return context
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object_list = self.get_queryset() #Manually 
        context = self.get_context_data(object_list=self.object_list)
        return render(request, self.template_name, context)


# def bank_account_list(request):
#     account_list = BankAccount.objects.all()
#     context_list = {'bank_accounts':account_list}
#     return render(request,'bankaccount/index.html',context=context_list)

class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccountProxy.objects.all()
    serializer_class = BankAccountSerializer

    def list(self, request):
        queryset = BankAccountProxy.objects.all()
        serializer = BankAccountSerializer(queryset, many=True)
        return Response(serializer.data)
    

#Used to trigger the Lambda function to update the dynamoDB database so contents can be fetched
class LambdaInvokeView(APIView):
    def get(self, request):
        url = "https://4molyb3cc5.execute-api.us-east-1.amazonaws.com/dev/bankaccount"
        header = {'Content-Type': 'application/json'} # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type
        response = requests.get(url, headers=header)
        # return Response(response.json(), status=response.status_code)
        return HttpResponse(response) #I could do a Response(response.json(), status_code=response.status) and then send it to a writable
                                        #store in Svelte. Then I can use that to serve the response message on a page and add styling to it

#For now we use --> /reik_finance_app/bankaccount/ --- and ---> /reik_finance_app/bankaccountupdate/