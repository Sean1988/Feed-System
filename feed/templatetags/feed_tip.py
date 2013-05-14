from django import template
from company.models import * 

register = template.Library()


@register.filter(name='dataFeed_title')
def dataFeed_title(value):
    if value.type == 'reach':
        entity = "web traffic"
        if value.direction ==1:
            direction = 'has climbed by'
        else:
            direction = 'has dropped by'
        if value.period == '1week':
            period = '1 week'
        elif value.period == '1month':
            period = '1 month'
        elif value.period == '3month':
            period = '3 months'
        return ' web traffic %s %s in %s' %(direction,str(int(value.percent))+'%',period)
    elif value.type == 'rank':
        entity = "global web traffic rank"
        if value.direction ==1:
            direction = 'has climbed by'
        else:
            direction = 'has dropped by'
        if value.period == '1week':
            period = '1 week'
        elif value.period == '1month':
            period = '1 month'
        elif value.period == '3month':
            period = '3 months'
        return ' web traffic %s %s in %s' %(direction,str(int(value.percent))+'%',period)



