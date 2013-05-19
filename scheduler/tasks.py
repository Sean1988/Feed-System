from celery import task,chord
#from company.models import Company
#import boto.ec2
from marketing.promot import sendPromotEmail

@task()
def sendMarketingEmail():
    print "sending promot email start "
    sendPromotEmail()
    print "sending promot email end"
    
