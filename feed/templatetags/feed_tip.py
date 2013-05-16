from django import template
from company.models import * 
from web.models import * 
register = template.Library()


@register.filter(name='sub_feed')
def sub_feed(value):
    if len(value) >=2:
        return value[1:]
    else:
        return None

@register.filter(name='isWebDataFeed')
def isWebDataFeed(value):
    if type(value) == list:
        return True
    else:
        return False


@register.filter(name='subfeedTitle')
def subfeedTitle(value):
    if value.type == 'reach':
        if value.period == '1week':
            period = '1 week'
        elif value.period == '1month':
            period = '1 month'
        elif value.period == '3month':
            period = '3 months'
        return 'Over the last three weeks, web traffic has grown (or fallen) by __'
        return ' web traffic changes in %s %s over the %s' %(direction,str(int(value.percent))+'%',period)


@register.filter(name='dataFeed_title')
def dataFeed_title(value):
    if value.type == 'reach':
        entity = "web traffic"
        if value.direction ==1:
            direction = 'has climbed by'
        else:
            direction = 'has dropped by'
        if value.period == '1week':
            period = 'past week'
        elif value.period == '1month':
            period = 'past one month'
        elif value.period == '3month':
            period = 'past three months'
        return ' web traffic %s %s over the %s' %(direction,str(int(value.percent))+'%',period)


@register.filter(name='webDataFeed_sub')
def dataFeed_title(value):
    if value.type == 'reach':

        if value.direction ==1:
            direction = 'grown'
        else:
            direction = 'fallen'
        if value.period == '1week':
            period = 'past week'
        elif value.period == '1month':
            period = 'past one month'
        elif value.period == '3month':
            period = 'past three months'
        return "Over the %s, web traffic has %s by %s." % (period,direction, str(int(value.percent))+'%')
