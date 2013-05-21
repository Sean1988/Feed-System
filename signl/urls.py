from django.conf.urls import patterns, include, url
from company.views import * 
from mobile.views import * 
from web.views import * 
from account.views import * 
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from marketing.views import * 
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from wiki.urls import get_pattern as get_wiki_pattern
from django_notify.urls import get_pattern as get_notify_pattern
SLUG = "(?P<slug>[-\w]+)"

urlpatterns = patterns('',
    # Examples:


    url(r'^$', main),
    url(r'^searchMarketTag/', searchMarketTag),
    url(r'^searchTag/', searchTag),
    url(r'^searchApp/', searchApp),
    url(r'^search/', search),
    url(r'^searchview/', searchView),
    url(r'^indAuto/', industryAutocomplete),
    url(r'^locAuto/', locationAutocomplete),
    url(r'^tagAuto/', tagAutocomplete),
    url(r'^compAuto2/', companyAutocomplete2),
    url(r'^compAuto/', companyAutocomplete),
    url(r'^accounts/', include('account.urls')),    
    url(r'^', include('feed.urls')), 
    url(r'^tools/', include('scheduler.urls')), 
    url(r'^aboutUs/', aboutUs),
    url(r'^contactUs/', contactUs),
    url(r'^privatePolicy/', privatePolicy),
    url(r'^terms/', termsOfService),
    url(r'^blog/$', blogPage),
    url(r'^update/', update),

    url(r'^company/'+SLUG, getCompany),
    url(r'^tag/(?P<tagSlug>[-\w]+)/(?P<slug>[-\w]+)/', tagWithCompany),  
    
    url(r'^getTrafficData/', getTrafficData),
    url(r'^getAppRankHistory/', getAppRankHistory),
    
    url(r'^company/'+SLUG, getCompany),
    url(r'^getAppRank/', getAppRank),
     
    url(r'^getcompanylist/', get_company_list,name = 'get_company_list'),
    url(r'^getapplist/', get_app_list,name = 'get_app_list'),
    
    url(r'^industry/'+SLUG, industry),
    url(r'^ranking/', marketingRedic),
    url(r'^test/', feedEmail),  
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^message/',include('postman.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^password/',include('password_reset.urls')),
    url(r'^notify/', get_notify_pattern()),
    url(r'^wiki/', get_wiki_pattern()),
   
)
