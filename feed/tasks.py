from celery import task,chord
from company.models import Company
from feed.news_fetch import * 
import time
from ec2.api import * 

@task()
def shutdown(ec2):
    print "shutting down"
    time.sleep(300)
    ec2.stopAllInstances()
    ec2.cancelAllRequest()
    print "finised"
    return True
    
def updatNewsDaily():
    c = Ec2()
    c.launchSpotInstance(7,'single_worker')
    companyList = Company.objects.filter(analysed=True)
    chord( [fetchNewsTask.delay(item) for item in companyList ])(shutdown.delay(c)).get()

@task()
def fetchNewsTask(company):
    print company.id
    fetchNewsFromFaroo(company)
    time.sleep(1)
