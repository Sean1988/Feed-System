import requests
from feed.models import * 
from lxml import objectify
from BeautifulSoup import BeautifulSoup
from dateutil import parser
from company.models import Company
import simplejson as json
import datetime
from raven import Client

client = Client('http://c659d941ffad4a8eb543e0a5c7751bc9:ef3dcbbc81cf4f1187a5d41fbc601f89@www.cornerstore.me:9000/2')
def fetchNewsFromFaroo(company):
    url = "http://www.faroo.com/api?q="+company.name+"&start=1&length=10&l=en&src=news&f=json"
    try:
        r = requests.get(url)
        data = json.loads(r.content)
        for item in data['results']:
            title = item['title']
            domain = item['domain']
            desc = item['kwic']
            author=item['author']
            date=item['date']
            link = item['url']
            dateObj = datetime.datetime.fromtimestamp(int(date)/1000)
            news = NewsData.objects.create(company=company, title= title,link=link,pub_date=dateObj,description=desc,domain=domain,author=author)
    except Exception,e:
        client.captureException()
            

def  fetchNewsFromGoogle(company):
    as_oq = company.name+"+"+company.website
    q = company.name+"+OR+"+company.website
    url = "https://news.google.com/news/feeds?hl=en&gl=us&as_oq="+as_oq+"&as_occt=any&as_qdr=d&authuser=0&q="+q+"&um=1&ie=UTF-8&output=rss"
    print url
    r = requests.get(url)
    try:
        root = objectify.fromstring(r.content)
    	root.channel.item
    except Exception,e:
    	print str(e)
    	print "no news for company %s" % company.name
    	return
    news_docs = []
    for item in root.channel.item:
        title = item.title.text
        link = item.link.text.split('url=')[1]
        pubDate = dt = parser.parse( item.pubDate.text )
        desc_bf = item.description
        desc = BeautifulSoup(desc_bf.text).find('div',{'class':"lh"}).findAll('font',{'size':'-1'})[1].text
        # how can we know the google change the text
        # check whether the news is already in db 

        news_docs.append(NewsFeed(company_id=company.id, title= title,link=link,pub_date=pubDate,description=desc))
    try:
    	NewsFeed.objects.insert(news_docs)
    except:
    	pass
