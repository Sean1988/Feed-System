from celery import task,chord
from mobile.models import IosApp
from company.models import Company
import time
from ec2.api import * 
from mobile.itunesData import getAppRatingAndSave,getCompanyApp

@task()
def shutdown(ec2):
    print "shutting down"
    time.sleep(300)
    ec2.stopAllInstances()
    ec2.cancelAllRequest()
    print "finised"
    return True

# this task is to get the app rating and rating count for app.    
def updateAppRating():
    c = Ec2()
    c.launchSpotInstance(7,'two_workers')
    appList = IosApp.objects.filter(ratingCount=0)
    chord( [getAppRatingAndSave.delay(item) for item in appList ])(shutdown.delay(c)).get()

def markHasApp():
    c = Company.objects.all()
    for i in c:
        print i.id
        if IosApp.objects.filter(company=i).exists():
            i.hasApp = True
            i.save()
            

def scanCompanyApp():
    c = Ec2()
    c.launchSpotInstance(7,'two_workers')
    compList = Company.objects.filter(appFetched=False)
    chord( [getCompanyApp.delay(item) for item in compList ])(shutdown.delay(c)).get()
