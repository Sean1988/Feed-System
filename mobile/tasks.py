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
import requests
# popid is chart id 
def getTop300FromApple():
    #url = "https://itunes.apple.com/WebObjects/MZStore.woa/wa/categoryList?cc=us&genreId=36&mode=TopCharts&popId=27"
    #url = "https://itunes.apple.com/WebObjects/MZStore.woa/wa/topChartFragmentData?popId=27"
    url = "https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewTop?cc=us&genreId=6017&popId=27&dataOnly=True"
    headers = { #'Referer': "https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewTop?cc=us&genreId=6015&popId=27",
                'X-Apple-Connection-Type': 'WiFi',
                'User-Agent' : 'iTunes-iPhone/6.1.2 (6; 16GB; dt:82)',
                'X-Apple-Store-Front': '143441-1,16',
                'X-Apple-Client-Versions':    'iBooks/3.1; GameCenter/2.0',
                'X-Apple-Client-Application': 'Software',
                'X-Apple-Partner': 'origin.0',
                'X-Dsid' : '1039594798'
              }
    
    r = requests.get(url,headers=headers)
    
    #print r.content
    data = json.loads(r.content)
    print len(data['charts'][0]['content'])
    return data

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

def getIosAppRankData():
    fetcher = IosAppDataFetcher()
    apps = IosApp.objects.filter(fetched=False,ratingCount__gt=0,minDate__gt=0)[:10]
    for app in apps:
        fetcher.getAppHistoryData(app)
        app.fetched = True
        app.save()

def markFirstAppInCompany():
    allComp = Company.objects.filter(analysed=True)
    for comp in allComp:
        apps = IosApp.objects.filter(Q(company=comp),~Q(ratingCount=0),~Q(primaryGenreName="Games")).order_by('-ratingCount')
        if apps.exists():
            firstApp = apps[0]
            firstApp.analysed = True
            firstApp.save()
            
def scanAppHistoryFromAnnie():
    appList = IosApp.objects.filter(analysed = True, fetched = False)
    for app in appList:
        getAppHistoryData(app)

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
