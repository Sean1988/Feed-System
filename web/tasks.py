from celery import task,chord
from company.models import Company
from web.models import *
from web.views import * 
import pickle
from ec2.api import *
import time

@task()
def shutdown(ec2):
    print "shutting down"
    time.sleep(500)
    ec2.stopAllInstances()
    ec2.cancelAllRequest()
    print "finised"
    return True
     
def reAnalyseAll():
    #c = Ec2()
    #c.launchSpotInstance(7,'two_workers')
    companyList = Company.objects.filter(analysed=True)
    for item in companyList:
        reAnalyse(item)
    #chord( [ reAnalyse.delay(item)  for item in companyList ])(shutdown.delay(c)).get()
    
def transferAll():
    companyList = Company.objects.all()
    for item in companyList:
        print "analysing company %s" % item.id
        transferAlexa.delay(item)
    print 'end'

def updateTrafficWeekely():
    c = Ec2()
    c.launchSpotInstance(7,'two_workers')
    companyList = Company.objects.filter(analysed=True)
    #for item in companyList:
    #    fetcheAlexaDataAuto(item)
    chord( [ fetcheAlexaDataAuto.delay(item)  for item in companyList ])(shutdown.delay(c))
    



def getMissingAlexaData():
    c = Ec2()
    c.launchSpotInstance(5,'two_workers')
    companyList = Company.objects.filter(analysed=True)
    for company  in companyList:
        print company.id
        webtraffic = WebTraffic.objects.get_or_create(company_id=company.id)[0]
        if len(webtraffic.traffic) < 30:
            continue
        else:
            missingMonth = checkMissingMonth(webtraffic.traffic)
            print "find missing date %s for company %s" % (str(missingMonth),company.name)
            for startDay in missingMonth:
                fetcheMissingAlexaData.delay(company,startDay,webtraffic)
        


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


@task()
def reAnalyse(company):
    print "analyse company %s " % company.id
    webtraffic = WebTraffic.objects.get(company_id=company.id)
    if len(webtraffic.traffic) == 0:
        return False
    reach = [pickle.loads(str(i['data']))[0] for i in webtraffic.traffic]
    lastRank = pickle.loads(str(webtraffic.traffic[-1]['data']))[1]
    if len(reach) < 20:
        return False
    else:
        analyseData(reach,company,lastRank)
        
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
