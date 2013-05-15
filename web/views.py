from awis import * 
from lxml import etree
from web.models import * 
from feed.models import * 
from signl.utils import * 
from dateutil import parser
from company.mathLogic import *
from signl.settings import AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY
from django.db.models import Q
from datetime import date,timedelta,datetime
from company.models import Company, Tag
from celery import task
import pickle      
from dateutil import parser
import requests
from feed.feedImg import generateImgForWebFeed
def generateDataImg():
    allComp = Company.objects.filter(analysed = True)
    for comp in allComp[0:10]:
        traffic = WebTraffic.get_reach(company_id=comp.id)
        if len(traffic) < 30:
            continue
        reach = str([ item['reach'] for item in traffic ])
        reach = reach.replace(' ','')
        reach = reach.replace('[','')
        reach = reach.replace(']','')
        firstDate =  parser.parse(str(traffic[0]['date'])).strftime('%B')[:3]
        endDate =  parser.parse(str(traffic[-1]['date'])).strftime('%B')[:3]
        url = "https://chart.googleapis.com/chart?cht=lc&chds=a&chd=t:%s&chs=150x100&chxt=x&chxl=0:|%s|%s" %(reach,firstDate,endDate)
        print url 
        r = requests.get(url)
        if r.status_code == 200:
            with open('/Users/wenzhixue/change/blastoff/images/%s.png'%comp.id , 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)

def temp4():
    wrong  = Company.objects.filter(fetched=520)
    for item in wrong:
        replaceWrongAlexaData(item,20121016)
        replaceWrongAlexaData(item,20121116)
        replaceWrongAlexaData(item,20121216)

import numpy
def temp3():
    allComp = Company.objects.filter(analysed = True)
    for comp in allComp:
        traffic = WebTraffic.objects.get(company_id=comp.id).traffic
        wrong = []
        correct = []
        for item in traffic:
            if item['date'] >= 20121016 and item['date']<= 20130114:
                wrong.append(item)
            else:
                correct.append(item)
        wrongData = [pickle.loads(str(i['data']))[0] for i in wrong]
        correctData = [pickle.loads(str(i['data']))[0] for i in correct]
        wrongDataAvg = float(numpy.average(wrongData))
        correctDataAvg =  float(numpy.average(correctData))
        if correctDataAvg == 0 :
            continue
        if wrongDataAvg/correctDataAvg > 10 or wrongDataAvg/correctDataAvg < 0.01 :
            print "find error company %s and id is %s " % (comp.slug, comp.id)
            comp.fetched = 520
            comp.save() 

def temp2():
    allComp = Company.objects.filter(analysed = True)
    for item in allComp:
        traffic = WebTraffic.objects.get(company_id = item.id).traffic
        print item.id
        if len(traffic) > 30:
            #generateRankFeed(traffic,item)
            generateReachFeed(traffic,item)

#==================Fetch Alexa Data using AWIS API !=========================================    
#============================================================================================

def getTimeYear(month,year):
    dateInt = date(year = year,month=month,day=15).strftime("%Y%m%d")
    return dateInt

def getTestDate(month,year):
    return date(year = year,month=month,day=20)

def findCompanyHasAlexaData():
    companies = Company.objects.filter(fetched=224)
    for company in companies:
        a = fetcheAlexaHistoricalData(company,1,2013)
        company.fetched=201303
        company.save()




def getStartDateAndDistance(traffic):
    if len(traffic) == 0 :
        return (date.today()-timedelta(days=31)).strftime("%Y%m%d"), 31
    else:
        last_day = datetime.strptime(str(traffic[-1]['date']),'%Y%m%d')
        print "last day is %s " % last_day
        distance = (datetime.today() - last_day).days
        return (last_day+timedelta(days=1)).strftime("%Y%m%d"),distance


@task()
def replaceWrongAlexaData(company,startDay):
    webtraffic = WebTraffic.objects.get(company_id = company.id)
    company_url = trimUrl(company.website)
    try:    
        api = AwisApi(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        tree = api.traffic_history(company_url, 31, startDay, "History")
    except:
        print "getting awis api error "
        return 2
    
    historicalData = tree.find('//aws:HistoricalData', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
   
    if historicalData ==None or len(historicalData) == 0:
        print "get nothing from historicalData from site %s" % company_url
        return 2
    newDateSet = {}
    newDataList = []
    for item in historicalData:
        dateText = item.find('.//aws:Date', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        dateInt = int(parser.parse(dateText).strftime("%Y%m%d"))
        reachObj = item.find('.//aws:Reach', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
        reach = reachObj.find('.//aws:PerMillion', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        rank = item.find('.//aws:Rank', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        pageViewsObj =  item.find('.//aws:PageViews', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
        pv_perMillion = pageViewsObj.find('.//aws:PerMillion', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        pv_perUser = pageViewsObj.find('.//aws:PerUser', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        if pv_perMillion == None: pv_perMillion = 0
        if pv_perUser == None : pv_perUser = 0
        if reach == None : reach = 0
        data = [float(reach),int(rank),float(pv_perMillion),float(pv_perUser)]
        newDateSet[dateInt] = 1
        newDataList.append({'date':dateInt,'data':pickle.dumps(data)})
    
    for i in xrange(len(webtraffic.traffic) - 1, -1, -1):
        print webtraffic.traffic[i]['date']
        if newDateSet.has_key(webtraffic.traffic[i]['date']):
            webtraffic.traffic.remove(webtraffic.traffic[i])
    webtraffic.save()

    for newData in newDataList:
        webtraffic.traffic.append(newData)
    webtraffic.save()
    print "!!!!!!successfuly save date for site %s for month %s" % (company.website,str(startDay))

@task()
def fetcheMissingAlexaData(company,startDay,webtraffic):
    company_url = trimUrl(company.website)
    try:    
        api = AwisApi(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        tree = api.traffic_history(company_url, 31, startDay, "History")
    except:
        print "getting awis api error "
        return 2
    
    dateList = set([i['date'] for i in webtraffic.traffic])
    historicalData = tree.find('//aws:HistoricalData', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
   
    if historicalData ==None or len(historicalData) == 0:
        print "get nothing from historicalData from site %s" % company_url
        return 2

    for item in historicalData:
        dateText = item.find('.//aws:Date', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        dateInt = int(parser.parse(dateText).strftime("%Y%m%d"))
        reachObj = item.find('.//aws:Reach', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
        reach = reachObj.find('.//aws:PerMillion', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        rank = item.find('.//aws:Rank', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        pageViewsObj =  item.find('.//aws:PageViews', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
        pv_perMillion = pageViewsObj.find('.//aws:PerMillion', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        pv_perUser = pageViewsObj.find('.//aws:PerUser', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        if pv_perMillion == None: pv_perMillion = 0
        if pv_perUser == None : pv_perUser = 0
        if reach == None : reach = 0
        
        if dateInt not in dateList:
            data = [float(reach),int(rank),float(pv_perMillion),float(pv_perUser)]
            webtraffic.traffic.append({'date':dateInt,'data':pickle.dumps(data)})
        
        else:
            print "find duplicate date %s " % dateInt
    try:
        webtraffic.save()
    except Exception,e:
        print str(e)

    print "!!!!!!successfuly save date for site %s for month %s" % (company.website,str(startDay))

@task()
def fetcheAlexaDataAuto(company):
    company_url = trimUrl(company.website)
    webtraffic = WebTraffic.objects.get_or_create(company_id=company.id)[0]
    startDay, distance = getStartDateAndDistance(webtraffic.traffic)
    print "start date %s and distance is %s  " % ( startDay, distance)

    if distance <= 5:
        print "already get data today"
        return
    try:    
        api = AwisApi(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        tree = api.traffic_history(company_url, distance, startDay, "History")
    except Exception,e:
        print str(e)
        return 2
    
    historicalData = tree.find('//aws:HistoricalData', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
    length = len(historicalData)
    if historicalData ==None or length == 0:
        print "get nothing from historicalData from site %s" % company_url
        return 2
    
    for idx, item in enumerate(historicalData):
        dateText = item.find('.//aws:Date', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        dateInt = int(parser.parse(dateText).strftime("%Y%m%d"))
        reachObj = item.find('.//aws:Reach', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
        reach = reachObj.find('.//aws:PerMillion', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        print "date is %s and reach is %s " % (dateText,reach)
        rank = item.find('.//aws:Rank', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        pageViewsObj =  item.find('.//aws:PageViews', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'})
        pv_perMillion = pageViewsObj.find('.//aws:PerMillion', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        pv_perUser = pageViewsObj.find('.//aws:PerUser', namespaces={'aws':'http://awis.amazonaws.com/doc/2005-07-11'}).text
        if pv_perMillion == None: pv_perMillion = 0
        if pv_perUser == None : pv_perUser = 0
        if reach == None : reach = 0
        #check last item is 0 
        if idx == length-1:
            if int(reach) == 0: 
                continue 
        data = [float(reach),int(rank),float(pv_perMillion),float(pv_perUser)]
        webtraffic.traffic.append({'date':dateInt,'data':pickle.dumps(data)})
    try:
        webtraffic.save()
    except Exception,e:
        print str(e)
    print "!!!!!!successfuly save date for site %s about %s for month %s" % (company.website,str(distance),str(startDay))
    #generateRankFeed(webtraffic.traffic,company)
    #generateReachFeed(webtraffic.traffic,company)
    
def createDataFeed(amount,percent,feedType,period,company,traffic):
    if amount > 0:
        direction=1
    elif amount==0:
        return
    else:
        direction=-1
    print "generate feed for company %s type %s amount %s period %s percent %s direct %s" %(company.name,feedType,amount,period,percent,direction)
    datafeed, created = DataFeed.objects.get_or_create(company=company,type=feedType,period=period)
    datafeed.amount=round(amount,3)
    datafeed.percent=percent
    datafeed.direction=direction
    datafeed.save()
    generateImgForWebFeed(datafeed,traffic)
   
def isSpikeTraffic(array):
    count = 0 
    length = len(array)
    if length == 0 :
        return True
    for item in array:
        if int(item) == 0:
            count +=1
    if float(count)/float(length) > 0.3:
        return True
    return False


def generateReachFeed(traffic,company):
    reach = [pickle.loads(str(i['data']))[0] for i in traffic]
    if len(reach)> 14 and not isSpikeTraffic(reach[-14:]):# calculate 1 week
        thisWeekAvg = float(sum(reach[-7:]))/7
        lastWeekAvg = float(sum(reach[-14:-7]))/7
        #print "last week avg = %s this week avg = %s " % (lastWeekAvg , thisWeekAvg)
        amount = thisWeekAvg-lastWeekAvg
        if lastWeekAvg == 0 : 
            percent = 0
        else:
            percent = int(abs(amount/lastWeekAvg)*100)
        if percent > 5: 
            createDataFeed(amount,percent,'reach','1week',company,traffic)
    if len(reach) > 61 and not isSpikeTraffic(reach[-60:]):#calculate 1 month
        thisMonthAvg = float(sum(reach[-30:]))/30
        lastMonthAvg = float(sum(reach[-60:-30]))/30
        #print "last month avg = %s this month avg = %s " % (thisMonthAvg, thisMonthAvg)
        amount = thisMonthAvg-lastMonthAvg
        if lastMonthAvg == 0:
            percent = 0
        else:
            percent = int(abs(amount/lastMonthAvg)*100)
        if percent > 5:
            createDataFeed(amount,percent,'reach','1month',company,traffic)
    if len(reach) > 181 and not isSpikeTraffic(reach[-180:]):#calculate 3 month
        thisThreeMonthAvg = float(sum(reach[-90:]))/90
        lastThreeMonthAvg = float(sum(reach[-180:-90]))/90
        #print "last 3 month avg = %s this 3 month avg = %s " % (lastThreeMonthAvg, thisThreeMonthAvg)
        amount = thisThreeMonthAvg-lastThreeMonthAvg
        if lastThreeMonthAvg == 0 :
            percent = 0
        else:
            percent = int(abs(amount/lastThreeMonthAvg)*100)
        #print percent 
        if percent > 5:
            createDataFeed(amount,percent,'reach','3month',company,traffic)

def generateRankFeed(traffic,company):
    rank = [pickle.loads(str(i['data']))[1] for i in traffic]

    if len(rank) > 15:
        thisWeekAvg= float(sum(rank[-7:]))/7
        lastWeekAvg= float(sum(rank[-14:-7]))/7
        amount = -1*(thisWeekAvg - lastWeekAvg)
        if lastWeekAvg == 0 :
            percent = 0
        else:    
            percent = int(abs(amount/lastWeekAvg)*100)
        if percent >5:
            createDataFeed(amount,percent,'rank','1week',company,traffic)
    if len(rank)> 61 :
        thisMonthAvg = float(sum(rank[-30:]))/30
        lastMonthAvg = float(sum(rank[-60:-30]))/30
        amount = -1*(thisMonthAvg - lastMonthAvg)
        if lastMonthAvg == 0:
            percent = 0
        else:
            percent= int(abs(amount/lastMonthAvg)*100)
        if percent >5:
            createDataFeed(amount,percent,'rank','1month',company,traffic)
    if len(rank) > 181:
        thisThreeMonthAvg = float(sum(rank[-90:]))/90
        lastThreeMonthAvg= float(sum(rank[-180:-90]))/90
        amount = -1*(thisThreeMonthAvg-lastThreeMonthAvg)
        if lastThreeMonthAvg == 0:
            percent = 0
        else:
            percent= int(abs(amount/lastThreeMonthAvg)*100)
        if percent >1:
            createDataFeed(amount,percent,'rank','3month',company,traffic)
      
    
from collections import namedtuple
from operator    import itemgetter

def smooth(reach_data, alpha=1, today=None):
    """Perform exponential smoothing with factor `alpha`.

    Time period is a day.
    Each time period the value of `iq` drops `alpha` times.
    The most recent data is the most valuable one.
    """
    assert 0 < alpha <= 1

    if alpha == 1: # no smoothing
        return sum(map(itemgetter(1), reach_data))

    if today is None:
        today = max(map(itemgetter(0), reach_data))

    return sum(alpha**((today - date).days) * reach for date, reach in reach_data)


def calGrowth(dataArray):
    firstWeek = dataArray[:7]
    lastWeek = dataArray[7:]
    firstWeek_sum =  sum(obj.reach for obj in firstWeek)
    lastWeek_sum =  sum(obj.reach for obj in lastWeek)
    if firstWeek_sum == 0:
        return 0
    return float((lastWeek_sum-firstWeek_sum)/firstWeek_sum)

def avg(array):
    return float(sum(array))/len(array)


def removeBadCompany():
    all = Company.objects.all()
    for item in all:
        if urlBlackList(item.name,item.website): 
            print item.name + "--- "+ item.website
            item.delete()

def reAnalyseAll():
    companyList = Company.objects.filter(analysed=True)
    for item in companyList:
        print "analysing company %s" % item.name
        reAnalyse(item)
    print "end"

def analyseData(reach,company,lastRank):
    average = avg(reach)
    if distance(reach) == 0:
        return
    reach = rescale(reach)
    company.smooth = li(reach)*100
    if average < 2:
        company.smooth = company.smooth/5
    company.rank = lastRank
    company.save()
    return 
    
