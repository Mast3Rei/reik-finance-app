from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # . for current directory
from .views import BankAccountViewSet, LambdaInvokeView, BankAccountListView, create_link_token

# register the app namespace
app_name = 'reik_finance_app'

router = DefaultRouter()
router.register(r'bankaccount',BankAccountViewSet, basename='bankaccount')

#always called urlpatterns
urlpatterns = [
    #empty string because we are going to define the path in the 'site' urls.py;
    #all of these paths will start with reik_finance_app/
    # path('<str:topic>/', views.page_views) # < > allows for the dynamic variable for the url path; 'str:' specifies it will be a string
    # path('', views.example_view,name='example'),
    # path('variable/', views.variable_view,name='variable'),
    path('bankaccountgetitem', views.BankAccountItem, name='bankaccountgetitem'),
    path('bankaccountputitem', views.BankAccountPutItem, name='bankaccountputitem'),
    path('bankaccountupdateitem', views.BankAccountUpdateItem, name='bankaccountupdateitem'),
    path('bankaccountitems',views.BankAccountAll, name='bankaccountitems'),
    path('bankaccountall', BankAccountListView.as_view(), name='bankaccountall'),
    path('', include(router.urls)),
    path('bankaccountupdate/', LambdaInvokeView.as_view(), name='bankaccountupdate'), #update the bank account information
    path('create-link-token', views.create_link_token, name='create-link-token'),
    path('exchange-public-token-bank', views.exchange_bank_access, name='exchange-public-token-bank'),
    path('exchange-public-token-credit', views.exchange_credit_access, name='exchange-public-token-credit'),
    path('get-bank-account', views.get_bank_account, name='get-bank-account'),
    path('get-credit-account', views.get_credit_account, name='get-credit-account'),
    path('get-transactions-curr-month', views.get_transactions_curr_month, name='get-transactions-curr-month'),
    path('get-transactions-prev-month',views.get_transactions_prev_month, name='get-transactions-prev-month'),
    path('group-transactions', views.group_transactions, name='group-transactions'),
    path('get-transaction-categories', views.get_transaction_categories, name='get-transaction-categories'),
]
