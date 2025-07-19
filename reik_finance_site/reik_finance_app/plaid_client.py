from plaid.api import plaid_api
import plaid
from django.conf import settings

configuration = plaid.Configuration(
    host=plaid.Environment.Production, #sandbox - production mode
    api_key={
        'clientId': settings.PLAID_CLIENT_ID,
        'secret': settings.PLAID_SECRET,
        'environment': settings.PLAID_ENV
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)