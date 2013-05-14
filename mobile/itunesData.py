import itunes 
import redis
import requests
import simplejson as json
from BeautifulSoup import BeautifulSoup
import time
from datetime import datetime
from celery import task
import simplejson as json
import codecs
from django.db.models import Q

from signl.utils import *
from mobile.models import * 
from company.mathLogic import *
from company.models import * 
from signl.settings import APPANNIE_ACCT, APPANNIE_PASS

country_map = {"China":1,"united-states":2,"Australia":3,"Canada":4,"France":5,"Germany":6,
                "Italy":7,"Japan":8,"Netherlands":9,"Russia":10,"Singapore":11,
                "South Korea":12,"Spain":13,"Sweden":14,"Switzerland":15,"united-kingdom":16}

board_map = {"Free":1,"Paid":2,"Grossing":3}

country_list = ["China","united-states","Australia","Canada","France","Germany",
                "Italy","Japan","Netherlands","Russia","Singapore",
                "South Korea","Spain","Sweden","Switzerland","united-kingdom"]

countryCode ={ "China":"CN","Australia":"AU","Canada":"CA","France":"FR","Germany":"DE",
               "Italy":"IT","Japan":"JP","Netherlands":"NL","Russia":"RU","Singapore":"SG",
               "South Korea":"KR","Spain":"ES","Sweden":"SE","Switzerland":"CH","united-kingdom":"GB",
               "united-states":"US"}


category_list = ["social-networking","weather","utilities","travel","sports","reference","productivity",
                 "photo-and-video","overall","newsstand","news","navigation","music","medical","lifestyle",
                 "health-and-fitness","games","food-and-drink","finance","entertainment","education","catalogs",
                 "business","books"]

category_map = {"social-networking": 5 ,"weather":40,"utilities":25,"travel":14,"sports":17,"reference":15,"productivity":23,
                 "photo-and-video":4,"overall":6,"newsstand":44,"news":34,"navigation":36,"music":10,"medical":21,"lifestyle":9,
                 "health-and-fitness":18,"games":1,"food-and-drink":29,"finance":20,"entertainment":11,"education":12,"catalogs":32,
                 "business":27,"books":13}

HOST = 'localhost'
#HOST = '54.235.67.9' 
class IosAppCache:
    def __init__(self):
        self.server = redis.Redis(host=HOST, port=6379, db=3)
        self.server2 = redis.Redis(host=HOST, port=6379, db=4)
    def _getRankKey(self,appId,countryId,categoryId,boardId):
        return "apprank:%s:%s:%s:%s" % (str(appId),str(countryId),str(categoryId),str(boardId))

    def setAppByLink(self,appAnnieLink,id):
        return self.server.hset("iosAppLink",appAnnieLink,id)

    def getAppByLink(self,appAnnieLink):
        return self.server.hget("iosAppLink",appAnnieLink)

    def getAllAppAnnieLink(self):
        return self.server.hgetall("iosAppLink")

    def addDayRank(self,appId,countryId,categoryId,boardId,rank,date):
        key = self._getRankKey(appId,countryId,categoryId,boardId)
        rankStr = "%s:%s" % (date , str(rank))
        return self.server.rpush(key,rankStr)

    def _checkduplicate(self,key,date):
        pass

    def addAppToSet(self,appId,country,category,board,score):
        key = "rankSet:%s:%s:%s" % (country,category,board)
        return self.server2.zadd(key,appId,score)

    def getAppsFromSet(self,country,category,board):
        key = "rankSet:%s:%s:%s" % (country,category,board)
        return self.server2.zrevrange(key,0,-1,withscores=True)

    
    def getDayRankByVar(self,appId,country,category,board):
        key = self._getRankKey(appId,country,category,board)
        return self.getDayRankByKey(key)


    def getDayRankByKey(self,key):
        allData = self.server.lrange(key,0,-1)
        result = []
        duplicate_set = {}
        for data in allData:
            dataSplit = data.split(":") 
            if duplicate_set.has_key(dataSplit[0]):
                continue
            else:
                duplicate_set[dataSplit[0]]=1
            dataJson = {}
            dataJson["date"] = int(dataSplit[0].replace("-",""))
            dataJson["rank"] = int(dataSplit[1])
            result.append(dataJson)
        return sorted(result, key=lambda x: x["date"])

            
    def pushDateImported(self,date):
        key = "apprankdate"
        return self.server.sadd(key,date) 
   
    def getAllImportedDate(self):
        key = "apprankdate"
        return sorted(list(self.server.smembers(key)))
    
    def getAllKeysForCond(self,country,category,board):
        search_key = "*:%s:%s:%s" % (str(country),str(category),str(board))
        all_keys = self.server.keys(search_key)
        return all_keys

    def findCountryByApp(self,appId):
        keys = self.server.keys("apprank:%s:*" % str(appId))
        countryList = []
        for key in keys:
            countryId = int(key.split(":")[2])
            for country_name, country_id in country_map.items():
                if countryId == country_id:
                    countryList.append(country_name)
        return Set(countryList)
    
    def getDateRange(self):
        all_keys = self.server.keys("apprank:*")
        for key in all_keys:
            data= self.server.lrange(key,0,-1)
            for item in data:
                date = item.split(":")[0]
                self.pushDateImported(date)
        self.getAllImportedDat()


def calculateMomAllApps():
    c = IosAppCache()
    for country in country_map.itervalues():
        for category in category_map.itervalues():
            for board in board_map.itervalues():
                searchKey = "*:%s:%s:%s" % (country,category,board)
                print searchKey
                keys = c.getAllKeysForCond(country,category,board)
                for key in keys:
                    result = c.getDayRankByKey(key)
                    if len(result)< 5 :
                        continue
                    appId = int(key.split(":")[1])
                    score = calculateMomScore(result)
                    c.addAppToSet(appId,country,category,board,score)



def calculateMomScore(result):
    rank = []
    for item in result:
        rank.append(item["rank"])
    score = li(rank)*(-1)
    return score
    

    
from mongoengine import *

class DatePushed(Document):
    date = StringField()

class IosDayRankList(Document):
    appId = IntField()
    countryId = IntField()
    categoryId = IntField()
    boardId = IntField()
    dayData = ListField(DictField())

class IosAppScoreSet(Document):
    countryId = IntField()
    categoryId = IntField()
    boardId = IntField()
    appList = ListField(DictField())

class AppAnnieLink(Document):   
    link = StringField(required=True)              
    appId = IntField(required=True)


class IosAppRankDb:

    def __init__(self):
        conn=connect('blastoff')

    def getAppByLink(self,appAnnieLink):
        try:    
            linkObj = AppAnnieLink.objects.get(link=appAnnieLink)
        except Exception,e:
            print str(e)
            return False
        else:
            return linkObj.appId

    def setAppByLink(self,appAnnieLink,appId):
        try:    
            saved = AppAnnieLink.objects.create(link=appAnnieLink,appId = int(appId))
        except Exception,e:
            print str(e)
            return False
            

    def addAppToSet(self,appId,country,category,board,score):
        try:    
            newSet = IosAppScoreSet.objects.get_or_create(countryId=countryId,categoryId=categoryId,boardId=boardId)[0]
        except Exception,e:
            print str(e)
            return False
        else:
            newSet.appList.append({'id':appId,'score':score})
            newSet.save()
            return True

    def getAppsFromSet(self,country,category,board):
        try:    
            newSet = IosAppScoreSet.objects.get(countryId=countryId,categoryId=categoryId,boardId=boardId)[0]
        except Exception,e:
            print str(e)
            return False
        else:
            return newSet.appList

    def addDayRank(self,appId,countryId,categoryId,boardId,rank,date):
        #key = self._getRankKey(appId,countryId,categoryId,boardId)
        try:    
            newObj = IosDayRankList.objects.get(appId= appId, countryId=countryId,categoryId=categoryId,boardId=boardId)
        except:
            newObj = IosDayRankList.objects.create(appId= appId, countryId=countryId,categoryId=categoryId,boardId=boardId)
            print "multiple object returned"
        else:
            try:
                newObj.dayData.append({'date':date,'rank':rank})
                newObj.save()
            except Exception,e:
                print str(e)

    def getDayRankByVar(self,appId,countryId,categoryId,boardId):
        try:
            obj = IosDayRankList.objects.get(appId= appId, countryId=countryId,categoryId=categoryId,boardId=boardId)              
        except Exception,e:
            print str(e)
        else:
            allData = obj.dayData
            result = []
            duplicate_set = {}
            for data in allData:
                dataSplit = data.split(":") 
                if duplicate_set.has_key(dataSplit[0]):
                    continue
                else:
                    duplicate_set[dataSplit[0]]=1
                dataJson = {}
                dataJson["date"] = int(dataSplit[0].replace("-",""))
                dataJson["rank"] = int(dataSplit[1])
                result.append(dataJson)
            return sorted(result, key=lambda x: x["date"])

    def pushDateImported(self,date):
        try:
            result = DatePushed.objects.get_or_create(date=date)[1]
        except Exception,e:
            print str(e)
        if result==False:
            raise Exception("date already pushed!")

    def getAllImportedDate(self):
        return DatePushed.objects.all()

def syncAppAnnieLink():
    s = IosAppCache()
    c = IosAppRankDb()
    all = s.getAllAppAnnieLink()
    print len(all)
    count = 0
    for k,v in all.items():
        print count
        count+=1
        c.setAppByLink(k,v)

def readAppannieDataToMongo(file):
    #file = "appList2013-02-21"
    with open(file) as f:
        content = f.readlines()
    dateStr = file.split("appList")[1]
    date = datetime.strptime(dateStr, '%Y-%m-%d').date()
    
    for app in content:
        print count
        try:
            newApp = json.loads(app.decode('utf-8'))
            board = newApp["board"]
            appName = newApp["appName"] #unicode(appName,'utf-8')
            appAnnieLink = newApp["appAnnieLink"]
            artist = newApp["artist"]  #unicode(artist,'utf-8')
            artistLink = newApp["artistLink"]
            rank = newApp["rank"] 
            category = newApp["category"] 
            country = newApp["country"]
        except:
            continue
        # find 
        appId = c.getAppByLink(appAnnieLink)
        if appId == None:
            try:
                newApp = IosApp.objects.create(trackName=appName,appAnnieLink=appAnnieLink,artistName=artist,artistLink=artistLink,country=countryCode[country])
            except Exception, e:
                print "create new app error = %s " % str(e)
                continue
            else:
                appId = newApp.id
                s.setAppByLink(appAnnieLink,appId)
                


        categoryId = category_map[category]
        countryId = country_map[country]
        boardId = board_map[board]
        result = s.addDayRank(appId,countryId,categoryId,boardId,rank,dateStr)
        count+=1
    c.pushDateImported(dateStr)


def syncAppToMongo():
    c = IosAppCache()
    s = IosAppRankDb()
    for country in country_map.itervalues():
        for category in category_map.itervalues():
            for board in board_map.itervalues():
                searchKey = "*:%s:%s:%s" % (country,category,board)
                print searchKey
                keys = c.getAllKeysForCond(country,category,board)
                for key in keys:
                    appId = int(key.split(":")[1])
                    result = c.getDayRankByKey(key)
                    for item in result:
                        s.addDayRank(appId,country,category,board,item['rank'],item['date'])
                    #if len(result)< 5 :
                    #    continue
                    #score = calculateMomScore(result)
                    #s.addAppToSet(appId,country,category,board,score)


def readAppannieData2(file):
    #file = "appList2013-02-21"
    with open(file) as f:
        content = f.readlines()
    dateStr = file.split("appList")[1]
    date = datetime.strptime(dateStr, '%Y-%m-%d').date()
    s = IosAppCache()

    for app in content:
        try:
            newApp = json.loads(app.decode('utf-8'))
            board = newApp["board"]
            appName = newApp["appName"] #unicode(appName,'utf-8')
            appAnnieLink = newApp["appAnnieLink"]
            artist = newApp["artist"]  #unicode(artist,'utf-8')
            artistLink = newApp["artistLink"]
            rank = newApp["rank"] 
            category = newApp["category"] 
            country = newApp["country"]
        except:
            continue
        # find 
        appId = s.getAppByLink(appAnnieLink)
        if appId == None:
            try:
                newApp = IosApp.objects.create(trackName=appName,appAnnieLink=appAnnieLink,artistName=artist,artistLink=artistLink,country=countryCode[country])
            except Exception, e:
                print "create new app error = %s " % str(e)
                continue
            else:
                s.setAppByLink(appAnnieLink,newApp.id)
                appId = newApp.id

        categoryId = category_map[category]
        countryId = country_map[country]
        boardId = board_map[board]
        result = s.addDayRank(appId,countryId,categoryId,boardId,rank,dateStr)
    s.pushDateImported(dateStr)


def mapCategoryStr(string):
    if string == "top_typ_0":
        return "Free"
    elif string == "top_typ_1":
        return "Grossing"
    elif string == "top_typ_2":
        return "Paid"
    else:
        return False

def crawleAppAnnieToday():
    date = datetime.today().date()
    dateStr = str( datetime.today().date())
    fd = open("appList"+dateStr, "w")
    s = login()
    
    for country in country_list :
        count = 0
        while count < len(category_list):
            print "getting data for %s at %s for date %s" % (category_list[count],country,str(date))
            try:
                getAppannieOnly(s,country,category_list[count],date,fd)
            except Exception,e:
                print str(e)
                time.sleep(5)
                continue
            else:
                count+=1
                time.sleep(2)
    fd.close()

def getAppannieOnly(s, country,category,date,fd):
    url = 'http://www.appannie.com/top/iphone/%s/%s/' % (country,category)
    r = requests.get(url)
    bf = BeautifulSoup(r.content,convertEntities=BeautifulSoup.HTML_ENTITIES)
    all = x = bf.findAll("tr")
    for item in all:
        rankElm = item.find("td",{"class":"rank"})  
        if rankElm == None:
            continue
        rank = rankElm.text
        apps = item.findAll("span",{"class":"app-name"})
        for app in apps:
            newApp ={}
            board = mapCategoryStr(app.parent["class"].split(" ")[0])
            if board == False:
                print "error!!!!! board map error "
                continue
            try:
                appName = app.a.text
                appAnnieLink=app.a["href"]
                artist = app.parent.find("span",{"class":"app-pub-er"}).a.text
                artistLink = app.parent.find("span",{"class":"app-pub-er"}).a["href"]
            #print "find app %s at category %s  for artist %s and rank is %s " %(appName,category,artist,rank)
            except:
                continue
            newApp["board"] = board
            newApp["appName"] = appName#unicode(appName,'utf-8')
            newApp["appAnnieLink"] = appAnnieLink
            newApp["artist"] = artist #unicode(artist,'utf-8')
            newApp["artistLink"] = artistLink 
            newApp["rank"] = rank
            newApp["category"] = category
            newApp["country"] = country
            res = json.dumps(newApp,ensure_ascii=False)
            fd.write(res.encode('utf-8')+'\n')


def readAppannieData(file):
    #file = "appList2013-02-21"
    with open(file) as f:
        content = f.readlines()
    date = datetime.strptime(file.split("appList")[1], '%Y-%m-%d').date()

    # cache Category obj from db
    appCategoryCache = {}
    allCategory = AppCategory.objects.all()
    for i in allCategory:
        appCategoryCache[i.id]=i
    print "finish cache category"
    
    print "finish cache appannie link"
    # cache iosRank today
    allIosRankTodayCache = {}
    allIosRankToday = IosAppRank.objects.filter(date=date,type='iphone')
    for i in allIosRankToday:
        key = "%s:%s:%s:%s" % (str(i.app.id), str(i.label.id), i.board, i.country)
        allIosRankTodayCache[key] = True
    print "finish cache iosRank today"
    rankList = []
    count = 0 
    idx = 0
    for app in content:
        idx +=1
        print idx
        try:
            newApp = json.loads(app.decode('utf-8'))
            board = newApp["board"]
            appName = newApp["appName"] #unicode(appName,'utf-8')
            appAnnieLink = newApp["appAnnieLink"]
            artist = newApp["artist"]  #unicode(artist,'utf-8')
            artistLink = newApp["artistLink"]
            rank = newApp["rank"] 
            category = newApp["category"] 
            country = newApp["country"]
        except:
            continue
        if iosAppLinkCache.has_key(appAnnieLink):
            appInDB = iosAppLinkCache[appAnnieLink]
        else:
            appInDB = findAppFromApple(appName,artist,appAnnieLink,artistLink,country) #2
        
        if appInDB == False or appInDB == None:
            print "can not get app %s " % appName
            continue
        categoryObj = appCategoryCache[category_map[category]]
        searchKey = "%s:%s:%s:%s" % (str(appInDB.id), str(categoryObj.id), board, country)
        if allIosRankTodayCache.has_key(searchKey):
            print "~~~~~~~~~~~~already have data in db "
        else:
            rankList.append(IosAppRank(app=appInDB,label=categoryObj,rank=int(rank),date=date,board=board,type='iphone',country=country))#hitdb
            #print "$$$$$$$$$$$$$$$$ insert iosRank to rankList  appid is  %s  and category id is %s" % ( str(appInDB.id), str(categoryObj.id) )
            count+=1
        if count == 2000:
            print "creating in to database -------------------------"
            try:
                IosAppRank.objects.bulk_create(rankList)
            except Exception, e:
                print str(e)
                time.sleep(10)
            rankList=[]
            count = 0

def getAppannie(s, country,category,date):
    url = 'http://www.appannie.com/top/iphone/%s/%s/' % (country,category)
    r = s.get(url)
    bf = BeautifulSoup(r.content,convertEntities=BeautifulSoup.HTML_ENTITIES)
    all = bf.findAll("tr")
    for item in all:
        rankElm = item.find("td",{"class":"rank"})  
        if rankElm == None:
            continue
        rank = rankElm.text
        apps = item.findAll("span",{"class":"app-name"})
        for app in apps:
            board = mapCategoryStr(app.parent["class"].split(" ")[0])
            if board == False:
                print "error!!!!! board map error "
                continue
            try:
                appName = app.a.text
                appAnnieLink=app.a["href"]
                artist = app.parent.find("span",{"class":"app-pub-er"}).a.text
                artistLink = app.parent.find("span",{"class":"app-pub-er"}).a["href"]
            #print "find app %s at category %s  for artist %s and rank is %s " %(appName,category,artist,rank)
            except:
                continue
            try:
                appInDB = IosApp.objects.get(appAnnieLink=appAnnieLink)
            except:
                appInDB = findAppFromApple(appName,artist,appAnnieLink,artistLink,country) # 2
            
            if appInDB == False or appInDB == None:
                print "can not get app %s " % appName
                continue
            categoryObj = AppCategory.objects.get(id= category_map[category] )
            try:
                IosAppRank.objects.get(app=appInDB,label=categoryObj,date=date,board=board,type='iphone',country=country)    
            except:    
                try:
                    IosAppRank.objects.create(app=appInDB,
                                              label=categoryObj,
                                              rank=int(rank),
                                              date=date,
                                              board=board,
                                              type='iphone',
                                              country=country)
                    print "create app Rank for %s successfully !!!!!!!!" % appName
                except Exception, e:
                    print "create rank data error %s" % str(e)
            else:
                print "~~~~~~~~~~~~already have data in db "


proxyDict = { 
              "http"  : "123.129.214.155:80", 
              "https" : "200.195.178.42:8080", 
            }

def loopAppNotData():
    #cache = IosAppCache()
    apps = IosApp.objects.filter( Q(trackId = 0),~Q(trackId=-1) )
    for app in apps:
        url = "http://www.appannie.com"+app.appAnnieLink
        r = requests.get(url, proxies=proxyDict)
        bf = BeautifulSoup(r.content,convertEntities=BeautifulSoup.HTML_ENTITIES)
        link = bf.find("div",{"class":"an_switcher"})
        if link == None:
            print "error can not find itunes for %s" % url
            app.trackId = -1
            app.save() 
            continue
        else:
            url = link.li.a["href"]
            trackId = int(url.split("id")[1])
        print "find app %s for trackId %s" % (app.trackName,str(trackId)) 
        icon = bf.find("img",{"itemprop":"image"})["src"]
        app.icon = icon 
        app.trackId = trackId
        app.link = url 
        app.save()
        time.sleep(2)

def getAppsNotFetched():
    apps = IosApp.objects.filter( trackId = 0)
    for item in apps:
        findAppFromApple2(item)

def findAppFromApple2(iosapp):
    try:
        appList = itunes.search(query=iosapp.trackName, media='software')
    except:
        return False
    for app in appList:
        artistName= app.get_artistName()
        trackName = app.get_trackName()
        sellerUrl = app.get_seller_url()
        sellerName= app.get_sellerName()
        if iosapp.artistName == artistName:
            print "!!!!!!!!!!!!in app got it for %s" % trackName
            trackId = app.get_id()
            bundleId = app.get_bundleId()
            artistId = app.get_artistId()
            icon = app.get_icon()
            link = app.get_link()
            primaryGenreId=app.get_primaryGenreId()
            primaryGenreName=app.get_primaryGenreName()

            iosapp.trackId = trackId
            iosapp.bundleId = bundleId
            iosapp.artistId = artistId
            iosapp.icon = icon
            iosapp.link = link 
            iosapp.primaryGenreId = primaryGenreId
            iosapp.primaryGenreName = primaryGenreName
            if sellerUrl != None:
                iosapp.artistUrl = sellerUrl
            try:
                iosapp.save()
            except Exception,e:
                print str(e)


@task()
def getAppRatingAndSave(ios):
    try:
        app = itunes.lookup(ios.trackId)
    except:
        return 
    else:
        avgRating = app.get_avg_rating()
        if avgRating == None: 
            avgRating = 0
        ratingNum = app.get_num_ratings()
        if ratingNum == None:
            ratingNum = 0
        if ratingNum != 0 or avgRating != 0:
            ios.ratingCount = ratingNum
            ios.avgRating  = avgRating
            ios.save()

def findAppFromApple(name,artist,appAnnieLink,artistLink,country):

    try:
        appList = itunes.search(query=name,store=countryCode[country], media='software')
    except:
        return False
    for app in appList:
        artistName= app.get_artistName()
        trackName = app.get_trackName()
        sellerUrl = app.get_seller_url()
        sellerName= app.get_sellerName()
        if artist == artistName:
            print "!!!!!!!!!!!!in app got it for %s" % trackName
            trackId = app.get_id()
            bundleId = app.get_bundleId()
            artistId = app.get_artistId()
            icon = app.get_icon()
            link = app.get_link()
            primaryGenreId=app.get_primaryGenreId()
            primaryGenreName=app.get_primaryGenreName()
            try:
                appInDB = IosApp.objects.get(trackId=trackId)
            except:               
                try:
                    appInDB = IosApp.objects.create(company=matchAppWithComp(sellerUrl),
                                                  trackId=trackId,
                                                  trackName=trackName,
                                                  bundleId=bundleId,
                                                  artistId=artistId,
                                                  artistName=artistName,
                                                  sellerName=sellerName,
                                                  primaryGenreId=primaryGenreId,
                                                  primaryGenreName=primaryGenreName,
                                                  appAnnieLink=appAnnieLink,
                                                  artistLink=artistLink,
                                                  icon=icon,
                                                  link=link
                                                  )
                except Exception, e:
                    print str(e)
                    print "create error "
                    return False
                else:
                    print "create app %s for id %s " % (trackName,str(appInDB.id))
            else:
                if appInDB.appAnnieLink=='':
                    appInDB.appAnnieLink = appAnnieLink
                    appInDB.artistLink = artistLink
                    appInDB.save()
            return appInDB
              


def matchAppWithComp(url):
    try:
        comp = Compant.objects.get(website=url)
    except:
        return None
    else:
        return comp

@task()
def getCompanyApp(company):
    try:
        appList = itunes.search(query=company.name, media='software')
    except:
        company.appFetched = True
        company.save()
        return

    url = trimUrl(company.website)
    count = 0 
    for app in appList:
        if count == 10:
            return
        count+=1
        sellerUrl = trimUrl(app.get_seller_url())
        artistName= app.get_artistName()
        avgRating = app.get_avg_rating()
        if avgRating == None: 
            avgRating = 0
        ratingNum = app.get_num_ratings()
        if ratingNum == None:
            ratingNum = 0
        
        sellerName = app.get_sellerName()
        trackName = app.get_trackName()
        isApp = 0 
        if sellerUrl!=None and sellerUrl.lower() == url.lower()>0:
            print "find sellerUrl %s" % sellerUrl
            isApp+=1
        if artistName!=None and artistName.lower()==company.name.lower():
            print "find artistName %s " % artistName.lower()
            isApp+=1
        if sellerName!=None and sellerName.lower()==company.name.lower():
            print "find sellerName %s " % sellerName.lower()
            isApp+=1 
        if isApp>0:
            print "rating avg %s for number %s " % (avgRating,ratingNum)
            print "find app %s for company %s" % (trackName, company.name)
            trackId = app.get_id()
            bundleId = app.get_bundleId()
            artistId = app.get_artistId()
            icon = app.get_icon()
            link = app.get_link()
            primaryGenreId=app.get_primaryGenreId()
            primaryGenreName=app.get_primaryGenreName()
            try:
                gotApp = IosApp.objects.get(trackId=trackId)
            except:
                try:
                    IosApp.objects.create(company=company,
                                      trackId=trackId,
                                      trackName=trackName,
                                      bundleId=bundleId,
                                      artistId=artistId,
                                      artistName=artistName,
                                      primaryGenreId=primaryGenreId,
                                      primaryGenreName=primaryGenreName,
                                      icon=icon,
                                      link=link,
                                      avgRating=avgRating,
                                      ratingCount=ratingNum
                                      )
                except Exception, e:
                    print str(e)
                    print "create error "
            else:
                if gotApp.company == None:
                    gotApp.company = company
                    gotApp.ratingNum = ratingNum
                    gotApp.avgRating = avgRating
                    gotApp.save()
                    print "linked company %s with app %s " %(company.name,gotApp.trackName)

    company.appFetched = True
    company.save()

def searchCompanyApp():
    allCompany = Company.objects.filter(appFetched = False,cbpermalink__isnull=False)
    for company in allCompany:
        try:
            getCompanyApp(company)
        except:
            print "error"

def getAllAppRankData():
    s = login()
    applist = IosApp.objects.filter(fetched = False)
    for app in applist:
        a = getIosAppRankData(s,app)
        if a !=False:
            app.fetched=True
            app.save()


DOMAIN = 'http://www.appannie.com'

def login():
    s = requests.Session()
    payload = { 'username': APPANNIE_ACCT, 'password': APPANNIE_PASS,'next':'/','remember_user':'on'}
    url = 'https://www.appannie.com/account/login/'
    r1 = s.post(url, data=payload,verify=False)
    return s 

def getIosAppRankData(s,app):
    #s = login()
    #trackName = "Etsy"
    #artistName = "Etsy, Inc."
    search_url = "http://www.appannie.com/search/?q="+app.trackName
    try:
        r = s.get(search_url)
    except:
        return False
    if r.content.count("has been temporarily blocked on our system"):
        return False
    print r.content
    bf = BeautifulSoup(r.content)

    div= bf.findAll("div", {"class":"search_result_details"})
    if len(div) == 0:
    	print "find nothing "
        time.sleep(10)
    	return 
    for item in div:
        try:
            appName = item.h4.a.text
            sellerName = item.h5.find('a').text
            appAnnieAppUrl =  item.h4.a['href']
        except:
            continue
        if sellerName == app.artistName:
            print "find app %s from %s " % (appName, sellerName)
            getAppHistoryData(s,app,appAnnieAppUrl)
            time.sleep(10)


def getLabelObj(label):
    try:
        label = AppCategory.objects.get(label=label)
    except:
        label = AppCategory.objects.create(label=label)
    return label

def getAppHistoryData(s,app,url):
    refer = DOMAIN+url+"ranking/history/"
    #print refer
    url = refer+"chart_data/?d=iphone&c=143441&f=ranks&s=2012-11-15&e=2013-01-24&_c=1"
    #print url 
    headers = {'Referer': refer }
    try:
        r = s.get(url,headers=headers)
    except:
        return 
    print r.content
    if r.content == "[]":
        print "find no data"
        return
    #print type(r.content)
    try:
        response = json.loads(r.content)
    except:
        print "find no data"
        return 
    for item in response:
        label = getLabelObj(item['label'])
        data = item['data']
        if len(data) == 0 : return
        for dayData in data:
            if dayData[1] == None : continue
            date = datetime.fromtimestamp(int(dayData[0])/1000).date()
            #print date
            note = dayData[2]
            try:
                IosAppRank.objects.create(app=app,
                                          label=label,
                                          rank=int(dayData[1]),
                                          date=date,
                                          type='iphone',
                                          country='us',
                                          note=note)
            except Exception, e:
                print "create rank data error %s" % str(e)
        print "save data for %s days" % str(len(data))

from django.db.models import Q
def mergeAppDataToRedis():
    alls = IosAppRank.objects.filter( ~Q(type='1') )
    s = IosAppCache()
    for item in alls:
        if item.board == "":
            boardId = 1
        else:
            boardId = board_map[item.board]
        try:
            s.addDayRank(item.app.id,2,item.label.id,boardId,item.rank,str(item.date))
        except:
            continue
        item.type = "1"
        item.save()



