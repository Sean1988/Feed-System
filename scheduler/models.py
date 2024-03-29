from django.db import models
from django.contrib import admin
# Create your models here.

class CrawlerAccount(models.Model):
    type = models.CharField( max_length=50 )
    accountName = models.CharField( max_length=100 )
    accountPass = models.CharField( max_length=100 )
    isUsed =  models.BooleanField(default=False)
    isBlocked = models.BooleanField(default=False)

    def __unicode__(self):
        return str(self.accountName) +" "+ str(self.type) 



admin.site.register(CrawlerAccount)
