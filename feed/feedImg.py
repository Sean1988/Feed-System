
import pickle      
from dateutil import parser
import requests
import urllib2
import boto
import StringIO
from boto.s3.key import Key
from signl.settings import AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY

def dataPadToString(traffic,feedType):
    if feedType == 'reach':
        data = [pickle.loads(str(i['data']))[0] for i in traffic]
    elif feedType == 'rank':
        data = [pickle.loads(str(i['data']))[1] for i in traffic]
    else:
        return None

    return str(data).replace(' ','').replace('[','').replace(']','')
                 
def generateImgForWebFeed(webFeed,traffic):
    conn = boto.connect_s3(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY)
    bucket = conn.create_bucket('datafeed-image')
    feedType = webFeed.type
    period = webFeed.period
    
    if period == '1week':
        if len(traffic) < 15: return
        dataPad = traffic[-14:]
    elif  period == '1month':
        if len(traffic) < 61: return
        dataPad = traffic[-60:]
    elif period == '3month':
        if len(traffic) < 181: return
        dataPad = traffic[-180:]
    
    firstDate =  parser.parse(str(dataPad[0]['date'])).strftime('%m/%d')
    endDate =  parser.parse(str(dataPad[-1]['date'])).strftime('%m/%d')
    dataStr = dataPadToString(dataPad,feedType) # get last two weeks data
    if dataStr == None:
        return
    url = "https://chart.googleapis.com/chart?cht=lc&&chds=a&chd=t:%s&chs=150x100&chxt=x&chxl=0:|%s|%s" %(dataStr,firstDate,endDate)
    fileName = "%s_%s_%s.png" %(webFeed.company.id,feedType,period)
    uploadToS3(url,fileName)



def writeToLocal(url,fileName):
    fileDir = '/home/ubuntu/signl/static/img/datafeed/%s' % fileName
    r = requests.get(url)
    if r.status_code == 200:
        with open(fileDir,'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk) 

def uploadToS3(url,fileName):
    try:
        conn = boto.connect_s3(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket('web-datafeed-img')
        k = Key(bucket)
        k.key = fileName
        file_object = urllib2.urlopen(url)           # 'Like' a file object
        fp = StringIO.StringIO(file_object.read())   # Wrap object    
        k.set_contents_from_file(fp)
        return "Success"
    except Exception, e:
        return e

