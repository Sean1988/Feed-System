from os.path import basename
from urlparse import urlsplit
from company.models import * 
from signl.utils import *
from blastoff.cache import *
from company.views import * 
from datetime import datetime
import os
import urllib2
import zipfile
import csv
import shutil

def url2name(url):
    return basename(urlsplit(url)[2])

def download(url, localFileName = None):
    localName = url2name(url)
    req = urllib2.Request(url)
    r = urllib2.urlopen(req)
    if r.info().has_key('Content-Disposition'):
        # If the response has Content-Disposition, we take file name from it
        localName = r.info()['Content-Disposition'].split('filename=')[1]
        if localName[0] == '"' or localName[0] == "'":
            localName = localName[1:-1]
    elif r.url != url: 
        # if we were redirected, the real file name we take from the final URL
        localName = url2name(r.url)
    if localFileName: 
        # we can force to save the file as specified name
        localName = localFileName
    f = open(localName, 'wb')
    f.write(r.read())
    f.close()
    return os.path.abspath(f.name)

def unzip(filePath):
    zfile = zipfile.ZipFile(filePath)
    for name in zfile.namelist():
        (dirname, filename) = os.path.split(name)
        print "Decompressing " + filename + " on " + dirname
        #if not os.path.exists(dirname):
        #    os.mkdir(dirname)
        f = open(name,"w")
        f.write(zfile.read(name))
        f.close()
        return os.path.abspath(f.name)
        
def readCSV(name,today):
    ifile  = open(name, "rb")
    reader = csv.reader(ifile)
    rownum = 0
    siteCache = AlexRankCache()
    for row in reader:
        #print row
        rank = row[0]
        site = row[1]
        siteCache.addRank(site,rank,today)       
        rownum += 1
    siteCache.save()
    print "successfully save %s data" % str(rownum)
    siteCache.save()
    ifile.close()

def addAlexaWebsiteToDB(url):
    pass

def saveNewTopSite():
    allCompany= Company.objects.all()
    allCompanySite = {}
    for item in allCompany:
        if len(item.website) < 3:
            continue
        url = trimUrl(item.website)
        allCompanySite[url] = 1

    top100k = getTop100k()
    count = 0
    for idx, site in enumerate(top100k):
        name = site.split('.')[0]
        rank = idx+1
        #print "rank is %s and site is %s" % (str(rank),site)
        if allCompanySite.has_key(site):   
            continue
        count +=1
    #print count 
        try:
            company = Company.objects.create(name = name, website = site, rank = rank, twitter="s")
        except Exception,e:
            print "create site error : %s" % str(e)
        else:
            print "getting company site alexa data !!!!!!! %s" % site
            #a = fetcheAlexaHistoricalData(company,12,2012)
            #if a == 2:
            #    continue
            #b = fetcheAlexaHistoricalData(company,11,2012)
            #if b == 2:
            #    continue
            #c = fetcheAlexaHistoricalData(company,10,2012)   
             


def getTop100k():
    today = str(datetime.today()).split(" ")[0]
    newZipFile = "/home/ubuntu/alexarank/top-1m.csv." + today + ".zip"
    csvFilePath = unzip(newZipFile)
    ifile  = open(csvFilePath, "rb")
    reader = csv.reader(ifile)
    data = []
    count = 0
    for row in reader:
        if count > 100000:
            break
        data.append(row[1])
        count +=1
    os.remove(csvFilePath)
    return data
    
def getAlexa1mrank():
    url = "http://s3.amazonaws.com/alexa-static/top-1m.csv.zip"
    zipFilePath = download(url)
    today = str(datetime.today()).split(" ")[0]
    #newZipFile = zipFilePath[:-4]+today+".zip"
    newZipFile = "/home/ubuntu/alexarank/top-1m.csv." + today + ".zip" 
    shutil.move(zipFilePath,newZipFile)
    #csvFilePath = unzip(newZipFile)
    #readCSV(csvFilePath,today)
    #os.remove(csvFilePath)
    pass
