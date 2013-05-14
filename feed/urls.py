from django.conf.urls import patterns, include, url
from feed.views import *

urlpatterns = patterns('',

    url(r'^feed/', feedPage),

)
