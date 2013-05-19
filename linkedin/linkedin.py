import httplib2
import time, os
import simplejson as json
import redis
from django.db.models import Q
import requests
from BeautifulSoup import BeautifulSoup
from models import * 
from signl.utils import * 
from company.cache import * 
from company.views import * 
from IPy import IP
from models import * 
from signl.settings import LINKEDIN_ACCT, LINKEDIN_PASS

class LinkedInCache:
    def __init__(self):
        self.server = redis.Redis(host='localhost', port=6379, db=1)
        self.today = str(datetime.today()).split(" ")[0]
    
    def saveLinkedin(self,company_id,data):
        key ="linkedin:%s" % str(company_id)
        self.server.set(key,data)

    def addFollower(self,company_id,follower):
        key = "linkedin:follower"
        self.server.zadd(key,company_id,follower)
    
    def addEmployee(self,company_id,employee):
        key = "linkedin:employee"
        self.server.zadd(key,company_id,employee)

    def getEmployee(self):
        key = "linkedin:employee"
        self.server.zrange(key, 0, -1, withscores=True)

    def getFollower(self):
        key = "linkedin:follower"
        self.server.zrange(key, 0, -1, withscores=True)

    def addId(self,company_id):
        self.server.sadd("linkedin:fetchedId",company_id)




class LinkedIn:
    def __init__(self):
        self.s = login()
        #self.cache = LinkedInCache()
    
    def getLinkedInCompany(self,id):
  
        url = "http://www.linkedin.com/company/"+ str(id)
        r = requests.get(url)
        bf = BeautifulSoup(r.content)

        error = bf.find("div", {"class":"alert error"})
        if error != None:
            return None,None,None

        basicInfo =  bf.find("div", {"class":"basic-info"})
          
        if basicInfo == None or basicInfo.find("a") ==None:
            return None,None,None

        fullSite = basicInfo.find("a").text
        website = trimUrl(basicInfo.find("a").text)
        name = bf.find("h1").text
        row = "%s*%s*%s" %(str(id),name,fullSite)
        return id, name, website
        print "find id = %s company name = %s , %s" % (str(id), name,website)
    

    def getLinkedinOtherInfo(self,content,dataDict):
        try:
            adr = content.find("p",{"class":"adr"})
            children = content.findChildren()
            adrStr = ""
            for child in children:
                adrStr += child.text+' '
            city = content.find("span",{"class":"locality"}).text
            postcode = content.find("span",{"class":"postal-code"}).text
            region = content.find("span",{"class":"region"}).text
        except:
            pass
        else:
            dataDict["adrStr"]=adrStr
            dataDict["city"]=city
            dataDict["postcode"]=postcode
            dataDict["region"]=region

        type = content.find("li",{"class":"type"})
        if type != None:
            type=type.p.text
            dataDict["type"]=type
        industry = content.find("li",{"class":"industry"})
        if industry != None:
            industry= industry.p.text
            dataDict["industry"]=industry
        founded = content.find("li",{"class":"founded"})
        if founded!=None:
            founded=founded.p.text
            dataDict["founded"] = founded
        return dataDict


    def isCompanyNotFoundError(self, error):
        try:
            msg = error.p.strong.text
            if msg == "We're sorry, but the company you are looking for is not active.":
                print "find company not found error !!"
                return True
            else:
                return False
        except:
            return False

    def getLinkedinData(self,id):
        url = "http://www.linkedin.com/company/"+ str(id)
        r = self.s.get(url)
        bf = BeautifulSoup(r.content)
        error = bf.find("div", {"class":"alert error"})
        dataDict = {}
        dataDict = self.getLinkedinOtherInfo(bf,dataDict)
        follower = None
        if error != None:
            print "getting error !!!!!"
            if self.isCompanyNotFoundError(error):
                return False
            return False
        try:
            follower= bf.find("p",{"class":"followers-count"}).a.strong.text
            empUl = bf.find("ul",{"class":"stats"})
            employee = None
            empLi = empUl.findAll("li")
            for li in empLi:
                if li.span.text == "Employees on LinkedIn" or li.span.text == "Employee on LinkedIn"  :
                    employee = li.a.text
        except:
            if follower != None and is_number(follower) and employee == None:
                employee = 0
            else:
                print "getting error !!!!! for linkedin id %s " % id
                return False
        print "get company id %s , follower %s employee %s" %(str(id),follower,employee)
        
        if employee == None:
            return False
        follower=int(follower.replace(',',''))
        if employee != 0:
            employee=int(employee.replace(',',''))
        return {'follower':follower, 'employee':employee}
    
    def printError(self,error):
        text_file = open("error.html", "w")
        text_file.write(error)
        text_file.close()


    def searchCompany(self,comp):
        site = trimUrl(comp.website)
        #rank = getGlobalRank(site)
        print "company name ===========%s" % comp.website
        rank = comp.rank
        #print "get site %s  rank which is %s" % (site, str(rank))
        if type(rank) == int and rank <= 0:
            return 4
        name = comp.name
        searchUrl = "http://www.linkedin.com/csearch/results?type=companies&keywords=%s&pplSearchOrigin=GLHD&pageKey=member-home" % site
        r = self.s.get(searchUrl)
        #print r.content
        bf = BeautifulSoup(r.content)
        title = bf.find("title")
        print title.text
        if title.text == "403: Forbidden" or title.text == "Restricted Action | LinkedIn":
            print "forbidden"
            return 2
        result = bf.findAll("a",{"title":"View Company Details"})
        if len(result) == 0:
            comp.linkedinFetched = True
            comp.save()
            return 
        for item in result:
            id = item['href'].split('/')[2]
            print "2323"
            id,name,website = self.getLinkedInCompany(id)
            print "sss"
            if site == website: 
                time.sleep(5) 
                comp.linkedInId = int(id)
                saveEmployee(self,int(id),comp)
                comp.linkedinFetched = True
                comp.save()
                print "find linkedin %s for site %s id : %s" % (name,website,comp.linkedInId)
                return
        comp.linkedinFetched = True
        comp.save()
            #if name.lower() == item.text.lower():
            #    print "find linkedin %s for site %s!!!! id = %s " % (site,item.text,item['data-li-track-id'])
            #    comp.linkedInId = int(item['data-li-track-id'])
            #    comp.save()

def grabIP():
    url = "http://spys.ru/en/"
    page = requests.get(url)
    bf = BeautifulSoup(page.content)
    ipList = bf.findAll("font", {"class":"spy14"})
    proxy_list = {}

    for ip in ipList:
        try:
            proxy_address = ip.text.split("document.w")[0]
            try:
                IP(proxy_address)
                #need to save to a dictionary
                proxy_list[proxy_address] = proxy_address
            except:
                #not a valid IP address
                pass
        except:
            pass
            # Notification needs

from datetime import date
def getLinkedinEmployee():
    allcomp = Company.objects.filter(linkedInId__gt = 0, rank__lt=300000,linkedinFetched=False)
    a = LinkedIn()
    for item in allcomp:
        linkedinId = item.linkedInId
        saveEmployee(a,linkedinId,item)
        item.linkedinFetched = True
        item.save() 
        time.sleep(10)
            
def saveEmployee(a,linkedinId,item):
    result = a.getLinkedinData(linkedinId)
    if result != False :
        follower = result['follower']
        employee = result['employee']
        if employee == None:
            employee = 0
        print "save linkedin follower = %s employee = %s for comp %s " %(follower,employee,item.name)
        try:
            LinkedinData.objects.create(company=item,follower=follower,employee=employee,date=date.today())
        except Exception,e:
            print str(e)   

def getAllLinkedinData():
    s = LinkedIn()
    fd = open('linkedinData','w')
    all = LinkedinProfile.objects.filter(linkedinId__lte = 100000,linkedinId__gt=6360)
    for link in all:
        print "!!!!!!!!!!!!!!getting  linkedin id = %s" % str(link.linkedinId)
        r = s.getLinkedinData(link.linkedinId,fd)
        time.sleep(4)
        if r == False:
            break
    fd.close()

def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def output():
    all = list(LinkedinProfile.objects.all().values_list("linkedinId",flat=True))
    length = len(all)
    chs = chunks(all, 180000)
    for idx, seg in enumerate(chs):
        fileName = "idData_"+ str(idx)
        fd = open(fileName,'w')
        for item in seg:
            fd.write(str(item)+'\n')
        fd.close


def input():
    with open('200000') as f:
        content = f.readlines()
    ids= []
    for item in content:
        ids.append(int(item))
    return ids

def getAllLinkedin():
    all = Company.objects.filter(rank__lte=1000000,rank__gte=800000,linkedInId=0,linkedinFetched=False)
    a = LinkedIn()
    for item in all:
        r = a.searchCompany(item)
        if r == 2:
            return
        time.sleep(15)

def readLinkedin2(file):
    filestr = "/home/ubuntu/trends/trends/%s" % file
    a = LinkedinProfile.objects.values_list('linkedinId',flat=True)
    with open(filestr) as f:
        content = f.readlines()
    id_list=[]
    id_map={}
    for item in content:
        data = item.split("*")
        try:
            id = data[0]
            name = data[1]
            website = data[2]
            url = trimUrl(website)
        except:
            continue
        if url == "":
            continue
        id_list.append(int(id))
        id_map[int(id)]=[website,name]
    dif = list(set(id_list)-set(a))
    print "find %s difference " % str(len(dif))
    for i in dif:
        print "%s -- %s--  %s " % ( str(i), id_map[i][1], id_map[i][0] )
    return

    obj_list = []
    count = 0 
    for i in dif:
        count+=1
        try:
            obj_list.append(LinkedinProfile(linkedinId = i, name=id_map[i][1],website=id_map[i][0]))
        except:
            pass
        if count == 2000:
            LinkedinProfile.objects.bulk_create(obj_list)
            obj_list = []
            count = 0 
     #   obj_list.append(LinkedinProfile(linkedinId = i, name=id_map[i][1],website=id_map[i][0]))
    #LinkedinProfile.objects.bulk_create(obj_list)

import redis        
def matchLinkedinWithComp():
    allComp = Company.objects.filter(linkedInId=0)
    server = redis.Redis(host='localhost', port=6379, db=2)
    #allLinkedin = LinkedinProfile.objects.all()
    count = 0
    for item in allComp:
        print item.id
        url = trimUrl(item.website)
        linkedinId = server.hget("linkedin",url)
        if linkedinId != None:
            item.linkedInId = int(linkedinId)
            item.save()
            count +=1
    print "find %s matchs " % str(count)   

def readLinkedin(file):
    filestr = "/home/ubuntu/trends/trends/%s" % file
    with open(filestr) as f:
        content = f.readlines()
    urlMapper = {}
    allComp = Company.objects.all()
    for i in allComp:
        site = trimUrl(i.website)    
        urlMapper[site]=i.id
    print "save mapper finished"
    start = False
    for item in content:
        data = item.split("*")
        try:
            id = data[0]
            name = data[1]
            print "reading id = %s" % id
            if int(id) == 953558:
                start = True
            website = data[2]
            url = trimUrl(website)
        except:
            continue
        if start == False:
            continue
        try:
            LinkedinProfile.objects.get(linkedinId=int(id))
        except:
            try:
                linkedinprofile = LinkedinProfile.objects.create(linkedinId = int(id),name = name,website = website)
            except:
                print "create error"
            print "successfully create linkedin profile"   
        continue
        try:
            compId = urlMapper[url]
        except:
            #print "not find for url %s" % url 
            continue
        else:
            try:
                company = Company.objects.get(id=compId)
            except:
                print "can not get company for id =%s" % compId
                continue
            print "find company %s in linkedin " % name
            company.linkedInId = id
            if company.twitter == "s":
                company.name = name
            try:
                company.save()
            except:
                continue

def scanLinkedinCompany():
    count = 1203763
    fd = open('linkedinScan6.txt','a')
    x = LinkedIn()
    while count < 1300000:
        print "getting compnay id  = %s" % str(count)
        try:
            x.getLinkedInCompany(fd,count)
        except Exception,e :
            print str(e)
        count +=1
    fd.close()

def getData():
    url = 'https://www.linkedin.com/uas/login?goback=&trk=hb_signin'
    r = requests.get(url)
    bf = BeautifulSoup(r.content)
    csrf= bf.find("input", {"name":"csrfToken"})
    csrf_val =  csrf['value']
    sourceAlias= bf.find("input", {"name":"sourceAlias"})
    sourceAlias_val =  sourceAlias['value']
    return csrf_val,sourceAlias_val


def login():
    s = requests.Session()
    csrf_val,sourceAlias_val = getData()
    payload = { 'csrfToken':csrf_val,'isJsEnabled':'true','session_key': LINKEDIN_ACCT, 'session_password': LINKEDIN_PASS,'session_redirect':'','signin':'Sign In','sourceAlias':sourceAlias_val}
    url = 'https://www.linkedin.com/uas/login-submit'
    r = s.post(url, data=payload)
    print "logged in "
    text_file = open("3.html", "w")
    text_file.write(r.content)
    text_file.close()
    return s 

from random import randint
def applyApp(s):
    r2 = s.get("https://www.linkedin.com/secure/developer?newapp=")
    bf = BeautifulSoup(r2.content)
    csrf= bf.find("input", {"name":"csrfToken"})
    csrf_val =  csrf['value']
    payload = { 'acc_id':'-1:New Company','accept_term': 'accept_term'}
    payload['admin_ids'] =''
    payload['admin_names'] =''
    payload['agr_lc'] =''
    payload['app_des'] ='sdfasdfasdf'
    payload['app_name'] ='sss' +str(randint(2,9))
    payload['app_url'] ='adasd.com'
    payload['app_use'] ='communications'
    payload['bus_e'] =''
    payload['bus_p'] =''
    payload['compnay_name'] ='asdasd'+ str(randint(2,9))
    payload['createapp'] ='Add Application'
    payload['csrfToken'] =csrf_val #!!!
    payload['current-user-developer'] ='current-user-developer'
    payload['dev_e'] ='asasdf@sd.com'
    payload['dev_ids'] =''
    payload['dev_names'] =''
    payload['dev_ids'] =''
    payload['dev_p'] ='asdfasdf'
    payload['int_url'] =''
    payload['live_st'] ='development'
    payload['logo'] =''
    payload['origin_url'] =''
    payload['red_url'] =''
    payload['logo'] =''
    url = "https://www.linkedin.com/secure/developer"
    re = s.post(url, data=payload)
    bf2 = BeautifulSoup(re.content)
    #text_file = open("Output4.html", "w")
    #text_file.write(re.content)
    #text_file.close()
    data = bf2.findAll('p')
    
    APIKey = data[3].text
    SecretKey = data[4].text
    UserToken = data[5].text
    UserSecret = data[6].text
    print "get new API key %s" % APIKey
    return  APIKey, SecretKey ,UserToken ,UserSecret



