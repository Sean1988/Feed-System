from company.models import * 
import redis
import simplejson as json
from utils import * 
from datetime import datetime

SESSION_REDIS_HOST = '127.0.0.1'
SESSION_REDIS_PORT = 6379
COMPANY_NAMESPACE = "comp"
SITE_NAMESPACE = "site"


class AlexRankCache:
    def __init__(self):
        self.server = redis.Redis(host='54.235.67.9', port=6379, db=1)
        self.today = str(datetime.today()).split(" ")[0]
    
    def _getSiteKey(self,site):
    	return "%s:%s" %(SITE_NAMESPACE, site.lower())
    
    def _getSiteRankKey(self,website):
    	return "%s:%s:rank" %(SITE_NAMESPACE,website)
    
    def saveSite(self,site,id):
        key = self._getSiteKey(trimUrl(site))
        return self.server.set(key,id)
     
    def addSiteToList(self,website):
    	self.server.sadd("alexasite", website)

    def getAllSite(self):
    	return self.server.smembers("alexasite")

    def addRank(self,website,rank,today):
    	key = self._getSiteRankKey(website)
    	data = {}
    	data["date"] = today
        data["rank"] = rank
        self.addSiteToList(website)
        self.server.rpush(key,json.dumps(data))
    
    def getSiteRank(self,website):
        rankList = self.getRankHistory(website)
        if len(rankList) == 0 :
            return False
        try:    
            lastest = json.loads(rankList[-1])
            return int(lastest['rank'])
        except:
            return False
    
    def getRankHistory(self,website):
        key = self._getSiteRankKey(website)
        return self.server.lrange(key, 0, -1)
    
    def addToBoard(self,website):
    	self.server.zadd("rankBoard", website, 0)

    def syncSite(self):
    	allCompanies = Company.objects.all()
    	for comp in allCompanies:
    		self.saveSite(comp.website,comp.id)
    
    def save(self):
        self.server.bgsave()
    
    def isSiteInDB(self,website):
        pass
                   
class CompanyCache:
    def __init__(self):
        self.server = redis.Redis(host='54.235.67.9', port=6379, db=1)

    def _getCompanyKey(self,company):
        return "%s:%s:%s" % (COMPANY_NAMESPACE ,company.name.lower(), company.id)

    def _getSearchKeyById(self,id):
        return "%s:*:%s" % (COMPANY_NAMESPACE ,str(id))

    def _getSearchKeyByName(self,name):
        return "%s:%s:*" % (COMPANY_NAMESPACE ,name.lower())

    def _getCompanyByKey(self,key):
        result=self.server.keys(key)
        if len(result) == 1:
            info = self.server.get(result[0])
            if info == None:
            	return False
            return json.loads(info)
        else:
            return False
    

    def hasCachedData(self):
    	result = self.server.keys("%s*" % SITE_NAMESPACE)
    	if len(result) == 0:
            return False
        return True

    def getCompanyIdFromSite(self,site):
    	key = self._getSiteKey(site)
    	return self.server.get(key)


    def addCompanyToTag(self,company,tag):
        setKey = "%s:%s" %(tag.id, tag.tagName)
        return self.server.zadd(setKey,company.id,company.smooth)
    
    def getCompanysFromTag(self,tag):
        setKey = "%s:%s" %(tag.id, tag.tagName)
        compList = self.server.zrange(setKey, 0, -1, withscores=True)
        resultList = []
        for item in compList:
            compObj = Object()
            compObj.id = item[0]
            compObj.name =  self.getCompanyName(compObj.id)
            compObj.website = self.getCompanyWebsite(compObj.id)
            compObj.smooth = item[1]
            compObj.hasApp = self.getCompanyHasApp(compObj.id)
            compObj.rank = self.getCompanyRank(compObj.id)
            resultList.append(compObj)
        return resultList    
    #def updateCompanyScore(self,company):


    def getCompanyInfoById(self,id):
        key = self._getSearchKeyById(id)
        return self._getCompanyByKey(key)

    def getCompanyInfoByName(self,name):
        key = self._getSearchKeyByName(name)
        return self._getCompanyByKey(key)

    def cacheCompanyInfo(self,company):
        key = self._getCompanyKey(company)
        info = {}
        info["name"] = company.name
        info["website"] = company.website
        info["hasapp"]= int(company.hasApp)
        info["rank"]= company.rank
        self.saveSite(company.website,company.id)
        return self.server.set(key,json.dumps(info))
    


    def syncByTag(self):
        allTags = Tag.objects.filter(fetched=True)
        for tag in allTags:
            companys = Company.objects.filter(tags=tag)
            for company in companys:
                if company.analysed:
                    print "sync company %s" % company.name
                    #self.addCompanyToTag(company,tag)
                    self.cacheCompanyInfo(company)

     


def cacheCompanyRank():
    alltag = Tag.objects.all()
    c = RankCache()
    for tag in alltag:
        company_array  =  list(Company.objects.filter(tags=tag))
        company_array.sort(key=lambda x: x.smooth, reverse=True)
        for idx,company in enumerate(company_array):
            result = c.setRank(company,tag,idx+1)
            if result ==False:
                print "cannot insert"
            print "insert key success %s:%s" %(company.name,tag.tagName)
    c.save()



class Object(object):
    pass

class RankCache:
    def __init__(self):
        self.server = redis.Redis(host='localhost', port=6379, db=0)
    
    def getRank(self,company,tag):
        key = company.name+":"+tag.tagName
        rank =  self.server.get(key)
        if rank==None:
            return False
        return rank

    def setRank(self,company,tag,rank):
        key = company.name+":"+tag.tagName
        return  self.server.set(key,rank)

    def save(self):
        return self.server.bgsave()
