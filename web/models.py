from django.db import models
from company.models import Company
from django.contrib import admin
from mongoengine import *
import datetime
from mongoengine.queryset import QuerySet
import pickle

# Create your models here.
class AlexaData(models.Model):
    company = models.ForeignKey( Company )
    date = models.DateField( blank=True , null=True)
    pv_perMillion = models.FloatField()
    pv_perUser = models.FloatField()
    rank = models.FloatField()
    reach = models.FloatField()

    def __unicode__(self):
        return str(self.company.name) +' '+ str(self.date)

admin.site.register(AlexaData)


class WebTraffic(Document):
    company_id = IntField(required=True,unique=True)
    traffic = SortedListField(DictField(),ordering='date')

    @queryset_manager
    def get_reach(doc_cls,queryset,company_id):
        data_set = queryset.get(company_id=company_id).traffic
        reach_list = []
        for item in data_set:
            reachArray = pickle.loads(str(item['data']))
            reach_list.append({'date':item['date'],'reach':reachArray[0]})
        return reach_list

    @queryset_manager    
    def get_reach_list(doc_cls,queryset,company_id):
        data_set = queryset.get(company_id=company_id).traffic
        reach_list = [ pickle.loads(str(item['data']))[0] for item in data_set]
        return reach_list

    meta = {
        'indexes': ['company_id']
    }



