
import pickle      
from dateutil import parser
import requests
def dataPadToString(traffic,feedType):
    if feedType == 'reach':
        data = [pickle.loads(str(i['data']))[0] for i in traffic]
    elif feedType == 'rank':
        data = [pickle.loads(str(i['data']))[1] for i in traffic]
    else:
        return None

    return str(data).replace(' ','').replace('[','').replace(']','')
                 

def generateImgForWebFeed(webFeed,traffic):
    feedType = webFeed.type
    period = webFeed.period
    fileName = "%s_%s_%s.png" %(webFeed.company.id,feedType,period)
    fileDir = '/home/ubuntu/blastoff/company/static/img/datafeed/%s' % fileName
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
    r = requests.get(url)
    if r.status_code == 200:
        with open(fileDir,'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk) 




def generateDataImg():
    conn = boto.connect_s3(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY)
    bucket = conn.create_bucket('datafeed-image')
    allComp = Company.objects.filter(analysed = True)
    start = False
    for comp in allComp:
        traffic = WebTraffic.get_reach(company_id=comp.id)
        if len(traffic) < 30:
            continue
        reach = str([ item['reach'] for item in traffic ])
        reach = reach.replace(' ','')
        reach = reach.replace('[','')
        reach = reach.replace(']','')
        firstDate =  parser.parse(str(traffic[0]['date'])).strftime('%B')[:3]
        endDate =  parser.parse(str(traffic[-1]['date'])).strftime('%B')[:3]
        url = "https://chart.googleapis.com/chart?cht=lc&&chds=a&chd=t:%s&chs=150x100&chxt=x&chxl=0:|%s|%s" %(reach,firstDate,endDate)
        r = requests.get(url)
        if r.status_code == 200:
            fileName = '/home/ubuntu/blastoff/company/static/img/datafeed/%s.png'%comp.id 
            with open(fileName,'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            #k = Key(bucket)
            #k.key = '%s.png' % comp.id
            #k.set_contents_from_filename(fileName)
