from django.db import models
from company.models import Company
from django.contrib import admin
# Create your models here.

    
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

    minDate = models.CharField( max_length=50 )
 
    icon = models.URLField()
    link = models.URLField()
    
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
