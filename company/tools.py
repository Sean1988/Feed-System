ACCESS_ID = "AKIAJSAJL6FSHMUIXBTQ"
SECRET_ACCESS_KEY = "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"
TOKEN = "15ff47ff8a032a5a3c2c27f4f4a537ae"


TOKEN_COUNT= 0
TOKEN_LIST=["15ff47ff8a032a5a3c2c27f4f4a537ae",
            "3ba231771c797fa2ae134c4e28340e25",
            "d816f44193aaf7f9ed7ce797c24a1619",
            "41e3265fdb77f5bd87bc25e0b8a5291a",
            "7a9c039613c9b19191b1da487874a90a"]

import datetime as dt
from collections import deque
from itertools import tee, islice, izip
from company.models import * 
from web.models import * 
from django.db.models import Q
#from openpyxl.cell import get_column_letter
#from openpyxl.reader.excel import load_workbook
import simplejson as json

cp1252 = {
    # from http://www.microsoft.com/typography/unicode/1252.htm
    u"\u20AC": u"\x80", # EURO SIGN
    u"\u201A": u"\x82", # SINGLE LOW-9 QUOTATION MARK
    u"\u0192": u"\x83", # LATIN SMALL LETTER F WITH HOOK
    u"\u201E": u"\x84", # DOUBLE LOW-9 QUOTATION MARK
    u"\u2026": u"\x85", # HORIZONTAL ELLIPSIS
    u"\u2020": u"\x86", # DAGGER
    u"\u2021": u"\x87", # DOUBLE DAGGER
    u"\u02C6": u"\x88", # MODIFIER LETTER CIRCUMFLEX ACCENT
    u"\u2030": u"\x89", # PER MILLE SIGN
    u"\u0160": u"\x8A", # LATIN CAPITAL LETTER S WITH CARON
    u"\u2039": u"\x8B", # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    u"\u0152": u"\x8C", # LATIN CAPITAL LIGATURE OE
    u"\u017D": u"\x8E", # LATIN CAPITAL LETTER Z WITH CARON
    u"\u2018": u"\x91", # LEFT SINGLE QUOTATION MARK
    u"\u2019": u"\x92", # RIGHT SINGLE QUOTATION MARK
    u"\u201C": u"\x93", # LEFT DOUBLE QUOTATION MARK
    u"\u201D": u"\x94", # RIGHT DOUBLE QUOTATION MARK
    u"\u2022": u"\x95", # BULLET
    u"\u2013": u"\x96", # EN DASH
    u"\u2014": u"\x97", # EM DASH
    u"\u02DC": u"\x98", # SMALL TILDE
    u"\u2122": u"\x99", # TRADE MARK SIGN
    u"\u0161": u"\x9A", # LATIN SMALL LETTER S WITH CARON
    u"\u203A": u"\x9B", # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    u"\u0153": u"\x9C", # LATIN SMALL LIGATURE OE
    u"\u017E": u"\x9E", # LATIN SMALL LETTER Z WITH CARON
    u"\u0178": u"\x9F", # LATIN CAPITAL LETTER Y WITH DIAERESIS
}

def retrieveFundingCB():
    # Jimmy's API Key
    api_key = '4s8vxm78zj4bb9969wfxuqcg'
    cbCompany = Company.objects.filter(cbpermalink='tracks')
#    cbCompany = Company.objects.filter(cbpermalink__isnull=True)
    for company in cbCompany:
        address = 'http://api.crunchbase.com/v/1/company/%s.js?api_key=%s' % (company.cbpermalink, api_key)
        cbDataGet = requests.get(address)
        cbDataJson = json.loads(cbDataGet.text)
        cbDataFunding = extractAmount(cbDataJson['total_money_raised'])

        # Update old funding info
        if cbDataFunding != company.totalMoneyRaised:
            company.totalMoneyRaised = cbDataFunding;
            company.save()
        # total_funding is empty, but funding info exists
        elif cbDataJson['total_money_raised'] == '':
            for funding in cbDataJson['funding_rounds']:
                if funding['raised_amount'] is None:
                    raisedAmount = 0
                else:
                    raisedAmount = funding['raised_amount']
                # Check funding in DB
                try:
                    existFund = Funding.objects.get(
                        company_id=company.id,
                        roundCode=funding['round_code'], 
                        raisedAmount=raisedAmount, 
                        currency=funding['raised_currency_code'],
                        date=funding)
                    if existFund is None:
                        Funding.objects.create(
                            company_id=company.id,
                            roundCode=funding['round_code'], 
                            raisedAmount=raisedAmount, 
                            currency=funding['raised_currency_code'],
                            date=funding)

                except:
                    pass

# Helper function for retrieveFundingCB 
def extractAmount(data, currency=""):
    currency_dict ={
        'USD' : 1.0,
        'CAD' : 1.0,
        'JPY' : 0.01,
        'EUR' : 1.28,
        'GBP' : 1.51,
        'NIS' : 0.27,
        'SEK' : 0.27,
    }
    multiplier = 1

#    print data, currency, type(data)
# -------------------------------------
# Calculating from Funding rounds data
# -------------------------------------
    if isinstance(data, long):
        try:
            multiplier = currency_dict[str(currency)]
#            print "data is " + str(data)
#            print "multiplier is " + str(multiplier)
            return data * multiplier
        except Exception,e:
            print str(e)

    amount = 0
    B = 1000000000
    M = 1000000
    k = 1000
    # Get M or B 
    if data[-1] == "M":
        data = data[:-1]
        multiplier *= M
    elif data[-1] == "B":
        data = data[:-1]
        multiplier *= B
    elif data[-1] == "k":
        data = data[:-1]
        multiplier *= k
# --------------------------------
# Translating Total Raised Amount
# --------------------------------
    if isinstance(data, unicode):
        
        temp = data.encode('unicode-escape')
#        print "this is temp: " + temp
#        print type(temp)
#        print len(temp)

        # extract currency factor
        # JPY Japanese Yen \u00a5
        if "\\xa5" in temp:
            amount = float(temp[4:])
            multiplier *= 0.01
        # EUR Euro
        elif "\\u20ac" in temp:
            amount = float(temp[6:])
            multiplier *= 1.28
        # GBP British Pound
        elif "\\xa3" in temp:
            amount = float(temp[4:])
            multiplier *= 1.51
        # NIS Israeli New Sheqel 
        elif "\\u20aa" in temp:
            amount = float(temp[6:])
            multiplier *= 0.27
        else:
            print "new currency found " + data
    elif isinstance(data, str):
        if "$" in data:
            # CAD 
            if "C$" in data:
                amount = float(data[2:])
            # USD
            else:
                amount = float(data[1:])
            multiplier *= 1
        # SEK Swedish Krona
        elif "kr" in data:
            amount = float(data[2:])
            multiplier *= 0.27

#    print "amount is " + str(amount)
#    print "multiplier is " + str(multiplier)

    return amount * multiplier


def markCompanyDefaultTag():
    allComp = Company.objects.filter(~Q(tags=None))
    server = redis.Redis(host='localhost', port=6379, db=5)
    for item in allComp:
        print item.id
        if not item.tags.exists():
            continue
        else:
            blastoff_tag = []
            for tag in item.tags.all():
                if tag.isBlastoff:
                    blastoff_tag.append(tag)
            if len(blastoff_tag) == 0:
                continue
            elif len(blastoff_tag) == 1:
                item.defaultTag = blastoff_tag[0]
                item.save()
                print "get default tag %s for company %s" %(blastoff_tag[0].tagName,item.name)
            else:
                blastoff_tag.sort(key=lambda x: x.companyNum)
                item.defaultTag = blastoff_tag[0]
                item.save()
                print "get default tag %s for company %s" %(blastoff_tag[0].tagName,item.name)


# getting highest and lowest momemtum and convert all companies
# to scale -100% to 100%
def scaleCompanySmooth():
    maxMomemtum_company = Company.objects.order_by('smooth')[0]
    minMomemtum_company = maxMomemtum_company.reverse()[0]
    maxMomemtum = maxMomemtum_company.smooth
    minMomemtum = minMomemtum_company.smooth
    # declare constant
    c = 200/(maxMomemtum - minMomemtum)
    # scale all number from -100 to 100
    for company in Company.objects.all():
        smooth = (company.smooth - minMomemtum) * c - 100
        company.smooth = smooth

def saveAllCompanyRank():
    allCompany = Company.objects.filter(rank= 999999)
    for company in allCompany:
        site = trimUrl(company.website)
        rank = getGlobalRank(site)
        if rank :
            print "get company rank %s is %s" %(company.name,str(rank))
            company.rank = rank 
            company.save()


def detectJustLaunchedSite():
    allCompany = Company.objects.filter(analysed=True)
    start = False
    for company in allCompany:
        print company.id
        if company.id == 170242:
            start = True
        if start == False:
            continue
        dataArray = AlexaData.objects.filter(company = company).order_by('date')
        count = 0 
        for day in dataArray:
            if day.reach == 0:
                count+=1
                if count >=1:
                    company.justLaunched = True
                    company.save()
                    
                    break

def getTagById(id):
    url = "https://api.angel.co/1/tags/"+str(id)
    payload = { 'access_token': TOKEN}
    response = requests.get(url,data=payload)
    data = json.loads(response.text)

    if data.has_key("error"):
        if data["error"] == "over_limit":
            print "over limit"
            return 2
        print "error!!!!!!!!!!!"
        print data
        return False
    else: 
        if data.has_key("id") and is_number(data["id"]):
            tagId = data["id"]
            tagType = data["tag_type"]
            tagName = data["name"]
        else:
            return False
        try:
            tag = Tag.objects.get(tagId = tagId)
        except:
            tag = Tag.objects.create(tagId = int(tagId),tagName = tagName,tagType=tagType)


def crawlerTags():
    i = 1
    while i < 5000:
        a = getTagById(i)
        if a == 2:
            time.sleep(200)
            continue
        i+=1

def crawlerAllTags():
    allTags = Tag.objects.filter(fetched = False)
    for item in allTags:
        print "getting tag %s" % item.tagName
        array = getCompanysFromTag(item)
        if len(array) != 0 :
            print "tag array is 0 "
            item.fetched = True
            item.save()

def crawlerAllCompanyAlexaData():
    allCompany = Company.objects.filter(fetched = False)
    for company in allCompany:
        data = fetchHistoricalData( company )
        if data == False: 
            continue 

def crawlerStartup(init):
    i = init
    global TOKEN
    while i < 157000:
        #print i 
        r = getStartupById(i)
        if r ==2:
            TOKEN = getNewToken()
            continue
        i+=1
def getStartupById(id,tag=False):
    print id
    try:
        company = Company.objects.get(companyId=id)
        print "company in database %s" % company.name
    except:
        url = "https://api.angel.co/1/startups/"+str(id)
        payload = { 'access_token': TOKEN}
        response = requests.get(url,data=payload)
        data = json.loads(response.text)
        print "company not in DB calling angellist"
        if data.has_key("error") and data["error"] == "over_limit":
            print "get company info over limit"
            return 2
        if data.has_key("success") or data["hidden"]== True :
            print "hidden true return fasle" 
            return False
        else:
            if data.has_key("company_url") and data["company_url"] == None:
                print "compny url none" 
                return False
            if data.has_key("markets") and len(data["markets"]) > 0:
               saveTag(data["markets"])
            if urlBlackList(data["name"],data["company_url"]): 
                print "compny url blacklist" 
                return False
            print data["name"]
            print data["company_url"]
            try:
                company = Company.objects.create(companyId=id, name = str(data["name"]), website=str(data["company_url"]))
            except:
                print "create error " 
                return False

    if tag != False:
        company.tags.add(tag)
        company.save()
    return company
  
def getStartupById2(id):
    url = "https://api.angel.co/1/startups/"+str(id)
    response = requests.get(url)
    data = json.loads(response.text)
    if data.has_key("success") or data["hidden"]== True :    
        return False
    else:
        if data.has_key("company_url") and data["company_url"] == None:
            return False
        try:
            company = Company.objects.create(companyId=id, name = data["name"], website=data["company_url"])
        except:
            print "create error "
        return True#{ "company_url" : data["company_url"], "name": data["name"]}

def getNewToken():
    global TOKEN_COUNT
    global TOKEN_LIST
    index = TOKEN_COUNT
    TOKEN_COUNT+=1
    if TOKEN_COUNT > 4:
       TOKEN_COUNT =0
    return TOKEN_LIST[index]

def processStartupsData(startup_array,name):
    company_array= []
    data_array= []
    for company in startup_array:
        data = fetchHistoricalData( company )
        if data == False: 
            continue
        if name!=None and data.name == name :
            data.isTarget= True                   
        company_array.append(data)

    company_array.sort(key=lambda x: x.smooth, reverse=True)
    
    return company_array


def getStartupByIdFromAngel(id):
    url = "https://api.angel.co/1/startups/"+str(id)
    payload = { 'access_token': TOKEN}
    response = requests.get(url,data=payload)
    data = json.loads(response.text)
    if data.has_key("success") or data["hidden"]== True :
        print "hidden true return fasle" 
        return False
    else:
        if data.has_key("company_url") and data["company_url"] == None:
            print "compny url none" 
            return False
        if urlBlackList(data["name"],data["company_url"]): 
            print "compny url blacklist" 
            return False
        try:
            company = Company.objects.create(companyId=id, name = str(data["name"]), website=str(data["company_url"]))
        except:
            print "create error " 
            return False
    return company

def saveTag(tags):
    for tag in tags:
        id = int(tag["id"])
        try:
            tagObj = Tag.objects.get(tagId=id)
        except:
            print "can't find tag %s" % tag["display_name"]
            try:
                newtag = Tag.objects.create(tagId=id,tagType=tag["tag_type"],tagName=tag["display_name"]) 
                print "create tag %s" % tag["display_name"]
            except Exception,e:
                print "can't create tag!! %s" % str(e)

def getCompanysFromTag(tag):
    tagId = tag.tagId
    data = getTagDataByPaging(tagId,0) # get first page  
    
    startup_array =[]
    startups = data["startups"]
    print " page #%s" % data["page"]
    print "last page %s" % data["last_page"]
    print "total %s" %data["total"]
    if data["page"] != None and data["last_page"]!=None and int(data["last_page"])>int(data["page"]):
        #print "inside !!!!"
        i = int(data["page"])+1
        while i <=  int(data["last_page"]):
            print i
            newData = getTagDataByPaging(tagId,i)
            if newData.has_key("error") and newData["error"] == "over_limit" :
                print "get company list over limit at page %s" % str(i)
                time.sleep(1000)
                continue
            startups += newData["startups"] 
            i+=1
    print "Done load company list from tags, lenght is %s" % str(len(startups))        
    # get all startup list
    i = 0 
    while i < len(startups):
        if startups[i]["hidden"] == True:
            i+=1
            continue
        company  = getStartupById(int(startups[i]["id"]),tag)
        if company == 2:
            time.sleep(1000)
            continue
        if company != False:
            startup_array.append(company)
        i+=1

    return startup_array

def getCompanysFromAngelList(tag):
    print tag.tagId
    tagId = tag.tagId
    data = getTagDataByPaging(tagId,0) # get first page  
    startup_array =[] 
    if data.has_key('errors'):
        print "over limit" 
        return startup_array
    startups = data["startups"]
    print " page #%s" % data["page"]
    print "last page %s" % data["last_page"]
    print "total %s" %data["total"]
    if data["page"] != None and data["last_page"]!=None and int(data["last_page"])>int(data["page"]):
        #print "inside !!!!"
        i = int(data["page"])+1
        while i <=  int(data["last_page"]):
            print i
            newData = getTagDataByPaging(tagId,i)
            startups += newData["startups"] 
            i+=1
    print len(startups)
    # get all startup list 
    for item in startups:
        if item["hidden"] == True:
            continue
        company  = getStartupById(int(item["id"]),tag)
        if company != False:
            startup_array.append(company)
    return startup_array

def getTagDataByPaging(tagId,pageNum):

    url = "https://api.angel.co/1/tags/%s/startups" % str(tagId)
    if(pageNum > 0):
        url += "?page=%s" %str(pageNum)
    response = requests.get(url)
    #print response.text
    return json.loads(response.text)
from django.template.defaultfilters import slugify

def readTagFromxlx():
    wb = load_workbook(filename = r'/Users/wenzhixue/Downloads/Level1_Category_V2.xlsx')
    sheet_ranges = wb.get_sheet_by_name(name = 'Sheet1')
    result = {}
    for row in xrange(2, 575):
        id = sheet_ranges.cell('A%s'%row).value
        tagName = sheet_ranges.cell('B%s'%row).value
        parentID = sheet_ranges.cell('C%s'%row).value
        keywords =  sheet_ranges.cell('D%s'%row).value
        isBlastoff = sheet_ranges.cell('E%s'%row).value
        newRow = {
                  'tagName':tagName,
                  'parentID':parentID,
                  'keywords':keywords,
                  'isBlastoff':isBlastoff
                  }
        try:
            tag = Tag.objects.get( slug = slugify(tagName))
        except:
            try:
                tag = Tag.objects.create(tagName = tagName,tagType ='Industry',slug=slugify(tagName))
            except Exception,e:
                print str(e)
            else:
                newRow['id'] = tag.id
        else:
            newRow['id'] = tag.id
        #tag.fetched = 2
        #tag.save()
        result[int(id)]=newRow

    return result

def tagParents():
    result =  readTagFromxlx()
    for k,row in result.items():
        if row['parentID'] != None:
            try:
                tag = Tag.objects.get( id = int(row['id']))
            except:
                print "can not find tag %s " % row['id']
            else:
                parentId = int(row['parentID'])
                parentRow = result[parentId]
                try:
                    parentTag = Tag.objects.get( id = int(parentRow['id']))
                except:
                    print "can not find parent tag %s " % parentRow['id']
                else:
                    print tag.tagName +" ->>> "  + parentTag.tagName
                    tag.move_to(parentTag, position='first-child')
                  

def reTag():
    result =  readTagFromxlx()
    for k,row in result.items():
        keywords = row['keywords']
        if keywords != None:
            keywords_list = keywords.split(", ")
            for i in keywords_list:
                print "rowid = %s <%s>"  % (row['rowId'], i) 
                try:
                    chindTag = Tag.objects.get( slug = slugify(i))
                except:
                    print "can not find tag %s" % i
                else:
                    continue
                    try:
                        parentTag = Tag.objects.get( slug = slugify(row['tagName']))
                    except:
                        print "can not get paretne tag %s " %  row['tagName']
                    else:
                        
                        comps = Company.objects.filter(tag=chindTag)
                        for comp in comps:
                            comp.tags.delete(chindTag)
                            comp.tags.add(parentTag)
                            comp.save()




        



