from rest_framework import serializers
from .models import BankAccountProxy


#This will turn our fields into a json output to serve to the Svelte application
class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountProxy
        fields = '__all__'