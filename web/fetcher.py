
from signl.settings import AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY
from datetime import date,timedelta,datetime
from signl.utils import * 
from web.models import * 
from celery.contrib.methods import task
from awis import * 
from dateutil import parser
import pickle 

AWIS_NAMESPACE = {'aws':'http://awis.amazonaws.com/doc/2005-07-11'}
class WebDataFetcher(object):

    def __init__(self):
        pass#self.session = self.login()

	def _getStartDateAndDistance(self,traffic):
	    if len(traffic) == 0 :
	        return (date.today()-timedelta(days=31)).strftime("%Y%m%d"), 31
	    else:
	        last_day = datetime.strptime(str(traffic[-1]['date']),'%Y%m%d')
	        print "last day is %s " % last_day
	        distance = (datetime.today() - last_day).days
	        return (last_day+timedelta(days=1)).strftime("%Y%m%d"),distance

	@task()
	def fetcheAlexaDataAuto(self,company):
	    company_url = trimUrl(company.website)
	    webtraffic, created = WebTraffic.objects.get_or_create(company_id=company.id)
	    startDay, distance = self._getStartDateAndDistance(webtraffic.traffic)
	    print "start date %s and distance is %s  " % ( startDay, distance)

	    if distance <= 5:
	        print "already get data today"
	        return
	    try:    
	        api = AwisApi(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
	        tree = api.traffic_history(company_url, distance, startDay, "History")
	    except Exception,e:
	        print str(e)
	        return
	    
	    historicalData = tree.find('//aws:HistoricalData', namespaces=AWIS_NAMESPACE)
	    if historicalData ==None or len(historicalData) == 0:
	        print "get nothing from historicalData from site %s" % company_url
	        return 
	    length = len(historicalData)
	    for idx, item in enumerate(historicalData):
	        dateText = item.find('.//aws:Date', namespaces=AWIS_NAMESPACE).text
	        dateInt = int(parser.parse(dateText).strftime("%Y%m%d"))
	        reachObj = item.find('.//aws:Reach', namespaces=AWIS_NAMESPACE)
	        reach = reachObj.find('.//aws:PerMillion', namespaces=AWIS_NAMESPACE).text
	        #print "date is %s and reach is %s " % (dateText,reach)
	        rank = item.find('.//aws:Rank', namespaces=AWIS_NAMESPACE).text
	        pageViewsObj =  item.find('.//aws:PageViews', namespaces=AWIS_NAMESPACE)
	        pv_perMillion = pageViewsObj.find('.//aws:PerMillion', namespaces=AWIS_NAMESPACE).text
	        pv_perUser = pageViewsObj.find('.//aws:PerUser', namespaces=AWIS_NAMESPACE).text
	        if pv_perMillion == None: pv_perMillion = 0
	        if pv_perUser == None : pv_perUser = 0
	        if reach == None : reach = 0
	        #check last item is 0 
	        if idx == length-1 and float(reach) == 0:
	            continue 
	        data = [float(reach),int(rank),float(pv_perMillion),float(pv_perUser)]
	        webtraffic.traffic.append({'date':dateInt,'data':pickle.dumps(data)})
	    try:
	        webtraffic.save()
	    except Exception,e:
	        print str(e)
	    print "!!!!!!successfuly save date for site %s about %s for month %s" % (company.website,str(distance),str(startDay))

    # some company's alexa data is wrong for serveral months
	@task()
	def replaceWrongAlexaData(self,company,startDay):
	    webtraffic = WebTraffic.objects.get(company_id = company.id)
	    company_url = trimUrl(company.website)
	    try:    
	        api = AwisApi(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
	        tree = api.traffic_history(company_url, 31, startDay, "History")
	    except:
	        print "getting awis api error "
	        return
	    
	    historicalData = tree.find('//aws:HistoricalData', namespaces=AWIS_NAMESPACE)
	   
	    if historicalData ==None or len(historicalData) == 0:
	        print "get nothing from historicalData from site %s" % company_url
	        return
	    newDateSet = {}
	    newDataList = []
	    for item in historicalData:
	        dateText = item.find('.//aws:Date', namespaces=AWIS_NAMESPACE).text
	        dateInt = int(parser.parse(dateText).strftime("%Y%m%d"))
	        reachObj = item.find('.//aws:Reach', namespaces=AWIS_NAMESPACE)
	        reach = reachObj.find('.//aws:PerMillion', namespaces=AWIS_NAMESPACE).text
	        rank = item.find('.//aws:Rank', namespaces=AWIS_NAMESPACE).text
	        pageViewsObj =  item.find('.//aws:PageViews', namespaces=AWIS_NAMESPACE)
	        pv_perMillion = pageViewsObj.find('.//aws:PerMillion', namespaces=AWIS_NAMESPACE).text
	        pv_perUser = pageViewsObj.find('.//aws:PerUser', namespaces=AWIS_NAMESPACE).text
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


    # some Company's alexa rank data is missing for serveral months
	@task()
	def fetcheMissingAlexaData(self,company,startDay,webtraffic):
	    company_url = trimUrl(company.website)
	    try:    
	        api = AwisApi(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
	        tree = api.traffic_history(company_url, 31, startDay, "History")
	    except:
	        print "getting awis api error "
	        return 
	    
	    dateList = set([i['date'] for i in webtraffic.traffic])
	    historicalData = tree.find('//aws:HistoricalData', namespaces=AWIS_NAMESPACE)
	   
	    if historicalData ==None or len(historicalData) == 0:
	        print "get nothing from historicalData from site %s" % company_url
	        return 

	    for item in historicalData:
	        dateText = item.find('.//aws:Date', namespaces=AWIS_NAMESPACE).text
	        dateInt = int(parser.parse(dateText).strftime("%Y%m%d"))
	        reachObj = item.find('.//aws:Reach', namespaces=AWIS_NAMESPACE)
	        reach = reachObj.find('.//aws:PerMillion', namespaces=AWIS_NAMESPACE).text
	        rank = item.find('.//aws:Rank', namespaces=AWIS_NAMESPACE).text
	        pageViewsObj =  item.find('.//aws:PageViews', namespaces=AWIS_NAMESPACE)
	        pv_perMillion = pageViewsObj.find('.//aws:PerMillion', namespaces=AWIS_NAMESPACE).text
	        pv_perUser = pageViewsObj.find('.//aws:PerUser', namespaces=AWIS_NAMESPACE).text
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

     