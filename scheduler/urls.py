from django.conf.urls import patterns, include, url
from scheduler.views import *

urlpatterns = patterns('',

    url(r'^getAvailableSettings/', getNextAccount),
    
)
