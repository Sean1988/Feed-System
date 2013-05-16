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
            period = 'past week'
        elif value.period == '1month':
            period = 'past one month'
        elif value.period == '3month':
            period = 'past three months'
        return ' web traffic %s %s over the %s' %(direction,str(int(value.percent))+'%',period)




