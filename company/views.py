# Create your views here.
#http://stackoverflow.com/questions/488670/calculate-exponential-moving-average-in-python

 
from dateutil import parser
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import simplejson as json
 
import requests
from BeautifulSoup import BeautifulSoup
import time
from itertools import chain
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Sum
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login
from django.contrib import auth
from haystack.query import SearchQuerySet
from company.cache import *
from mobile.itunesData import *
from mobile.models import * 
from web.models import * 
from company.mathLogic import *
from company.angellist import *
from company.models import *
from linkedin.models import * 
from haystack.inputs import AutoQuery, Exact, Clean
from django.template.defaultfilters import slugify
from company.crunchbaseData import getCrunchBaseFunding
from account.perm import * 
import redis

def slugall():
    all = Tag.objects.filter(slug__isnull =True)
    for item in all:
        print item.id
        slugStr = slugify(item.tagName)
        try:
            item.slug = slugStr
            item.save()
        except: 
            for i in range(1,10):
                slugStrNew = slugStr + str(i)
                try:
                    item.slug =slugStrNew
                    item.save()
                except:
                    continue
                else:
                    break

@login_required
def industry(request,slug):
    if request.method == 'GET':
        user = request.user
        if slug == "all":
            tagId = 0
            tag = None
        else: 
            if slug == None or slug == "":
                return render(request, '404.html', locals())
            try:
                tag = Tag.objects.get(slug = slug)
            except:
                return render(request, '404.html', locals())
            else:
                if tag.fetched == False:
                    return render(request, '404.html', locals())
            tagId = tag.id
            tagName = tag.tagName
        
        limited = check_permission(request,tag)
        return render(request, 'tagResult.html', locals())
    else:
        return render(request, '404.html', locals())

def marketingRedic(request):
    comp = request.GET.get('comp')
    if comp !=None:
        return HttpResponseRedirect("/accounts/register/?comp=%s"% comp)
    else:
        return render(request, '404.html', locals())


def applyFilter(querySet,hasApp,rank,universe,launch,funded,minFunding,maxFunding,hasLinkedin):
    if hasApp != None and int(hasApp)==1:
        querySet = querySet.filter(hasApp=True)
    if rank != None and rank != 0 :
        if rank == '10k':
            querySet=querySet.filter(rank__lte=10000)
        elif rank=='100k':
            querySet=querySet.filter(rank__lte=100000)
    if universe !=None and int(universe) == 1:
        querySet=querySet.filter(cbpermalink__isnull=False,companyId__gt=0)
    if launch !=None and int(launch)!= 0:
        if int(launch) == 1:
            querySet=querySet.filter(justLaunched=True)
        elif int(launch) ==2:
            querySet=querySet.filter(justLaunched=False)
    if hasLinkedin !=None  and int(hasLinkedin) ==1:
        querySet = querySet.filter(linkedInId__gt=0)

    if funded != None and int(funded)==1 :
        if minFunding !=None:
            if int(minFunding)==0:
                querySet = querySet.filter(totalFunding__gte=1)
            else:
                querySet=querySet.filter(totalFunding__gte=int(minFunding))
    elif funded != None and int(funded)==0:
            querySet=querySet.filter(totalFunding__gte=int(minFunding))

    if maxFunding !=None:
        querySet=querySet.filter(totalFunding__lte=int(maxFunding))

    return querySet


def get_company_list(request):
    if request.method == 'GET':
        tagId = request.GET.get('tagId')
        tagName = request.GET.get('tagName')
        hasApp =  request.GET.get('hasApp')
        rank = request.GET.get('rank')
        universe = request.GET.get('universe')
        launch = request.GET.get('launch')
        funded = request.GET.get('funded')
        minFunding = request.GET.get('minFunding')
        maxFunding = request.GET.get('maxFunding')
        hasLinkedin = request.GET.get('hasLinkedin')

        response = {}
        response["aaData"] = []

        columnIndexNameMap = { 0 : 'idx', 1: 'name', 2: 'website', 3: 'smooth', 4: 'rank',5: 'DT_RowId',  }
        searchableColumns = ['name', 'site']
        
        if int(tagId) == 0 :
            company_array= Company.objects.all().order_by('-smooth')
            tag=None
        else:
            try:
                tag = Tag.objects.get(id = tagId)
            except:
                HttpResponse(json.dumps(response))
            else:
                if tag.fetched == False:
                    HttpResponse(json.dumps(response))
            company_array  =  Company.objects.filter(tags=tag,analysed=True).order_by('-smooth')
        company_array =  applyFilter(company_array,hasApp,rank,universe,launch,funded,minFunding,maxFunding,hasLinkedin)

        limited = check_permission(request,tag)
        if limited :
            jsonTemplatePath = 'json_company_limit.txt'
        else:
            jsonTemplatePath = 'json_company_full_access.txt'
 
        return get_datatables_records(request,limited, company_array, columnIndexNameMap, searchableColumns, jsonTemplatePath)

from company.tools import cp1252
@csrf_exempt 
def getTrafficData(request):
    if request.method == 'GET':
        companyId= request.GET.get('id')
        response = {}
        try:
            company = Company.objects.get(id = companyId)
        except:
            return HttpResponse(json.dumps({'success':False}) )
        else:
            app = []
            linkedin = []
            reach = WebTraffic.get_reach(company.id)
            appList = IosApp.objects.filter(company=company)
            linkedinData = LinkedinData.objects.filter(company=company)
            #print appList
            for item in appList:
                newApp = {'id':item.id,'name':item.trackName,'icon':item.icon,'link':item.link}
                app.append(newApp)
    
            for item in linkedinData:
                newItem = {'date':str(item.date),'employee':item.employee,'follower':item.follower}
                linkedin.append(newItem)
                
            response={'success':True,'reach': reach, 'slug':company.slug,'app':app,'linkedin':linkedin}
            if company.admin != None:
                response['contact']= company.admin.slug
            elif company.slug != None:
                response['contact'] = company.slug
            
            if company.overview != None:
                try:
                    overview = company.overview
                    pattern = re.compile(r'\b(' + '|'.join(cp1252.keys()) + r')\b')
                    result = pattern.sub(lambda x: cp1252[x.group()], overview)
                    response['overview'] = result.decode('unicode-escape')
                except:
                    response['overview'] = ''
            else:
                response['overview'] = ''

            data = json.dumps(response)
        return HttpResponse(data)


def tagAutocomplete(request):
    if request.method == 'GET':
        query= request.GET.get('query')
        onlyIndustry =  request.GET.get('onlyIndustry')
        suggestions = []
        if onlyIndustry:
            sgs = SearchQuerySet().models(Tag).autocomplete(content_auto=query,tagType="Industry")[:8] 
        else:
            sgs = SearchQuerySet().models(Tag).autocomplete(content_auto=query)[:8]
        
        for item in sgs:
            suggestions.append({'value':item.object.tagName,'data':item.object.slug})
        the_data = json.dumps({
            'query': "Unit",
            'suggestions': suggestions
        })
        return HttpResponse(the_data, content_type='application/json')

def companyAutocomplete(request):
    if request.method == 'GET':
        query= request.GET.get('query')
        sgs= SearchQuerySet().models(Company).autocomplete(content_auto=query)[:8]
        suggestions = []
        for item in sgs:
            suggestions.append({'value':item.object.name,'data':item.object.slug})

        the_data = json.dumps({
            'query': "Unit",
            'suggestions': suggestions
        })
        return HttpResponse(the_data, content_type='application/json')


def search(request):
    if request.method == 'GET':
        text = request.GET.get('text')

        results = SearchQuerySet().models(Tag).auto_query(text).order_by('-tagType','rank')

    return render(request, 'searchResult.html', locals())

@login_required
def searchMarketTag(request):
    if request.method == 'GET':
        response_data = {}
        query= request.GET.get('query')
        type = request.GET.get('type')
        s = requests.Session()
        url = "https://api.angel.co/1/search"
        payload = { 'query': query, 'type': type}
        response = s.get(url,data=payload)
        #data = json.loads(response.text)
        return HttpResponse(response.text)



@login_required
def searchTag(request):
    if request.method == 'GET':
        tagName= request.GET.get('tagName')
        tagSlug= request.GET.get('tagSlug')
        user = request.user
        if tagName == "All":
            tagId = 0
            tag = None
        else:    
            try:
                if tagSlug != None and tagSlug != "":
                    tag = Tag.objects.get(slug = tagSlug)
                else:
                    tag = Tag.objects.get(tagName = tagName)
            except:
                return render(request, '404.html', locals())
            else:
                if tag.fetched == False:
                    return render(request, '404.html', locals())
            tagId = tag.id
            tagName = tag.tagName
        
        limited = check_permission(request,tag)
        return render(request, 'tagResult.html', locals())
    else:
        return render(request, '404.html', locals())


def tagWithCompany(request,tagSlug,slug):
    if request.method == 'GET':
        if request.user.is_authenticated():
            return HttpResponseRedirect('/industry/'+tagSlug)

        tag = None
        try:
            comp = Company.objects.get(slug=slug)
        except:
            return render(request, '404.html', locals())
        else:
            for item in comp.tags.all():
                if item.slug == tagSlug:
                    tag = item
                    break;
        if tag == None:
            return render(request, '404.html', locals())

        allCompany = Company.objects.filter(tags=tag).order_by('-smooth')
        c = RankCache()
        print "aall somcpasd %s " % len(allCompany)
        startRecord = int(c.getRank(comp,tag))
        print startRecord
        endRecord = startRecord -3
        sub = allCompany[endRecord:startRecord-1]
        sub2 = allCompany[startRecord:startRecord+3]

        return render(request, 'tagCompany.html', locals())   

@login_required
def getCompany(request,slug):
    if request.method == 'GET':
        id = request.GET.get('startupId')
        name = request.GET.get('startupName')
        try:
            company = Company.objects.get(slug=slug)
        except:
            return render(request, 'noResult.html', locals()) 
            print "can't get startup"
        else:
            tags = company.tags.all()
            tagsRank = []
            c = RankCache()
            try:
                for tag in tags:
                    r = c.getRank(company,tag)
                    if r !=False:
                        tagsRank.append({'rank':r, 'name':tag.tagName,'id':tag.tagId})
            except:
                pass
            return render(request, 'startupResult.html', locals())
            #else:
                #return render(request, 'noResult.html', locals())


def update(request):
    getCrunchBaseFunding()
    return HttpResponse("Good!")

def aboutUs(request):
    next = request.GET.get('next')
    c = {}
    c.update(csrf(request))
    if next !=None:
        c.update({'next':next})

    return render(request,"aboutUs.html", c)

def contactUs(request):
    next = request.GET.get('next')
    c = {}
    c.update(csrf(request))
    if next !=None:
        c.update({'next':next})

    return render(request,"contactUs.html", c)

def termsOfService(request):
    next = request.GET.get('next')
    c = {}
    c.update(csrf(request))
    if next !=None:
        c.update({'next':next})

    return render(request,"terms.html", c)

def privatePolicy(request):
    next = request.GET.get('next')
    c = {}
    c.update(csrf(request))
    if next !=None:
        c.update({'next':next})

    return render(request,"privatePolicy.html", c)

def searchView(request):
    isSearchPage = True
    return render(request, 'search.html', locals()) 

def main(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/feed/')
    else:
        return HttpResponseRedirect('/accounts/register/')

def searchApp(request):
    return render(request, 'appResult.html', locals())

def test(request):
    return render(request, 'test.html', locals())

