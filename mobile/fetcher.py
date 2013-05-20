import requests
import simplejson as json
from BeautifulSoup import BeautifulSoup
from signl.utils import *
from signl.settings import APPANNIE_ACCT, APPANNIE_PASS
from models import *
import time
from django.db.models import Q
from celery import task
DOMAIN = 'http://www.appannie.com'


# for getting history of the app, you must have the earliest date for the data
@task()
def getMinDateForAppAnnie(app):
    url = "http://www.appannie.com/app/ios/%s/ranking/history/" % app.trackId
    print url
    r = requests.get(url)
    bf = BeautifulSoup(r.content)
    js = bf.findAll('script')
    
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
 

def getIosAppRankData():
    s = login()
    app = IosApp.objects.get(id=24706)
    getAppHistoryData(s,app)

class IosAppFetcher:

    def __init__:
        self.s = self.login()

    def login():
        s = requests.Session()
        payload = { 'username': APPANNIE_ACCT, 'password': APPANNIE_PASS,'next':'/','remember_user':'on'}
        url = 'https://www.appannie.com/account/login/'
        r1 = s.post(url, data=payload,verify=False)
        return s 

    def getAppHistoryData(s,app):
        url = app.appAnnieLink
        refer = DOMAIN+url+"ranking/history/"
        #print refer
        url = refer+"chart_data/?d=iphone&c=143441&f=ranks&s=2011-11-16&e=2013-04-24&_c=1"
        print url 
        url = "http://www.appannie.com/app/ios/477128284/ranking/history/chart_data/?d=iphone&c=143444&f=ranks&s=2013-05-08&e=2013-05-21&_c=1"
        headers = {'Referer': refer }
        print headers
        try:
            r = s.get(url,headers=headers)
        except:
            return 
        print "11111"
        print r.content

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
                #print date
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

