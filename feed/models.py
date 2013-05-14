from django.db import models
from mongoengine import *
import datetime
from company.models import Company
from django.contrib import admin

class NewsData(models.Model):
    company = models.ForeignKey(Company)
    author = models.CharField( max_length=120,blank = True, null = True )
    domain = models.CharField( max_length=120,blank = True, null = True )
    title = models.CharField( max_length=150 ,unique=True ) 
    link =  models.URLField(blank = True, null = True)
    media = models.CharField( max_length=100,blank = True, null = True )
    pub_date =  models.DateTimeField()
    description = models.TextField(blank = True, null = True )

    def __unicode__(self):
        return str(self.title)

class DataFeed(models.Model):
    company = models.ForeignKey(Company)
    type =  models.CharField( max_length=50, blank = True, null = True)
    period = models.CharField( max_length=50, blank = True, null = True ) 
    amount = models.FloatField( blank = True, null = True)
    percent = models.FloatField( blank = True, null = True)
    direction = models.IntegerField( blank = True, null = True)
    conent = models.TextField(blank = True, null = True )
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return str(self.company.name)

admin.site.register(DataFeed)
admin.site.register(NewsData)
# Create your models here.
class Comment(EmbeddedDocument):
    content = StringField()
    name = StringField(max_length=120)

class Feed(Document):
    date_modified = DateTimeField(default=datetime.datetime.now)
    date_created = DateTimeField(default=datetime.datetime.now)
    company_channels = ListField(StringField(max_length=30))
    industry_channels = ListField(StringField(max_length=30))
    comments = ListField(EmbeddedDocumentField(Comment))
    
    meta = {'allow_inheritance': True}

    
class NewsFeed(Feed):
    company_id = IntField(required=True)
    author = StringField(max_length=120)
    domain = StringField(max_length=120)
    title = StringField(max_length=120, required=True ,unique=True)
    link = StringField()
    media = StringField()
    pub_date = DateTimeField()
    description = StringField() 

    meta={
         'indexes':['title','pub_date'],
         'ordering': ['-pub_date']
    }
