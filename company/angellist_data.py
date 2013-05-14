from company.angellist import *
from company.models import Company
from django.db.models import Q
import time

def getAngellistIcon():
    al = AngelList()
    allComp = Company.objects.filter(Q(companyId__gt=0),~Q(googlePlay='wq'))
    count = 0
    i = 0 
    while i < len(allComp):
    	item = allComp[i]
        count+=1
        print count
        print item.id
        print "angel list id = %s " % item.companyId
        try:
            startup = al.getStartups(startup_id=item.companyId)
        except Exception, e :
            print str(e)
            if str(e) == "HTTP Error 403: Forbidden":
            	time.sleep(100)
            	al.switchAccount()
                continue
            item.googlePlay = 'wq'
            item.companyId = 0
            item.save()
            i+=1
            continue
        if startup['hidden'] == True:
            item.googlePlay = 'wq'
            item.save()
            i+=1
            continue
        if startup.has_key('logo_url') and startup['logo_url']!= None and startup['logo_url']!="":
            item.icon = startup['logo_url']
        if startup.has_key('thumb_url') and startup['thumb_url'] != None and startup['thumb_url']!="":
            item.thumb = startup['thumb_url']
        if startup.has_key('product_desc') and startup['product_desc'] != None and startup['product_desc']!="":
            item.overview = startup['product_desc']
        if startup.has_key('twitter_url') and startup['twitter_url'] != None and startup['twitter_url']!="":
            try:
                twitter = startup['twitter_url'].split('twitter.com/')[1]
            except:
                pass
            item.twitter = ''.join(i for i in twitter if i.isalpha())
        if startup.has_key('angellist_url') and startup['angellist_url']!= None and startup['angellist_url']!="":
            item.angelListSlug = startup['angellist_url'].split('https://angel.co/')[1]
            print item.angelListSlug
        item.googlePlay = 'wq'
        item.save()

        i+=1
            



