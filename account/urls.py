from django.conf.urls import patterns, include, url
from account.views import *
from account.ajax import * 
urlpatterns = patterns('',

    url(r'^doLogin/', doLogin),
    url(r'^logout/', doLogout),
    url(r'^login/', loginPage),
    url(r'^doRegister/', doRegister),
    url(r'^register/', register),
    url(r'^basic-profile/', profileFill),
    url(r'^contact/', contact),
    url(r'^msgadmin/', messageAdmin),
    url(r'^msgAdminSaveEmail/', msgAdminSaveEmail),
    url(r'^payment/', payment),
    url(r'^doPayment/', doPayment),
    url(r'^processEvent/', processEvent),
    url(r'^tracker/', trackerPage),
    url(r'^track/', track),
    url(r'^untrack/', untrack),

    url(r'^ajax/changeCompany/', ajaxChangeCompany),
    url(r'^ajax/changeIndustry/', ajaxChangeIndustry),
    url(r'^ajax/autoFillIndustry/', autoFillIndustry),
    url(r'^recommend/', recommend),
    url(r'^recommendTrack/', recommendTrack),
    

    url(r'^setting/', setting),
    url(r'^doSetting/', doSetting),
    url(r'^resetPassword/', resetPassword),  
    url(r'^emailSetting/', emailSetting),
    url(r'^doEmail/', doEmail),
       
    url(r'^pickIndustry/', pickIndustry),
    url(r'^industries/', pickIndustryPage),  

)
