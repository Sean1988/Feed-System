from django.db.models import Q
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.mail import send_mail
import requests

def get_datatables_records(request, limited, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath, *args):

    #Safety measure. If someone messes with iDisplayLength manually, we clip it to
    #the max value of 100.
    if not 'iDisplayLength' in request.GET or not request.GET['iDisplayLength']:
        iDisplayLength = 10 # default value
    else: 
        iDisplayLength = min(int(request.GET['iDisplayLength']),500)

    if not 'iDisplayStart' in request.GET or not request.GET['iDisplayStart']:
        startRecord = 0 #default value
    else:
        startRecord = int(request.GET['iDisplayStart'])
    print startRecord
    endRecord = startRecord + iDisplayLength 
    
    print endRecord
    #apply ordering 
    if not 'iSortingCols' in request.GET or not request.GET['iSortingCols']:
        iSortingCols = 0 #default value
    else:
        iSortingCols = int(request.GET['iSortingCols'])
    asortingCols = []
    if iSortingCols>0:
        for sortedColIndex in range(0, iSortingCols):
            sortedColName = columnIndexNameMap[int(request.GET['iSortCol_'+str(sortedColIndex)])]
            sortingDirection = request.GET['sSortDir_'+str(sortedColIndex)]
            if sortingDirection == 'desc':
                sortedColName = '-'+sortedColName
            asortingCols.append(sortedColName)

        querySet = querySet.order_by(*asortingCols)

    if limited : 
        actualNum = querySet.count()
        querySet= querySet[:50]
        iTotalRecords = iTotalDisplayRecords = 50
    else:        
        iTotalRecords = iTotalDisplayRecords = querySet.count()
    
    #get the slice
    querySet = querySet[startRecord:endRecord]
    

    #prepare the JSON with the response
    if not 'sEcho' in request.GET or not request.GET['sEcho']:
        sEcho = '0' #default value
    else:
        sEcho = request.GET['sEcho'] #this is required by datatables 
    jstonString = render_to_string(jsonTemplatePath, locals())
    
    return HttpResponse(jstonString, mimetype="application/javascript")

def get_app_records(request, querySet, columnIndexNameMap, searchableColumns, jsonTemplatePath, *args):

    #Safety measure. If someone messes with iDisplayLength manually, we clip it to
    #the max value of 100.
    if not 'iDisplayLength' in request.GET or not request.GET['iDisplayLength']:
        iDisplayLength = 10 # default value
    else: 
        iDisplayLength = min(int(request.GET['iDisplayLength']),500)

    if not 'iDisplayStart' in request.GET or not request.GET['iDisplayStart']:
        startRecord = 0 #default value
    else:
        startRecord = int(request.GET['iDisplayStart'])
    print startRecord
    endRecord = startRecord + iDisplayLength 
    
    '''
    #apply ordering 
    if not 'iSortingCols' in request.GET or not request.GET['iSortingCols']:
        iSortingCols = 0 #default value
    else:
        iSortingCols = int(request.GET['iSortingCols'])
    asortingCols = []
    if iSortingCols>0:
        for sortedColIndex in range(0, iSortingCols):
            sortedColName = columnIndexNameMap[int(request.GET['iSortCol_'+str(sortedColIndex)])]
            sortingDirection = request.GET['sSortDir_'+str(sortedColIndex)]
            if sortingDirection == 'desc':
                sortedColName = '-'+sortedColName
            asortingCols.append(sortedColName)

        querySet = querySet.order_by(*asortingCols)   
    ''' 
    #count how many records match the final criteria
    iTotalRecords = iTotalDisplayRecords = len(querySet)
    
    #get the slice
    querySet = querySet[startRecord:endRecord]
    
    #prepare the JSON with the response
    if not 'sEcho' in request.GET or not request.GET['sEcho']:
        sEcho = '0' #default value
    else:
        sEcho = request.GET['sEcho'] #this is required by datatables 
    jstonString = render_to_string(jsonTemplatePath, locals())
    
    return HttpResponse(jstonString, mimetype="application/javascript")


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def sendMsgAlert(msg):
    send_mail('signl Server alert', msg, 'info@signl.com',['8482289101@vtext.com'])

    
def ajax_login_required(view_func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated():
            return view_func(request, *args, **kwargs)
        jsonObj = json.dumps({ 'not_authenticated': True })
        return HttpResponse(jsonObj, mimetype='application/json')
    wrap.__doc__ = view_func.__doc__
    wrap.__dict__ = view_func.__dict__
    return wrap
    
def getGlobalRank(site):
    url = "http://api.similarweb.com/Site/%s/GlobalRank?Format=JSON&UserKey=b8140d6db6e9181b65a423a76ca4d7ea" % site
    response = requests.get(url)
    #print response.text
    try:
        data = json.loads(response.text)
        return int(data['Rank'])
    except:
        return False

        
blackList = ["wix.com/",
             "crunchbase.com",
             "youtu.be",
             "indiegogo.com/",
             "angel.co/",
             "facebook.com/",
             "/twitter.com/",
             "linkedin.com/",
             "youtube.com/",
             "slideshare.com",
             "itunes.apple.com",
             "blogs.mail.ru",
             "goo.gl",
             "yellowpages.com/",
             "@gmail",
             "behance.com/",
             "about.me/",
             'wikipedia.org/',
             'scribd.com/']

nameList = ["wix",
             "angellist",
             "facebook",
             "twitter",
             "linkedin",
             "youtube",
             "slideshare",
             "apple",
             "yellowpages",
             "gmail",
             "behance",
             "about.me",
             'wikipedia',
             'scribd']

def urlBlackList(name,website):
    for item in blackList:
        if item in website.lower() and name.lower() not in nameList :
            return True
    return False

def trimUrl(url):
    if url == None:
        return None
    url_split = url.split("//")
    if len(url_split) > 1:
        url = url_split[1]
    else:
        url = url_split[0]
    count = url.find("www.")
    if count>=0:
        url = url[(4+count):]
    if url.endswith("/"):
        url=url[:-1]
    url = url.split("/")[0]
    return url

from numpy import arange,array,ones,linalg
from pylab import plot,show


def rescale(reach):
    top = max(reach)
    bot = min(reach)
    for i in range(len(reach)):
        reach[i] = calRescale(reach[i],bot,top)
    return reach

def distance(reach):
    return max(reach) - min(reach)

def calRescale(x,bot,top):
    return float((x-bot)*100)/float(top-bot)

def li2(dataArray):
    reach = []
    for item in dataArray:
        reach.append(item.reach)
    #reach = rescale(reach)
    xi = arange(0,len(reach))
    A = array([ xi, ones(len(reach))])
    # linearly generated sequence
    #y = [19, 20, 20.5, 21.5, 22, 23, 23, 25.5, 24]
    w = linalg.lstsq(A.T,reach)[0] # obtaining the parameters
    print "slope = %s" % str(w[0])
    print "offset = %s" % str(w[1])
     
    # plotting the line
    line = w[0]*xi+w[1] # regression line
    print xi
    print line
    plot(xi,line,'r-',xi,reach,'o')
    show()

