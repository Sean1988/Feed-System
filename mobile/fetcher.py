import requests
import simplejson as json
from BeautifulSoup import BeautifulSoup
from signl.utils import *
from signl.settings import APPANNIE_ACCT, APPANNIE_PASS
from models import *
from celery import task
from django.db.models import Q
from celery import task
from scheduler.views import releaseAccount
from ec2.api import * 
import itunes
import time
import pickle  
DOMAIN = 'http://www.appannie.com'


def login():
    session = requests.Session()
    payload = { 'username': APPANNIE_ACCT, 'password': APPANNIE_PASS,'next':'/','remember_user':'on'}
    url = 'https://www.appannie.com/account/login/'
    r1 = session.post(url, data=payload,verify=False)
    return session

appAnnieSession = None#login()
# for getting history of the app, you must have the earliest date for the data
@task()
def getMinDateForAppAnnie(app):
    time.sleep(1)
    url = "http://www.appannie.com/app/ios/%s/ranking/history/" % app.trackId
    print url
    r = requests.get(url)
    bf = BeautifulSoup(r.content)
    js = bf.findAll('script')
    if r.status_code == 403 :
        sendMsgAlert("get blocked by appannie, starting new instance")
        releaseAccount(APPANNIE_ACCT) # relase appannie account
        c = Ec2()
        c.stopAndBringNewInstance('single_worker',needEIP=True) # bring new instance 
    if len(js) == 0 :
        print "not getting js"
        return
    c = js[1]
    startPos = c.text.find('min_date')
    if startPos == -1:
        print "not find min_date"
        return
    min_date = c.text[startPos+12:startPos+12+10]
    print min_date
    app.minDate = min_date
    app.save()
 
@task()
def getBasicDataFromAppAnnie(app):
    time.sleep(1)
    url = "http://www.appannie.com%sranking/history/" % app.appAnnieLink
    r = requests.get(url)
    print url 
    bf = BeautifulSoup(r.content)
    js = bf.findAll('script')
    if r.status_code == 403 :
        print "get blocked "
        return
        #sendMsgAlert("get blocked by appannie, starting new instance")
        #releaseAccount(APPANNIE_ACCT) # relase appannie account
        #c = Ec2()
        #c.stopAndBringNewInstance('single_worker',needEIP=True) # bring new instance 
    if len(js) == 0 :
        print "not getting js"
        return
    c = js[3]
    startPos = c.text.find('app_id')
    if startPos == -1:
        print "not find app_id"
        app.delete()
        return
    try:    
        app_id = int(c.text[startPos+8:startPos+8+15].split("'")[1])
    except:
        print "find app id error for ios app %s " % app.id
    else:
        print app_id
        app.trackId = app_id
        app.save()


def getIosAppRankData():
    fetcher = IosAppDataFetcher()
    apps = IosApp.objects.filter(fetched=False,ratingCount__gt=0,minDate__gt=0)[:10]
    for app in apps:
        fetcher.getAppHistoryData(app)
        app.fetched = True
        app.save()




class IosAppDataFetcher:

    def __init__(self):
        pass#self.session = self.login()
        
    def getAppHistoryData(self,app):
        time.sleep(3)
        refer = DOMAIN+app.appAnnieLink+"ranking/history/"
        #print refer
        url = refer+"chart_data/?d=iphone&c=143441&f=ranks&s=%s&e=2013-05-20&_c=1" % app.minDate 
        print url
        headers = {'Referer': refer }
        try:
            r = appAnnieSession.get(url,headers=headers)
        except:
            print "error"
            return 
        if r.content == "[]":
            print "find no data"
            return
        try:
            response = json.loads(r.content)
        except:
            print "find no data"
            return 
        
        for item in response:
            label = item['label']
            print "label = %s id = %s " % (label,app.id)
            try:
                mobileRank = MobileRank.objects.get(app_id=app.id,category=label, type='iphone', board='download', country= 'united-states')
            except:
                mobileRank = MobileRank.objects.create(app_id=app.id,category=label, type='iphone', board='download', country= 'united-states')
            dup_set = set([item['date'] for item in mobileRank.ranks ])
            data = item['data']
            if len(data) == 0 : return
            for dayData in data:
                if dayData[1] == None : continue
                dateInt = int(datetime.fromtimestamp(int(dayData[0])/1000).strftime("%Y%m%d"))
                note = dayData[2]
                if dateInt not in dup_set:
                    #print "date = %s rank = %s " % (dateInt,int(dayData[1]))
                    dayRankData = [int(dayData[1]),note]
                    mobileRank.ranks.append({'date':dateInt,'data':pickle.dumps(dayRankData)})
            print "save data for %s days" % str(len(data))

# using apple 's official itunes Api > no limit
class AppleItunesApi:
    def __init__(self):
        pass
    @task()
    def getAppBasicData(self,ios):
        try:
            app = itunes.lookup(ios.trackId)
        except:
            return 
        else:
            avgRating = app.get_avg_rating()
            if avgRating == None: 
                avgRating = 0
            ratingNum = app.get_num_ratings()
            if ratingNum == None:
                ratingNum = 0
            if ratingNum != 0 or avgRating != 0:
                ios.ratingCount = ratingNum
                ios.avgRating  = avgRating
                ios.save()
    @task()
    def getAppCategory(ios):
        try:
            app = itunes.lookup(ios.trackId)
        except:
            return 
        else:
            avgRating = app.get_avg_rating()
            if avgRating == None: 
                avgRating = 0
            ratingNum = app.get_num_ratings()
            if ratingNum == None:
                ratingNum = 0
            if ratingNum != 0 or avgRating != 0:
                ios.ratingCount = ratingNum
                ios.avgRating  = avgRating
                ios.save()

