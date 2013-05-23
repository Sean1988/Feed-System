
from web.models import * 
from celery.contrib.methods import task
from company.mathLogic import *
from company.models import *
from signl.utils import * 
import pickle 
import numpy


def removeBadCompany():
    all = Company.objects.all()
    for item in all:
        if urlBlackList(item.name,item.website): 
            print item.name + "--- "+ item.website
            item.delete()

class WebDataAnalyser(object):
    def __init__(self):
        pass

    @task()
    def reAnalyse(self,company):
        print "analyse company %s " % company.id
        webtraffic = WebTraffic.objects.get(company_id=company.id)
        if len(webtraffic.traffic) == 0:
            return False
        reach = [pickle.loads(str(i['data']))[0] for i in webtraffic.traffic]
        lastRank = pickle.loads(str(webtraffic.traffic[-1]['data']))[1]
        if len(reach) < 20:
            return False
        else:
            self.analyseData(reach,company,lastRank)

    def analyseData(self,reach,company,lastRank):
        average = float(numpy.average(reach))
        if distance(reach) == 0:
            return
        reach = rescale(reach)
        company.smooth = li(reach)*100
        if average < 2:
            company.smooth = company.smooth/5
        company.rank = lastRank
        company.save()
        return 
