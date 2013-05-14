from celery import task
from company.models import Company 
import time
from django.db.models import Q
from company.crunchbase import * 

def fetchCrunchbaseIcon():
    allCompany = Company.objects.filter(Q(cbpermalink__isnull=False),~Q(appleStore='r'))
    for item in allCompany:
        getCrunchBaseIcon.delay(item)

@task()
def getCrunchBaseIcon(company):
    cb = crunchbase('zmjsk6dn8kmry4e443yfs6u6')
    if company.cbpermalink == None:
        return
    try:
        companyData = cb.getCompanyData(company.cbpermalink)
        print company.id
    except Exception,e:
        print str(e)
        return
    if companyData['image'] != None and len(companyData['image']['available_sizes']) > 0 :
        icon_url = companyData['image']['available_sizes'][-1][1]
        icon = "http://www.crunchbase.com/"+icon_url
        print icon
        company.icon = icon
        company.appleStore='r'
        company.save()
