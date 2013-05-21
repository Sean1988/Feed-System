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
DOMAIN = 'http://www.appannie.com'

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
        c.stopAndBringNewInstance('single_worker') # bring new instance 
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
    url = "http://www.appannie.com/app/ios/%s/ranking/history/" % app.trackId
    r = requests.get(url)
    bf = BeautifulSoup(r.content)
    js = bf.findAll('script')
    if r.status_code == 403 :
        sendMsgAlert("get blocked by appannie, starting new instance")
        #releaseAccount(APPANNIE_ACCT) # relase appannie account
        #c = Ec2()
        #c.stopAndBringNewInstance('single_worker') # bring new instance 
    if len(js) == 0 :
        print "not getting js"
        return
    c = js[3]
    startPos = c.text.find('app_id')
    if startPos == -1:
        print "not find app_id"
        return
    try:    
        app_id = int(c.text[startPos+8:startPos+8+15].split("'")[1])
    except:
        print "find app id error for ios app %s " % app.id
    else:
        app.trackId = app_id
        app.save()


def getIosAppRankData():
    fetcher = IosAppFetcher()
    app = IosApp.objects.get(id=9413)
    fetcher.getAppHistoryData(app)

class IosAppFetcher:

    def __init__(self):
        self.session = self.login()

    def login(self):
        session = requests.Session()
        payload = { 'username': APPANNIE_ACCT, 'password': APPANNIE_PASS,'next':'/','remember_user':'on'}
        url = 'https://www.appannie.com/account/login/'
        r1 = session.post(url, data=payload,verify=False)
        return session

    def getAppHistoryData(self,app):
        refer = DOMAIN+app.appAnnieLink+"ranking/history/"
        #print refer
        url = refer+"chart_data/?d=iphone&c=143441&f=ranks&s=%s&e=2013-05-15&_c=1" % app.minDate 
        print url
        headers = {'Referer': refer }
        try:
            r = self.session.get(url,headers=headers)
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
            label = getLabelObj(item['label'])
            
            data = item['data']
            if len(data) == 0 : return
            for dayData in data:
                if dayData[1] == None : continue
                date = datetime.fromtimestamp(int(dayData[0])/1000).date()
                print "date = %s rank = %s " % (date,int(dayData[1]))
                note = dayData[2]
                '''
                try:
                    IosAppRank.objects.create(app=app,
                                              label=label,
                                              rank=int(dayData[1]),
                                              date=date,
                                              type='iphone',
                                              country='us',
                                              note=note)
                except Exception, e:
                    print "create rank data error %s" % str(e)
                '''
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

