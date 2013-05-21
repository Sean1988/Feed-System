from django.db import models
from company.models import Company
from django.contrib import admin
from mongoengine import *
from mongoengine.queryset import QuerySet
import pickle  


class IosApp(models.Model):
    company = models.ForeignKey( Company,default=None, blank = True, null = True )
    trackId = models.IntegerField( default = 0 )
    trackName = models.CharField( max_length=200 )
    bundleId = models.CharField( max_length=200 )
    artistId = models.IntegerField( default = 0 )
    artistName = models.CharField( max_length=200 )
    artistUrl = models.CharField( max_length=200 )
    primaryGenreId = models.IntegerField( default = 0 )
    primaryGenreName = models.CharField( max_length=100 )
    appAnnieLink = models.CharField( max_length=200 ) #link combined with trackId app/ios/310633997/
    artistLink = models.CharField( max_length=200 )
    country = models.CharField( max_length=50 )
    avgRating = models.FloatField(default=0)
    ratingCount = models.IntegerField( default = 0 )
    icon = models.URLField()
    link = models.URLField()


    minDate = models.CharField( max_length=50 )
    isGame = models.BooleanField(default=False)


    
    analysed =  models.BooleanField(default=False)
    fetched =  models.BooleanField(default=False)

    def __unicode__(self):
        return str(self.bundleId)


class AppCategory(models.Model):
    label = models.CharField( max_length=100 )
    
    def __unicode__(self):
        return str(self.label)

class IosAppRank(models.Model):
    app = models.ForeignKey( IosApp ,blank=True , null=True )
    label = models.ForeignKey( AppCategory ) # category
    date = models.DateField( blank=True , null=True)
    rank = models.IntegerField( default = 0 )
    type =  models.CharField( max_length=100 ) # iphone or ipad
    board = models.CharField( max_length=50 ) # paid free grossing
    country = models.CharField( max_length=100 )
    note =  models.CharField( max_length=200,blank=True , null=True )

    def __unicode__(self):
        try:
            return str(self.app.trackName)
        except:
            return "app" 

admin.site.register(IosAppRank)          
admin.site.register(AppCategory)   
admin.site.register(IosApp)


APP_BOARD = ('paid','free','grossing')
APP_TYPE = ('iphone','ipad')
class MobileRank(Document):
    app_id = IntField(required=True,unique=True)
    category = StringField( max_length=100)
    type = StringField( max_length=30, choices=APP_TYPE) # iphone or ipad
    board = StringField( max_length=30, choices=APP_BOARD) # paid free grossing
    country = StringField( max_length=100)
    ranks = SortedListField(DictField(),ordering='date')
    '''
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
    '''
    meta = {
        'indexes': ['app_id']
    }
