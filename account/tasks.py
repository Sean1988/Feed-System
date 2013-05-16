from celery import task,chord
from company.models import Company
import boto.ec2
import time

@task()
def testTask():
    print "1111"