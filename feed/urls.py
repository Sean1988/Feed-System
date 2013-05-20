from django.conf.urls import patterns, include, url
from feed.views import *
from feed.ajax import * 
urlpatterns = patterns('',

    url(r'^feed/', feedPage),
    url(r'^dismissTutorial/', ajaxChangeFeedTutorial),

)
