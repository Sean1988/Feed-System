from company.models import * 
from django.db.models import Q
from account.models import *

from django.template.loader import render_to_string
from marketing.tasks import send_simple_message
from feed.views import * 

DOMAIN = "http://www.signl.com"
DEF_ICON = "/static/img/def_comp_icon.jpg"
WELCOME_CAMP = "bt57f"
MARKETING_CAMP = "bt57g"
DIGEST_CAMP = "bt6g7"
SIGNL_INFO = "Signl <info@signl.com>"
SIGNL_MARKETING = "Signl <nick@signl.com>"



def send_digest():
    allUsers = MyUser.objects.filter(is_company=False)
    for user in allUsers:
        send_weekly_digest(user)  

def send_weekly_digest(user):
    sender = SIGNL_INFO
    subject = "Signl Weekly Digest"
    receiver = user.email

    if not user.comp and not user.tracker.exists():
        feed_list = getDefaultFeed()
    else:
        feed_list = selectFeedFromCompAndTag(user)
    feed_list=feed_list[:6]
    
    content = render_to_string('weekly_digest.html', locals())
    send_simple_message(sender,receiver,subject,content,'weekly_digest', DIGEST_CAMP)

    


def send_welcome_email(user):
    sender = SIGNL_INFO 
    receiver = user.email
    subject = "Welcome to Signl."
    if user.comp :
        seeCompUrl = "%s/company/%s/" % (DOMAIN,user.comp.slug)
        if user.comp.thumb == DEF_ICON:
            iconUrl = DOMAIN + DEF_ICON 
        else:
            iconUrl = user.comp.thumb
    else:
        seeCompUrl = "%s/feed/?rmd=1" % DOMAIN
        iconUrl = DOMAIN + DEF_ICON 

    if user.tag.exists():
        industryPage  = "%s/searchTag/?tagSlug=%s" % (DOMAIN, user.tag.all()[0].slug)
    else:
        industryPage  = "%s/feed/?rmd=1" % DOMAIN
    trackCompanyUrl = "%s/accounts/tracker/" % DOMAIN
    feedUrl = "%s/feed/" % DOMAIN

    content = render_to_string('welcome_email.html', locals())
    send_simple_message(sender,receiver,subject,content,'welcome', WELCOME_CAMP)

from django.db.models import Q
def sendPromotEmail():
    cot = 0
    sender = SIGNL_MARKETING
    allComps = Company.objects.filter(Q(email__isnull=False),~Q(email=""),Q(rank__lt=100000),Q(emailSent = False))
    for item in allComps:
        if item.defaultTag != None:
            url = "http://www.signl.com/ranking/?comp=%s" % item.slug
            subject = "%s Momentum Score - April 2013" % item.name
            footer= "<p style='font-size: 9px;color:gray;margin:1px;'>I'm only planning to email you once, but you can still <a href='%unsubscribe_url%'>unsubscribe.</a></p><p style='font-size: 9px;color:gray;margin:1px;'>2013, SIGNL. 20 Jay St. New York City, NY, 11201</p>"
            body1 = "<html><p>Hello,</p><p></br>I work at Signl, where we monitor the fastest growing companies across many industries. %s showed up on our %s growth ranking for April 2013. </p>" % (item.name, item.defaultTag.tagName)
            body = body1+ "<p>Signl helps companies like yours measure growth and the competitive landscape around you. You can view your ranking here:</p></br>"+url+"</br><p>Let me know if you have any questions.</p>"
            body = body + "<p>Best,<br>Nick, Founder</p><p><a href='http://www.signl.com'>Signl.com</a><br>Address: 20 Jay St. New York City<br>Email: nick@signl.com<br>Phone: 862.205.4769</p><br>"+footer+"</html>"
            try:
                send_simple_message(sender,"wenzhixue@gmail.com",subject,body,'marketing',MARKETING_CAMP)
                return
            except:
                print "send email error %s " % item.email
                continue
            print "sent email to %s " %(item.email) 
            item.emailSent = True
            item.save()
            cot +=1
            if cot == 50:
                return
