from celery import task,chord
from mobile.models import IosApp
from company.models import Company
import time
from ec2.api import * 
from mobile.itunesData import getCompanyApp
from mobile.fetcher import *
from scheduler.views import releaseAllAccounts
from django.db.models import Q
# this task is to get the app rating and rating count for app.    
def updateAppRating():
    c = Ec2()
    c.launchSpotInstance(7,'two_workers')
    appList = IosApp.objects.filter(ratingCount=0)
    #chord( [getAppRatingAndSave.delay(item) for item in appList ])(shutdown.delay(c)).get()

# mark app hasApp field 
def markHasApp():
    c = Company.objects.all()
    for i in c:
        print i.id
        if IosApp.objects.filter(company=i).exists():
            i.hasApp = True
            i.save()

def CrawlerAppHistoryHistory():
    count = 0
    allComp = Company.objects.filter(analysed=True)
    for comp in allComp:
        apps = IosApp.objects.filter(Q(company=comp),~Q(ratingCount=0),~Q(primaryGenreName="Games"))
        if apps.exists():
            count +=1
    print count 


def scanAppBasicDataFromApple():
    releaseAllAccounts()
    c = Ec2()
    c.launchSpotInstance(6,'single_worker')
    appList = IosApp.objects.filter(primaryGenreName="",trackId__gt=0)
    chord( [getAppBasicData.delay(item) for item in appList ])(c.shutdown.delay()).get()

# to get the init date from appannie inorder to get the whole data range for history
def scanAppAnnieTrackId():
    releaseAllAccounts()
    c = Ec2()
    c.launchSpotInstance(3,'single_worker',True)
    appList = IosApp.objects.filter(trackId__lt=0)
    #for item in appList:
    #    getBasicDataFromAppAnnie(item)
    chord( [getBasicDataFromAppAnnie.delay(item) for item in appList ])(c.shutdown.delay()).get()

def scanAppAnnieStartDate():
    releaseAllAccounts()
    c = Ec2()
    c.launchSpotInstance(7,'single_worker',True)
    appList = IosApp.objects.filter(ratingCount__gt=0, minDate="")
    #for item in appList:
    #    getMinDateForAppAnnie(item)
    chord( [getMinDateForAppAnnie.delay(item) for item in appList ])(shutdown.delay(c)).get()
    
# search company 's app by using apple offical api 
def scanCompanyApp():
    c = Ec2()
    c.launchSpotInstance(7,'two_workers')
    compList = Company.objects.filter(appFetched=False)
    chord( [getCompanyApp.delay(item) for item in compList ])(shutdown.delay(c)).get()
