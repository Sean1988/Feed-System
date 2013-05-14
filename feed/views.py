from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from feed.models import  * 
from random import shuffle
from company.models import Company

from web.models import * 
from dateutil import parser
import requests
from account.models import * 
import boto
from boto.s3.key import Key
from django.core.context_processors import csrf

from signl.settings import AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY
def transferDataToORM():
    allFeed = NewsFeed.objects()
    for item in allFeed:
        company = Company.objects.get(id=item.company_id)
        print item.id
        try:
            NewsData.objects.create(company=company,author=item.author,
                                domain=item.domain,title=item.title,
                                link=item.link,media=item.media,
                                pub_date=item.pub_date,description=item.description)
        except:
            continue

def generateDataImg():
    conn = boto.connect_s3(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY)
    bucket = conn.create_bucket('datafeed-image')
    allComp = Company.objects.filter(analysed = True)
    start = False
    for comp in allComp:
        traffic = WebTraffic.get_reach(company_id=comp.id)
        if len(traffic) < 30:
            continue
        reach = str([ item['reach'] for item in traffic ])
        reach = reach.replace(' ','')
        reach = reach.replace('[','')
        reach = reach.replace(']','')
        firstDate =  parser.parse(str(traffic[0]['date'])).strftime('%B')[:3]
        endDate =  parser.parse(str(traffic[-1]['date'])).strftime('%B')[:3]
        url = "https://chart.googleapis.com/chart?cht=lc&&chds=a&chd=t:%s&chs=150x100&chxt=x&chxl=0:|%s|%s" %(reach,firstDate,endDate)
        r = requests.get(url)
        if r.status_code == 200:
            fileName = '/home/ubuntu/blastoff/company/static/img/datafeed/%s.png'%comp.id 
            with open(fileName,'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            #k = Key(bucket)
            #k.key = '%s.png' % comp.id
            #k.set_contents_from_filename(fileName)

def getFeaturedDataFeed():
    trending = Company.objects.filter(thumb__isnull=False,rank__lt=100000,companyId__gt=0,cbpermalink__isnull=False).order_by('-smooth')


def selectFeedFromCompAndTag(user):
    dataFeedList = []
    newsFeedList = []

    hasIndustry = user.tag.exists()
    if user.comp:
        compDataFeed = list(DataFeed.objects.filter(company=user.comp).order_by('-percent')[:1])
        compNewsFeed = list(NewsData.objects.filter(company=user.comp).order_by('-pub_date')[:1])
        if compDataFeed:
            dataFeedList.append(compDataFeed[0])
        if compNewsFeed:
            newsFeedList.append(compNewsFeed[0])

    if user.tracker.exists():
        for item in user.tracker.all():
            newsTracker = list(NewsData.objects.filter(company=item).order_by('-pub_date')[:1])
            dataFeedTacker = list(DataFeed.objects.filter(company=user.comp).order_by('-percent')[:1])
            if newsTracker:
                newsFeedList.append(newsTracker[0])
            if dataFeedTacker:
                dataFeedList.append(dataFeedTacker[0])    
    if len(newsFeedList) < 4:
        if hasIndustry :
            newsFeedList += getIndustryNewsFeed(user.tag.all()[0])
        else:
            newsFeedList += getDefaultNewsFeed()    
    if len(dataFeedList) < 2:
        if hasIndustry :
            dataFeedList += getIndustryDataFeed(user.tag.all()[0])
        else:
            dataFeedList += getDefaultDataFeed()  
    
    seen_titles = set()
    news_list = []
    for obj in newsFeedList:
        if obj.title not in seen_titles:
            news_list.append(obj)
            seen_titles.add(obj.title)

    feed_list = news_list[:4] + dataFeedList[:2]
    shuffle(feed_list)
    return feed_list


def getDefaultDataFeed():
    return list(NewsData.objects.all().order_by('-pub_date')[:4])

def getDefaultDataFeed():
    return list(DataFeed.objects.all().order_by('-percent')[:2])

def getIndustryNewsFeed(industry):
    comps = Company.objects.filter(tags=industry).order_by('-smooth')[:10]
    news_list = []
    for item in comps:
        if len(news_list) >= 4:
            break
        news_list += list(NewsData.objects.filter(company=item).order_by('-pub_date'))
    if len(news_list) < 4:
        news_list += list(NewsData.objects.all().order_by('-pub_date')[:4])
    return news_list[:4]

def getIndustryDataFeed(industry):
    comps = Company.objects.filter(tags=industry).order_by('-smooth')[:10]
    datafeed_list = []
    for item in comps:
        if len(datafeed_list) >= 2:
            break
        datafeed_list += list(DataFeed.objects.filter(company=item).order_by('-percent'))

    if len(datafeed_list) < 2:
        datafeed_list += list(DataFeed.objects.all().order_by('-percent')[:2])
    return datafeed_list[:2]

def getDefaultFeed():
    feed_list = []
    trending = Company.objects.filter(thumb__isnull=False,rank__lt=100000,companyId__gt=0,cbpermalink__isnull=False).order_by('-smooth')
    for item in trending[0:8]:
        result = getFeedForCompany(item)
        feed_list+=result
    return feed_list

def getRecommends(user):
    trackIds = user.tracker.all().values_list('id',flat=True)
    if user.tag.exists():
        myTag = user.tag.all()[0]
        return Company.objects.filter(companyId__gt=0,thumb__isnull=False,tags=myTag).exclude(id__in = trackIds).order_by('-smooth')
    return Company.objects.filter(companyId__gt=0,thumb__isnull=False).exclude(id__in = trackIds).order_by('-smooth')


def selectDataFeed(dataFeed):
    newDataFeed = []
    for item in dataFeed:
        if abs(float(item.percent.replace('-',''))) > 2:
            newDataFeed.append(item)
    return newDataFeed


def queueFeed(newsFeed,dataFeed):
    data = selectDataFeed(dataFeed)
    allFeed = newsFeed + data

    return allFeed


def getFeedForCompany(company):
    result = []
    try:
        news = NewsData.objects.filter(company=company).order_by('-pub_date')
        data = DataFeed.objects.filter(company=company).order_by('-percent')
    except Exception,e:
        print (e)
    else:
        if news.exists():
            result.append(news[0])
        result+=data
    return result 


@login_required
def feedTestPage(request):
    start = request.GET.get('s')
    end = request.GET.get('e')
    if start == None or end == None:
        dataFeed = DataFeed.objects.all().order_by('-percent')[0:50]
    else:  
        dataFeed = DataFeed.objects.all().order_by('-percent')[start:end]
    return render(request, 'feedTest.html', locals())




@login_required
def feedPage(request):
    recommend = request.GET.get('rmd')
    tracker = request.user.tracker.all()
    user = request.user
    hasTracker = tracker.exists()
    hasIndustry = user.tag.exists()
    
    feed_list= []
    
    if hasIndustry:
        competitor = Company.objects.filter(tags=user.tag.all()[0]).order_by('-smooth')[7:9]

    if recommend !=None and int(recommend) == True or not hasTracker:
        try:
            userTag = user.tag.all()
        except:
            return render(request,"404.html")
        else:
            # We are using 9 since we want to display only 9 companies in recommend.
            if not hasIndustry:
                # if user doesn't have tag, grab top 9 from alexa rank
                rmd = Company.objects.filter(rank__lte=20)[:9]
            else:
                active_user_list = 5
                comp_displayByRank = 9 - active_user_list
                # Company in industry, has user in our db, by rank
                trackIds = tracker.values_list('id',flat=True)
                rmd = Company.objects.filter(tags=userTag[0]).exclude(id__in = trackIds).order_by('-hasUser', 'rank')
                rmd1 = rmd.filter(hasUser=True)[:active_user_list]
                if rmd1.count()<5:
                    comp_displayByRank = 9 - rmd1.count()
                # Company in industry, has no user in our db, by rank
                rmd2 = rmd.filter(hasUser=False)[:comp_displayByRank]
                rmd = list(rmd2)+list(rmd1)
                homeTag = userTag[0].tagName

    if not hasTracker and not hasIndustry and not request.user.comp:
        feed_list = getDefaultFeed()
    elif not hasTracker and hasIndustry :
        feed_list = getDefaultFeed()
    else:
        for company in tracker:
            result= getFeedForCompany(company)
            feed_list += result
    
    shuffle(feed_list)
    recommend_tracker = getRecommends(request.user)

    locals().update(csrf(request))
    return render(request, 'feed.html', locals())

