# Create your views here.
from mobile.models import *
from company.models import * 
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import simplejson as json
from mobile.itunesData import * 

def get_app_list(request):
    if request.method == 'GET':
        country = request.GET.get('country')
        category = request.GET.get('category')
        board =  request.GET.get('board')
        #rank = request.GET.get('rank')
        #universe = request.GET.get('universe')
        #launch = request.GET.get('launch')
        response = {}
        response["aaData"] = []
        
        columnIndexNameMap = { 0 : 'idx', 1: 'icon', 2: 'name', 3: 'score', 4: 'DT_RowId',  }
        searchableColumns = ['name']
        jsonTemplatePath = 'json_app.txt'
        
        c = IosAppCache()
        app_results= c.getAppsFromSet(country,category,board)
        #print app_results
        id_list=[]
        score_map ={}
        for appUnit in app_results:
            id_list.append(int(appUnit[0]))
            score_map[int(appUnit[0])]=float(appUnit[1])

        #id_list = [ int(d[0]) for d in app_results ]
        app_array= IosApp.objects.filter(id__in=id_list)
        for item in app_array:
            item.score = score_map[item.id]

        app_array = sorted( app_array, key=lambda x: x.score, reverse=True)
        return get_app_records(request, app_array, columnIndexNameMap, searchableColumns, jsonTemplatePath)


@csrf_exempt
def getAppRank(request):
    if request.method == 'GET':
        appId= request.GET.get('id')
        print appId
        rank = []
        try:
            app = IosApp.objects.get(id=appId)
        except:
            return HttpResponse("can not find app")
        else:
            resultList = []
            iosRank = list(IosAppRank.objects.filter(app = app).order_by('label','date'))
            labelList=[]
            for item in iosRank:
                if item.label.label not in labelList:
                    labelList.append(item.label.label)
                newRank = {'date':str(item.date),'rank':item.rank,'label':item.label.label}
                resultList.append(newRank)

        return HttpResponse(json.dumps({'label':labelList,'data':resultList}))

@csrf_exempt         
def getAppRankHistory(request):
    if request.method == 'GET':
        appId = request.GET.get('id')
        country = request.GET.get('country')
        category = request.GET.get('category')
        board = request.GET.get('board')
        response ={}

        c = IosAppCache()
        result = c.getDayRankByVar(appId,country,category,board)
        try:
            obj = IosApp.objects.get(id = appId)
        except:
            print "error , cant get app"
            link = ""
            seller = ""
        else:
            link = obj.link
            seller = obj.artistName

        return HttpResponse(json.dumps({"data":result,"link":link,"seller":seller}))

  
