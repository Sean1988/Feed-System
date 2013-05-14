from django.db import models
from django.contrib import admin
from company.models import Company
# Create your models here.
class LinkedinProfile(models.Model):
    linkedinId=models.IntegerField( default = 0)
    name = models.CharField( max_length=100, blank = True, null = True )
    website = models.CharField( max_length=300, blank = True, null = True )
    founded = models.DateField( blank=True , null=True)
    type =  models.CharField( max_length=100 )
    industry = models.CharField( max_length=100 )
    location = models.CharField( max_length=100 )
    postcode = models.IntegerField( default = 0 )
    locationStr = models.CharField( max_length=400 )
    
    def __unicode__(self):
        return str(self.name)

class LinkedinData(models.Model):
    company = models.ForeignKey(Company)
    follower = models.IntegerField( default = -1 )
    employee = models.IntegerField( default = -1 )
    date =  models.DateField( blank=True , null=True)

    def __unicode__(self):
        return str(self.company.name)


admin.site.register(LinkedinProfile)
admin.site.register(LinkedinData)
