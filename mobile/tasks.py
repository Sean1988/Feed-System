from celery import task,chord
from mobile.models import IosApp
from company.models import Company
import time
from ec2.api import * 
from mobile.itunesData import getAppRatingAndSave,getCompanyApp
from mobile.fetcher import getMinDateForAppAnnie

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


# mark app hasApp field 
def markHasApp():
    c = Company.objects.all()
    for i in c:
        print i.id
        if IosApp.objects.filter(company=i).exists():
            i.hasApp = True
            i.save()

# to get the init date from appannie inorder to get the whole data range for history
def scanAppAnnieStartDate():
    c = Ec2()
    c.launchSpotInstance(7,'single_worker')
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
