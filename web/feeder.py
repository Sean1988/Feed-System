from feed.models import * 
from feed.feedImg import generateImgForWebFeed
ONE_WEEK_DAY = 7
TWO_WEEKS_DAY = 14
ONE_MONTH_DAY = 30
TWO_MONTHS_DAY = 60
THREE_MONTHS_DAY = 90
SIX_MONTHS_DAY = 180


IS_SPIKE_RATE = 0.3 # threshold for how much point in data is 0 to be consider as useless feed
FEED_GENERATE_DOOR = 5 # threshold for the change rate to be consider as useful data feed 


class WebFeedGenerator:

    def __init__(self):
        pass

    def isSpikeTraffic(self,array):
        count = 0 
        length = len(array)
        if length == 0 :
            return True
        for item in array:
            if int(item) == 0:
                count +=1
        if float(count)/float(length) > IS_SPIKE_RATE:
            return True
        return False

    def createDataFeed(self,amount,percent,feedType,period,company,traffic):
        if amount > 0:
            direction=1
        elif amount==0:
            return
        else:
            direction=-1
        print "generate feed for company %s type %s amount %s period %s percent %s direct %s" %(company.name,feedType,amount,period,percent,direction)
        datafeed, created = DataFeed.objects.get_or_create(company=company,type=feedType,period=period)
        datafeed.amount=round(amount,3)
        datafeed.percent=percent
        datafeed.direction=direction
        datafeed.save()
        generateImgForWebFeed(datafeed,traffic)


    def generateReachFeed(self,traffic,company):
        reach = [pickle.loads(str(i['data']))[0] for i in traffic]
        if len(reach)> TWO_WEEKS_DAY and not self.isSpikeTraffic(reach[-TWO_WEEKS_DAY:]):# calculate 1 week
            thisWeekAvg = float(sum(reach[-ONE_WEEK_DAY:]))/ONE_WEEK_DAY
            lastWeekAvg = float(sum(reach[-TWO_WEEKS_DAY:-ONE_WEEK_DAY]))/ONE_WEEK_DAY
            #print "last week avg = %s this week avg = %s " % (lastWeekAvg , thisWeekAvg)
            amount = thisWeekAvg-lastWeekAvg
            if lastWeekAvg == 0 : 
                percent = 0
            else:
                percent = int(abs(amount/lastWeekAvg)*100)
            if percent > FEED_GENERATE_DOOR: 
                self.createDataFeed(amount,percent,'reach','1week',company,traffic)
        if len(reach) > TWO_MONTHS_DAY and not self.isSpikeTraffic(reach[-TWO_MONTHS_DAY:]):#calculate 1 month
            thisMonthAvg = float(sum(reach[-ONE_MONTH_DAY:]))/ONE_MONTH_DAY
            lastMonthAvg = float(sum(reach[-TWO_MONTHS_DAY:-ONE_MONTH_DAY]))/ONE_MONTH_DAY
            #print "last month avg = %s this month avg = %s " % (thisMonthAvg, thisMonthAvg)
            amount = thisMonthAvg-lastMonthAvg
            if lastMonthAvg == 0:
                percent = 0
            else:
                percent = int(abs(amount/lastMonthAvg)*100)
            if percent > FEED_GENERATE_DOOR:
                self.createDataFeed(amount,percent,'reach','1month',company,traffic)
        if len(reach) > SIX_MONTHS_DAY and not self.isSpikeTraffic(reach[-SIX_MONTHS_DAY:]):#calculate 3 month
            thisThreeMonthAvg = float(sum(reach[-THREE_MONTHS_DAY:]))/THREE_MONTHS_DAY
            lastThreeMonthAvg = float(sum(reach[-SIX_MONTHS_DAY:-THREE_MONTHS_DAY]))/THREE_MONTHS_DAY
            #print "last 3 month avg = %s this 3 month avg = %s " % (lastThreeMonthAvg, thisThreeMonthAvg)
            amount = thisThreeMonthAvg-lastThreeMonthAvg
            if lastThreeMonthAvg == 0 :
                percent = 0
            else:
                percent = int(abs(amount/lastThreeMonthAvg)*100)
            #print percent 
            if percent > FEED_GENERATE_DOOR:
                self.createDataFeed(amount,percent,'reach','3month',company,traffic)
