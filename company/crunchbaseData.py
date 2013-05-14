from company.crunchbase import * 
from company.models import * 
from signl.utils import * 
import redis
import xlrd

class CrunchTagCache:
    def __init__(self):
        self.server = redis.Redis(host='localhost', port=6379, db=1)

    def saveTag(self,tagName,mappedId):
        return self.server.set("crunchTag:%s" % tagName, mappedId)

    def getAllTags(self):
        tags = self.server.keys("crunchTag:*");
        tags_array = []
        for tag in tags:
            tag_str = tag.split(":")[1]
            tags_array.append(tag_str)
    
        return tags_array
        #text_file = open("Output.html", "w")
        #text_file.write(r.content)
        #text_file.close()
        #print tags_array
    def printALTags(self):
        alltags = Tag.objects.all()
        alltagsArray = []
        for item in alltags:
            alltagsArray.append(item.tagName)
        tag_file = open("altags.txt", "w")
        tag_file.write(str(alltagsArray))
        tag_file.close()


    def processTag(self):
        #ALTags = Tag.objects.all()
        crunchTags = self.getAllTags()
        unRelatedTag = []
        relatedTag  = []
        for tag in crunchTags:
            try:
                obj = Tag.objects.get(tagName=tag)
            except:
                unRelatedTag.append(tag)
            else:
                self.saveTag(tag,obj.id)
                relatedTag.append(tag)
        tag_file = open("unrelatedTag.txt", "w")
        tag_file.write(str(unRelatedTag))
        tag_file.close()
        tag_file2 = open("relatedTag.txt", "w")
        tag_file2.write(str(relatedTag))
        tag_file2.close()

    def addCompany(self,companyName):
        return self.server.sadd("companyTemp", companyName)
    
    def removeCompany(self,companyName):
        return self.server.srem("companyTemp", companyName)
    
    def getAllCompanies(self):
        return self.server.smembers("companyTemp")

    def gotCompanyFromCB(self,id):
        return self.server.sadd("companyAtCB", id)

class CbTagMap:
    def __init__(self):
        self.server = redis.Redis(host='localhost', port=6379, db=2)

    def saveTagMap(self,tagName,mappedStr):
        return self.server.set("crunchTag:%s" % tagName, mappedStr)

    def getTagMap(self,tagName):
        return self.server.get("crunchTag:%s" % tagName)

    def getAllTagMap(self):
        return self.server.keys("crunchTag:*")

    def save(self):
        return self.server.bgsave()

def storetags():
    wb = xlrd.open_workbook('tag.xls')
    sh = wb.sheet_by_index(0)
    tagMap = CbTagMap()
    for rownum in range(sh.nrows):
        data = sh.row_values(rownum)
        #print sh.row_values(rownum)
        cbTag = data[1].replace(" ", "").replace("'", "")
        print cbTag
        agTag1 = data[2]
        if agTag1 == 'x':
            continue
        else:
            agTagList = []
            for i in range(2,4):
                if data[i] != '':
                    agTagList.append(data[i])
            aTag = ":".join(agTagList)
            result = tagMap.saveTagMap(cbTag,aTag)
    tagMap.save()

def tagAllCBCompany():
    tagMap = CbTagMap()
    allCompany = Company.objects.filter(cbpermalink__isnull=False)
    cb = crunchbase('zmjsk6dn8kmry4e443yfs6u6')
    last = False
    count = 0
    for company in allCompany:
        if company.name == 'lilitab':
            last = True
        if last == False:
            count+=1
            print count
            continue    
        try:
            companyData = cb.getCompanyData(company.cbpermalink)
        except:
            print "Can not get compnay %s " % company.cbpermalink
            continue
        tagListStr = companyData["tag_list"]
        if tagListStr ==None:
            continue

        tagList = tagListStr.split(", ")
        print "got company data %s form crunchbase and tag list %s" %(company.cbpermalink,tagListStr)
        for tag in tagList:
            tagStr = tagMap.getTagMap(tag)
            if tagStr == None:
                continue
            mappedList = tagMap.getTagMap(tag).split(":")
            for agtag in mappedList:
                try:
                    newTag = Tag.objects.get(tagName = agtag )
                except:
                    print "can not get tag from database for tagname %s" % agtag
                    continue
                company.tags.add(newTag)
                company.save()
                print "successfully add tag %s to company %s" % (newTag.tagName, company.name)
                
  
from company.tools import extractAmount                
from datetime import date
import re
def getCrunchBaseFunding():
    cb = crunchbase('zmjsk6dn8kmry4e443yfs6u6')
    allCompany = Company.objects.filter(Q(cbpermalink__isnull=False),~Q(appleStore='s'))
    for company in allCompany:
        try:
            companyData = cb.getCompanyData(company.cbpermalink)
            print company.id, company.name, company.cbpermalink
        except Exception,e:
            print str(e)
            company.appleStore = 's'
            company.save()
            continue
        if companyData['total_money_raised'] !=None:
            company.totalFunding = int(extractAmount(companyData['total_money_raised']))

        if companyData['twitter_username'] !=None:
            company.twitter= companyData['twitter_username']  

        if companyData['email_address'] !=None:
            company.email= companyData['email_address']

        if companyData['phone_number'] !=None:
            company.phoneNumber = companyData['phone_number']
        
        if companyData['overview'] !=None:
            company.overview = re.sub(r'[\\]', r'\\', companyData['overview'])
            

        print "total is : %s" % company.totalFunding

        if companyData['funding_rounds'] != None:
            sumFunding = 0
            for fund in companyData['funding_rounds'] :
                round_code = fund["round_code"]

                if fund["raised_amount"] == None:
                    raised_amount = 0
                else:
                    raised_amount = fund["raised_amount"]
                if fund['raised_currency_code'] is None:
                    currency_code = "USD"
                else:
                    currency_code = fund['raised_currency_code']

                funded_year = fund['funded_year']
                if fund['funded_month'] is None:
                    funded_month = 1
                else:
                    funded_month = fund['funded_month']
                if fund['funded_day'] is None:
                    funded_day = 1
                else:
                    funded_day = fund['funded_day']

                try:
                    fundedDate = date(int(funded_year),int(funded_month),int(funded_day))
                except:
                    print "Error date can not found !!!"
                    print "%s : %s : %s " % (funded_year,funded_month,funded_day ) 
                    continue
                try:
                    getCreated = Funding.objects.get_or_create(company=company,roundCode=round_code,raisedAmount=int(raised_amount),date=fundedDate,currency=currency_code)
                except Exception,e:
                    print str(e)
                    print "error"
                else:
                    if getCreated[1]:
                        print "create a funding successfull!!"
#                    else:
#                        print "funding already in database."

                    sumFunding += int(extractAmount(long(getCreated[0].raisedAmount), getCreated[0].currency))
 
            # Happen when companyData['total_money_raised'] == None
            if company.totalFunding == '0':
                print "total new funding is: " + sumFunding
                company.totalFunding = sumFunding
       
        try:
            company.appleStore="s"
            company.save()
        except:
            print "error"

def getCrunchBaseCompany():
    allCompany = Company.objects.all()
    allUrl = []
    idMap = {}
    for company in allCompany:
        url = trimUrl(company.website)
        if url != None:
            allUrl.append(url)
            idMap[url] = company.id
    
    print "finish get company data!!!!!"
    cb = crunchbase('zmjsk6dn8kmry4e443yfs6u6')
    allList = cb.listCompanies()
    for item in allList:
        name = item["name"]
        permalink = item["permalink"]
        try:
            Company.objects.get(cbpermalink=permalink)
            print "already in db !!!!!"
        except:
            try:
                companyData = cb.getCompanyData(permalink)
            except:
                print "Can not get compnay %s " % permalink
                continue
            homepage_url = companyData["homepage_url"]
            if homepage_url == None:
                continue
            url = trimUrl(homepage_url)
            print url 
            try:
                company_id = idMap[url]
            except: # not in db 
                try:
                    Company.objects.create(cbpermalink=permalink,name=name,website=homepage_url)
                    print "create company in db website = %s" % homepage_url
                except Exception,e:
                    print "can not create company from cb : %s" %str(e)
            else:
                print "find compnany in db id =%s " % str(company_id)
                comp = Company.objects.get(id=company_id)
                comp.cbpermalink = permalink
                comp.save()
            print "-------------------"





def tagAllCompetitor():
    cb = crunchbase('zmjsk6dn8kmry4e443yfs6u6')
    s = CrunchTagCache()
    allCompany = Company.objects.all()
    tag_list = []
    for item in allCompany:
        try:
            cbData = cb.getCompanyData(item.name)
        except:
            #print "not find company %s in crunchbase" % item.name
            continue
        else:
            tagListStr = cbData["tag_list"]
            if tagListStr ==None:
                continue
            tagList = tagListStr.split(", ")
            for item in tagList:
                if item in tag_list:
                    continue
                else:
                    s.saveTag(item,0)
                    tag_list.append(item)
            print tagList
    print "!!!!!!!!!!!!!!!!"
    print tag_list
            #print str(cb)
            #if len(competitorList)==0:
            #    continue
            #for competitor in competitorList:
            #    name = competitor["competitor"]["name"]
            #    try:
            #        company = Company.objects.get(name=name)
            #    except:
            #        print "no company in db"
            #        # search angel list again
            #    else:

#   find app MacGyver Emergency Tricks Database - All the recipes from every episode of the series from Giacomo Balli                 
