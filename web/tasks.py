from celery import task,chord
from celery import chain
from company.models import Company
from web.models import *
from web.fetcher import *
from web.feeder import *
from web.analyser import * 
from ec2.api import *
import numpy
import time
import pickle


def webDataProcessor():
    c = Ec2()
    c.launchSpotInstance(7,'two_workers')
    companyList = Company.objects.filter(analysed=True)
    chord( [ webBundleTask.delay(item)  for item in companyList ])(c.shutdown.delay())
    
@task()
def webBundleTask(company):
    fetcher = WebDataFetcher()
    print "getting alexa data"
    newWebTraffic = fetcher.fetcheAlexaDataAuto(company)
    if newWebTraffic == None:
        print "no data found "
        return False
    feeder = WebFeedGenerator()
    print "generate feed image"
    feeder.generateReachFeed(newWebTraffic.traffic,company)
    analyer = WebDataAnalyser()
    print "re-analyse company"
    analyer.reAnalyse(company)


def reAnalyseAll():
    #c = Ec2()
    #c.launchSpotInstance(7,'two_workers')
    analyer = WebDataAnalyser()
    companyList = Company.objects.filter(analysed=True)[0:100]
    for item in companyList:
        analyer.reAnalyse(item)
    #chord( [ analyer.reAnalyse.delay(item)  for item in companyList ])(c.shutdown.delay())
    
def updateTrafficWeekely():
    c = Ec2()
    c.launchSpotInstance(7,'two_workers')
    fetcher = WebDataFetcher()
    companyList = Company.objects.filter(analysed=True)
    #for item in companyList:
    #    fetcher.fetcheAlexaDataAuto(item)
    chord( [ fetcher.fetcheAlexaDataAuto.delay(item)  for item in companyList ])(c.shutdown.delay())
    

def generateReachFeedTask():
    feeder = WebFeedGenerator()
    allComp = Company.objects.filter(analysed = True)
    for item in allComp:
        traffic = WebTraffic.objects.get(company_id = item.id).traffic
        print item.id
        if len(traffic) > 30:
            feeder.generateReachFeed(traffic,item)

#===========================================================================
def replacingWrongWebData():
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


def getMissingAlexaData():
    c = Ec2()
    c.launchSpotInstance(5,'two_workers')
    companyList = Company.objects.filter(analysed=True)
    fetcher = WebDataFetcher()
    for company  in companyList:
        print company.id
        webtraffic, created = WebTraffic.objects.get_or_create(company_id=company.id)
        if len(webtraffic.traffic) < 30:
            continue
        else:
            missingMonth = checkMissingMonth(webtraffic.traffic)
            print "find missing date %s for company %s" % (str(missingMonth),company.name)
            for startDay in missingMonth:
                fetcher.fetcheMissingAlexaData.delay(company,startDay,webtraffic)
        


def checkMissingMonth(traffic):
    dateList = [i['date'] for i in traffic]
    missing_startDate = []
    if not 20120925 in dateList and not 20121005 in dateList:
        missing_startDate.append(20120916)
    if not 20121025 in dateList and not 20121105 in dateList:
        missing_startDate.append(20121016)
    if not 20121125 in dateList and not 20121205 in dateList:
        missing_startDate.append(20121116)
    if not 20121225 in dateList and not 20130105 in dateList:
        missing_startDate.append(20121216)
    if not 20130125 in dateList and not 20130205 in dateList:
        missing_startDate.append(20130116)
    if not 20130225 in dateList and not 20130305 in dateList:
        missing_startDate.append(20130216)
    return missing_startDate

#===========Transfer Mysql data to MongoDb
def transferAll():
    companyList = Company.objects.all()
    for item in companyList:
        print "analysing company %s" % item.id
        transferAlexa.delay(item)
    print 'end'

  
@task()
def transferAlexa(company):
    c = AlexaData.objects.filter(company=company).order_by('date')
    webtrafficObj = WebTraffic.objects.get_or_create(company_id=company.id)[0]
    dateDict = {}
    for i in c:
        dateInt = int(i.date.strftime('%Y%m%d'))
        if dateDict.has_key(dateInt):
            continue
        else:
            data = [i.reach,i.rank,i.pv_perMillion,i.pv_perUser]
            webtrafficObj.traffic.append({'date':dateInt,'data':pickle.dumps(data)})
            dateDict[dateInt]=1
    webtrafficObj.save()
