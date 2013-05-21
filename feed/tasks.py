from celery import task,chord
from company.models import Company
from feed.news_fetch import * 
import time
from ec2.api import * 
from scheduler.views import releaseAllAccounts

@task()
def shutdown(ec2):
    print "shutting down"
    time.sleep(300)
    releaseAllAccounts()
    ec2.stopAllInstances()
    ec2.cancelAllRequest()
    print "finised"
    return True
    
def updatNewsDaily():
    c = Ec2()
    c.launchSpotInstance(10,'single_worker')
    companyList = Company.objects.filter(analysed=True)
    chord( [fetchNewsFromFaroo.delay(item) for item in companyList ])(shutdown.delay(c)).get()
