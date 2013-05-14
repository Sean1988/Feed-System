# Create your views here.

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login,logout
from django.contrib import auth
from django.core.context_processors import csrf
import hashlib
import simplejson as json
from account.models import MyUser
User = MyUser
from company.models import Company,Tag
import stripe
from django.core.validators import email_re
from django.core.signing import Signer
from django import forms
from postman.models import Message,PendingMessage
from marketing.promot import send_welcome_email

from account.ajax import ajax_login_required
ERROR_AUTH_FAIL = "UserName/Password was wrong."
ERROR_ISLINKEDIN = 'You registered by Linkedin last time, please use Linkedin login.'
ERROR_INACTIVE = "Account has been inactive. Please contact support."
ERROR_INVALID_EMAIL = "Email address is invalid."
ERROR_EMAIL_TAKEN='This email address has already been registered.'
ERROR_CREATE_ACCOUT = "Can not create account. Please contact support."
ERROR_TOKEN_INVALID = "Sorry, your token is invalid."
ERROR_OLDPASSWORD = "Incorrect old password. Try again?"
ERROR_PASSWORD_MISMATCH = "Sorry, your new passwords don't match, please re-enter your new password."


def is_valid_email(email):
    return True if email_re.match(email) else False

@login_required
def trackerPage(request):
    tracked_comp = request.user.tracker.all()
    return render(request, 'tracker.html', locals())


@ajax_login_required
def track(request):
    if request.POST:
        slug = request.POST.get('slug')
        companyId = request.POST.get('id')
        try:
            if companyId != None:
                company = Company.objects.get(id=companyId)
            else:
                company = Company.objects.get(slug=slug)
        except:
            return HttpResponse(json.dumps({'success':False,'msg':"Can not find Company"}))
        else:
            request.user.tracker.add(company)
            request.user.save()
            return HttpResponse(json.dumps({'success':True}))
    return HttpResponse(json.dumps({'success':False,'msg':"Wrong Method"}))


@ajax_login_required
def untrack(request):
    if request.POST:
        slug = request.POST.get('slug')
        try:
            company = Company.objects.get(slug=slug)
        except:
            return HttpResponse(json.dumps({'success':False,'msg':"Can not find Company"}))
        else:
            request.user.tracker.remove(company)
            request.user.save()
            return HttpResponse(json.dumps({'success':True}))
    return HttpResponse(json.dumps({'success':False,'msg':"Wrong Method"}))


@login_required
def messageAdmin(request):
    if not request.user.is_staff:
        return render(request, '404.html', locals())
    allPending = PendingMessage.objects.all()
    return render(request, 'msgAdmin.html', locals())


@csrf_exempt
def msgAdminSaveEmail(request):
    if request.POST and request.user.is_staff:
        id = request.POST.get('id')
        email = request.POST.get('email')
        try:
            user= User.objects.get(id=int(id))
        except:
            return HttpResponse(json.dumps({'success':False,'msg':"recipient not found"}))
        else:
            user.email = email
            try:
                user.save()
            except Exception,e:
                return HttpResponse(json.dumps({'success':False,'msg':str(e)}))
            else:
                return HttpResponse(json.dumps({'success':True}))
    else:
        return HttpResponse(json.dumps({'success':False,'msg':"No permission"}))


@csrf_exempt
def msgAdminSendEmail(request):
    if request.POST and request.user.is_staff:
        id = request.POST.get('id')
        try:
            msg = PendingMessage.objects.get(id=int(id))
        except:
            return HttpResponse(json.dumps({'success':False,'msg':"message not found"}))
        else:
            print msg.moderation_status 
            msg.set_accepted()
            msg.save()
            msg.notify_users('p', is_auto_moderated=False)
            print msg.moderation_status 
            return HttpResponse(json.dumps({'success':True}))
    else:
        return HttpResponse(json.dumps({'success':False,'msg':"No permission"}))


def transferCorpToUserAcct(loginUser,original):
    try:
        user= User.objects.get(email=original)
    except:
        return False,"Token expired."
    else:
        if user.is_company == False:
            return False,"Token expired."

        # transfer admin 
        try:
            comp = Company.objects.get(admin = user)
        except Exception,e:
            print str(e)
            return False,"Can not find email."
        else:
            comp.admin = loginUser
            comp.save()

        # transfer Message
        allMsg = Message.objects.filter(recipient=user)
        for msg in allMsg:
            msg.recipient = loginUser
            msg.save()
        
        #delete old account
        user.delete()
        return True,"" 

@login_required
def profileFill(request):
    if request.POST:
        company = request.POST.get('company')        
        title = request.POST.get('title')
        industry = request.POST.get('industry')
        slug = request.POST.get('slug')
        user = request.user
        if slug != request.user.slug:
            Error = "You can not update other's profile." 
            return render(request, 'profile_fill.html', locals())
        try:
            tag = Tag.objects.get(tagName=industry)
        except:
            tag = None
        else:
            request.user.tag.add(tag)
        try:
            request.user.industry = industry
            request.user.headline = title

            comp_check = Company.objects.filter(name=company).order_by('rank')
            # if comp is empty/company doesn't exist in our db
            if comp_check.exists():
                comp = comp_check[0]
                request.user.comp = comp
                request.user.company_name = comp.name
                comp.hasUser = True;
                if tag == None and comp.defaultTag != None:
                    request.user.tag.add(comp.defaultTag)
                    request.user.industry = comp.defaultTag.tagName
                comp.save()
            else:
                request.user.company_name = company

            request.user.save()
        except:
            Error = "Save profile failed." 
            return render(request, 'profile_fill.html', locals())
        else:
            send_welcome_email(request.user)
            return HttpResponseRedirect("/feed/?rmd=1")
    else:
        return render(request, 'profile_fill.html', locals())


def recommend(request):
    if request.user.is_authenticated():
        user = request.user

        try:
            userTag = user.tag.all()
        except:
            print "bad user given?"
            return render(request,"404.html")
        else:
            if not userTag:
                rmd = Company.objects.filter(rank__lte=20)[:9]
            else:
            # Get user industry, and grab company with highest smooth in those industry.
                rmd = Company.objects.filter(tags__tagName=userTag[0].tagName).order_by('-smooth')[:9]
                homeTag = userTag[0].tagName
            return render(request,"recommend.html", locals())
    return render(request,"recommend.html", locals())


@ajax_login_required
def recommendTrack(request):
    if request.POST:
        wantTrack = request.POST.get('wantTrack')
        try:
            companyIds=[ int(item)  for item in wantTrack.split(',')]
        except:
            return HttpResponse(json.dumps({'success':False,'msg':"Can't decode request"}))
        print companyIds
        
        try:
            company = Company.objects.filter(id__in=companyIds)
        except:
            return HttpResponse(json.dumps({'success':False,'msg':"Can't decode request"}))
        else:
            request.user.tracker.add(*company)
            try:
                request.user.save()
            except:
                return HttpResponse(json.dumps({'success':False,'msg':"Can't decode request"}))
            else:
                return HttpResponse(json.dumps({'success':True}))
    return HttpResponse(json.dumps({'success':False,'msg':"Wrong Method"}))


def loginPage(request):
    next = request.GET.get('next')
    token = request.GET.get('token')
    c = {}
    c.update(csrf(request))
    if next !=None:
        c.update({'next':next})
    if token !=None:
        c.update({'token':token})

    return render(request,"login.html", c)


def doLogin(request):
    if request.POST:
        email = request.POST.get('email')
        password = request.POST.get('password')
        linkedinId = request.POST.get('linkedinId')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        headline = request.POST.get('headline')
        pictureurl = request.POST.get('picture')
        next = request.POST.get('next')
        token = request.POST.get('token')
        
        try:
            userObj = User.objects.get(email = email)
        except:
            Error= ERROR_AUTH_FAIL
            return render(request, 'login.html', locals())
        else:

            if userObj.linkedinId is not None: # user is already linkedin user
                if linkedinId is not None: # is linkedin login
                    password = hashlib.sha224(linkedinId).hexdigest() # generate password for auth
                    userObj.headline = headline
                    userObj.icon = pictureurl
                    userObj.save()
                else: # is email login
                    Error = ERROR_ISLINKEDIN 
                    return render(request, 'login.html', locals())
            else: # user is email user
                if linkedinId is not None: #is linkedin login, merge user account to linkedin account
                    password = hashlib.sha224(linkedinId).hexdigest()
                    userObj.set_password(password)
                    userObj.linkedinId = linkedinId
                    userObj.first_name = firstname
                    userObj.last_name = lastname
                    userObj.headline = headline
                    userObj.icon = pictureurl
                    userObj.save()

        # Check if user login with linkedin, and connect account if needed
        loginUser = authenticate(email = email, password = password)

        if loginUser is not None and loginUser.is_active:
            if token != None and token !="":
                signer = Signer(salt='blastoffCorp')
                try:
                    original = signer.unsign(token)
                except signing.BadSignature:
                    if linkedinId == None: #emal register   
                        Error= ERROR_TOKEN_INVALID
                        return render(request, 'login.html', locals())  
                    else:
                        return HttpResponse(json.dumps({'success':'False','msg':ERROR_TOKEN_INVALID}))
                else:
                    success,msg = transferCorpToUserAcct(loginUser,original)
                    if success == False:
                        Error= msg
                        return render(request, 'login.html', locals())  

            auth.login(request, loginUser)          
            if linkedinId is not None:
                if next != None:
                    return HttpResponse(json.dumps({'success':'True','next':next}))
                else:
                    return HttpResponse(json.dumps({'success':'True'}))

            if next != None:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect("/")

        elif loginUser is not None and not loginUser.is_active:
            Error= ERROR_INACTIVE 
            return render(request, 'login.html', locals())
        else:
            Error= ERROR_AUTH_FAIL
            return render(request, 'login.html', locals())

    return HttpResponseRedirect("/")


def doLogout(request):
    logout(request)
    return HttpResponseRedirect("/")


def register(request):
    next = request.GET.get('next')
    token = request.GET.get('token')
    comp = request.GET.get('comp')
    print comp 
    c = {}
    if comp != None and comp != "":
        try:
            company = Company.objects.get(slug=comp)
        except:
            print "can not find company"
        else:
            c.update({'company':company})

    c.update(csrf(request))
    if next !=None:
        c.update({'next':next})
    if token !=None:
        c.update({'token':token})

    return render(request,"register.html", c)


def createAccountForUser(request,user,firstname,lastname,email,password=None,linkedinId=None,headline=None,pictureurl=None):
    user.first_name = firstname
    user.last_name = lastname
    user.email = email
    user.is_company = False
    if linkedinId !=None:
        user.headline = headline
        user.icon = pictureurl
        user.linkedinId = linkedinId
        password = hashlib.sha224(linkedinId).hexdigest()
    user.set_password(password)
    try:
        user.save()
    except:
        return False,ERROR_CREATE_ACCOUT
    loginUser = auth.authenticate(username = email, password = password)
    auth.login(request,loginUser)
    return True,""


def linkCorpAccount(request,target_email,firstname,lastname,email,password=None,linkedinId=None,headline=None,pictureurl=None):
    try:
        user = User.objects.get(email=target_email)
    except:
        return False,"Target Email is invalid."
    else:
        if user.is_company == False:
            return False,'Token expired.'
        if target_email == email :
            return createAccountForUser(request,user,firstname,lastname,email,password,linkedinId,headline,pictureurl)
        try:
            User.objects.get(email=email) # check email already exited
        except:
            return createAccountForUser(request,user,firstname,lastname,email,password,linkedinId,headline,pictureurl)
        else:
            return False,'Email address already exists.'


from django.contrib import messages
from django.core import signing
def doRegister(request):
    if request.POST:
        linkedinId = request.POST.get('linkedinId')        
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        headline = request.POST.get('headline')
        pictureurl = request.POST.get('picture')
        password = request.POST.get('password')
        token = request.POST.get('token')
        comp = request.POST.get('comp')
        next = request.POST.get('next')

        if not is_valid_email(email):
            messages.error(request, ERROR_INVALID_EMAIL)
            return HttpResponseRedirect("/accounts/register/") 
       
        if token != None and token != "":
            signer = Signer(salt='blastoffCorp')
            try:
                original = signer.unsign(token)
            except signing.BadSignature:
                messages.error(request, ERROR_TOKEN_INVALID)
                return HttpResponseRedirect("/accounts/register/?token="+token+"&next=/message/inbox/")  
            else:
                if linkedinId == None or linkedinId == "":
                    success,msg = linkCorpAccount(request,original,firstname,lastname,email,password)
                else:
                    success,msg = linkCorpAccount(request,original,firstname,lastname,email,"",linkedinId,headline,pictureurl)
                if success == False:
                    messages.error(request, msg)
                    return HttpResponseRedirect("/accounts/register/?token="+token+"&next=/message/inbox/") 
                else:
                    if next != None:
                        return HttpResponseRedirect(next) 
                    return HttpResponseRedirect("accounts/basic-profile/")


        try:
            userObj = User.objects.get(email = email);  
            if userObj is not None:
                messages.error(request, ERROR_EMAIL_TAKEN)
                return HttpResponseRedirect("/accounts/register/")             
        except:
            try:
                # Create password for user
                if linkedinId != None and linkedinId != "":
                    password = hashlib.sha224(linkedinId).hexdigest()
                print linkedinId
                user = User.objects.create_user(email = email, password = password)
                
                user.first_name = firstname
                user.last_name = lastname
                if linkedinId != None and linkedinId != "":
                    user.headline = headline
                    user.icon = pictureurl
                    user.linkedinId = linkedinId
                if comp != None and comp != "":
                    try :
                        comp = Company.objects.get(slug=comp)
                    except:
                        print "can not gat tag obj"
                    else:
                        user.comp = comp
                user.save()

            except Exception,e:
                print str(e)
                messages.error(request, ERROR_CREATE_ACCOUT)
                return HttpResponseRedirect("/accounts/register/")

            loginUser = authenticate( username = email, password = password)
            login(request,loginUser)

            return HttpResponseRedirect("/accounts/basic-profile/")


def pickIndustryPage(request):
    if request.user.is_anonymous():
        return render(request, '404.html', locals())
    if request.user.tag.count() > 0 :
        return render(request, '404.html', locals())
    nodes = Tag.objects.filter(tagType = "Industry",isBlastoff=True).order_by('isBlastoff')
    return render(request, 'industry.html', locals())


def pickIndustry(request):
    if request.GET:
        tagId = request.GET.get('tagId')

        if request.user.is_anonymous():
            return HttpResponse(json.dumps({'success':False,'msg':"No permission"}))
        try:
            tag = Tag.objects.get(id=tagId)
        except:
            return HttpResponse(json.dumps({'success':False,'msg':"tag not found"}))
        else:
            try:
                request.user.tag.add(tag)
                request.user.save()
            except:
                return HttpResponse(json.dumps({'success':False,'msg':"save tag error."}))

            else:
                return HttpResponse(json.dumps({'success':True})) 
    else:
        return HttpResponse(json.dumps({'success':False,'msg':'wrong method.'})) 


def setting(request):
    if request.user.is_authenticated():
        user = request.user
        c = {}
        c.update(csrf(request))
        if next !=None:
            c.update({'next':next})
        
        return render(request,"setting.html", locals())
    return render(request, "login.html")


def emailSetting(request):
    if request.user.is_authenticated():
        user = request.user
        return render(request,"email.html", locals())
    else:
        return HttpResponseRedirect("/accounts/login/?next=/accounts/emailSetting/")


def doEmail(request):
    wkFd = request.POST.get('wkFd')
    wkIdsy = request.POST.get('wkIdsy')
    idsyAlert = request.POST.get('idsyAlert')
    momAlert = request.POST.get('momAlert')
    trackSug = request.POST.get('trackSug')

    try:
        user = request.user
    except:
        return HttpResponse(json.dumps({'success':False,'msg':"user not found"}))
    else:
        try:
            if wkFd =='1':
                user.wkFd = True
            else:
                user.wkFd = False
            if wkIdsy =='1':
                user.wkIdsy = True
            else:
                user.wkIdsy = False
            if idsyAlert =='1':
                user.idsyAlert = True
            else:
                user.idsyAlert = False
            if momAlert =='1':
                user.momAlert = True
            else:
                user.momAlert = False
            if trackSug =='1':
                user.trackSug = True
            else:
                user.trackSug = False

            user.save()
            return HttpResponse(json.dumps({'success':True})) 
        except Exception,e:
            print str(e)
            return HttpResponse(json.dumps({'success':False,'msg':"update error"}))
    return HttpResponse(json.dumps({'success':False,'msg':"update error"}))


def doSetting(request):
    firstname = request.POST.get('firstname')
    lastname = request.POST.get('lastname')
    company = request.POST.get('company')
    headline = request.POST.get('headline')
    industry = request.POST.get('industry')

    try:
        user = request.user
    except:
        return HttpResponse(json.dumps({'success':False,'msg':"user not found"}))
    else:
        try:
            user.first_name = firstname
            user.last_name = lastname
            user.company_name = company
            user.industry = industry
            user.headline = headline
            user.save()
            return HttpResponse(json.dumps({'success':True})) 
        except Exception,e:
            print str(e)
            return HttpResponse(json.dumps({'success':False,'msg':"update error"}))
    return HttpResponse(json.dumps({'success':False,'msg':"update error"}))


def resetPassword(request):
    oldpassword = request.POST.get('oldpassword')
    newpassword = request.POST.get('newpassword')
    confirm = request.POST.get('newconfirm')

    try:
        user = request.user
    except:
        return HttpResponse(json.dumps({'success':False,'msg':"user not found"}))
    else:
        try:
            if (user.check_password(oldpassword)):
                if (newpassword == confirm):
                    user.set_password(newpassword)
                    user.save()
                    return HttpResponse(json.dumps({'success':True})) 
                else: 
                    return HttpResponse(json.dumps({'success':False,'msg':ERROR_PASSWORD_MISMATCH}))
            else: 
                return HttpResponse(json.dumps({'success':False,'msg':ERROR_OLDPASSWORD}))
        except Exception,e:
            print str(e)
            return HttpResponse(json.dumps({'success':False,'msg':"throw update error"}))
    return HttpResponse(json.dumps({'success':False,'msg':"update error"}))


def createUnknowAdminForCompany(company):
    email = "unknow@%s" % company.website
    try:
        result = User.objects.get_or_create(email = email)
    except:
        return False
    user = result[0]
    if result[1] == True:
        user.first_name=company.name
        user.is_company=True
        user.save()
    print user.email
    company.admin = user
    company.save()
    return user


from postman.api import pm_write_corp
def contact(request):
    if request.GET:
        if request.user.is_authenticated():
            slug= request.GET.get('slug')
            subject = request.GET.get('subject')
            body = request.GET.get('body')
            msgType = request.GET.get('type')
            try:
                recipient = User.objects.get(slug=slug)
            except:
                try:
                    comp = Company.objects.get(slug=slug)
                except:
                    return HttpResponse(json.dumps({'success':'False','msg':'recipient not found.'}))
                else:
                    recipient = createUnknowAdminForCompany(comp)
                    if recipient == False:
                        return HttpResponse(json.dumps({'success':'False','msg':'recipient not found.'}))
            
            pm_write_corp(request.user, recipient, subject, body,msgType)
            return HttpResponse(json.dumps({'success':'True'}))

        else:
            return HttpResponse(json.dumps({'success':'False','msg':'User is not authenticated.'}))
    else:
        return HttpResponse(json.dumps({'success':'False','msg':'Method wrong.'}))


from signl.settings import STRIPE_SECRET,STRIPE_PUBLISH
@login_required
def payment(request):
    next = request.GET.get('next')
    tag = request.GET.get('tag')
    PUBLISH = STRIPE_PUBLISH
    c = {}
    c.update(csrf(request))
    if next !=None:
        c.update({'next':next})
    
    tier = request.user.tier
    if tag != None and tag != '':
        jump = "/industry/"+ tag
    elif request.user.tag.all().count() == 0:
        jump = "/accounts/industries/"
    elif request.user.tag.all().count() > 0:
        jump = "/industry/"+ request.user.tag.all()[0].slug
    return render(request,"payment.html", locals())


def doPayment(request):
    stripe.api_key = STRIPE_SECRET

    # Get the credit card details submitted by the form
    token = request.POST.get('stripeToken')
    plan = request.POST.get('plan')
    # Create the charge on Stripe's servers - this will charge the user's card
    try:
        # Create a Customer
        user = request.user
        customer = stripe.Customer.create(
            card=token,
            plan=plan,
            email=user.email,
            description="Upgrade to "+ plan,
        )
        user.stripeId = customer.id
        user.save()

    except stripe.CardError, e:
      # The card has been declined, no stripeID has been saved
        return HttpResponse(json.dumps({'success':'False','msg':'Upgrade fails due to card declined'}))

    else:
        # Successfully charged, return to main
        return HttpResponse(json.dumps({'success':'True'}))


import time
from postman.api import pm_write
@csrf_exempt
def processEvent(request):
 
    event = json.loads(request.raw_post_data)
    try:
        recipient = User.objects.get(stripeId = event['data']['object']['customer'])
        body = "Hello! Welcome to Signl.\n\n"  
    except:
        print "recipient not found"
        pass

    try:
        systemUser = User.objects.get(email='Payment@blastoff.co')
        sender ='Payment@blastoff.co'
    except:
        print "systemUser not found"
        pass

    # 1. First Payment
    if event['type'] == "customer.subscription.created":
        planName = event['data']['object']['plan']['name']
        currency = event['data']['object']['plan']['currency']
        amount = str(event['data']['object']['plan']['amount'])
        status = event['data']['object']['status']
        startDate = time.strftime("%D %H:%M %Z", time.localtime(int(event['data']['object']['current_period_start'])))
        endDate = time.strftime("%D %H:%M %Z", time.localtime(int(event['data']['object']['current_period_end'])))

        subject = "You Have Successfully Subscribed to Signl's "+planName
        body = body+ "Welcome to the Signl Community!\n\nWe've received your payment of $"+amount[:-2]+".00"+", and your status as a "+planName+" is now active.\nWe hope you find our service as powerful and exciting as we do.\n\nIf you have any issues with the service, or believe you have received this email in error, please email us at info@blastoff.co.\n\nThank you for your business. We hope it helps YOUR business, and pays for itself ; )\n\n\nAll Our Best,\nThe Signl Team\n\n"
        body = body+"\n\nSignl\nAddress: 20 Jay St. New York City\nEmail: info@blastoff.co\nPhone: 862.205.4769\nWebsite: http://www.blastoff.co\n\n"
        # change user tier
        if planName == "Pro Plan":
            recipient.tier = 1
            recipient.save()
        elif planName == "Platinum Plan":
            recipient.tier = 2
            recipient.save()
        #pm_write(systemUser, recipient, subject, body, skip_notification=True)
        #sendEmail(sender, recipient.email, subject, body)
    # 2. Any subsequent payment is processed
    elif event['type'] == "charge.succeeded":
        invoiceId = event['data']['object']['invoice']
        amount = str(event['data']['object']['amount'])
        # only send the first payment receipt to the customer
        if recipient.tier == 0 or (recipient.tier == 1 and int(amount) == 29900):
            subject = "Your 1st Payment to Signl Has Been Received"
            body = body+"Your payment for has been received for $"+amount[:-2]+".00"+"\n\n"
            body = body+"Note: This email is also your receipt for your paid plan for "+recipient.first_name+" "+recipient.last_name+". Here are the details:\n\n"
            body = body+"======================================"
            body = body+"invoice #: "+invoiceId+"\nBill to:\n"+recipient.first_name+" "+recipient.last_name+"\n\n"
            body = body+"Total:$"+amount[:-2]+".00"+"\n\n\nIf you have any billing questions, please email us at billing@blastoff.co\n\n\nAll Our Best,\nThe Signl Team\n\n"
            body = body+"\n\nSignl\nAddress: 20 Jay St. New York City\nEmail: info@blastoff.co\nPhone: 862.205.4769\nWebsite: http://www.blastoff.co\n\n"

            sendEmail(sender, recipient.email, subject, body)
    # 3. User changes subscription level
    elif event['type'] == "customer.subscription.updated":
        pass
        #planName = event['data']['object']['plan']['name']
        #currency = event['data']['object']['plan']['currency']
        #amount = str(event['data']['object']['plan']['amount'])
        #oldplanName = event['data']['previous_attributes']['plan']['name']
        #oldCurrency = event['data']['previous_attributes']['plan']['currency']
        #oldAmount = str(event['data']['previous_attributes']['plan']['amount'])

        #subject = "Your subscription has been updated"
        #body = body+"Your subscription plan has changed from the old plan: "+ oldplanName+ " with "+ oldCurrency +" " + oldAmount +" to the new plan: "+ planName+ " with "+ currency +" " + amount + ending
        #pm_write(systemUser, recipient, subject, body)

    # 4. User updates credit card information
    elif event['type'] == "customer.updated":
        pass
    # 5. User or admin cancels account
    elif event['type'] == "customer.subscription.deleted":
        #planName = event['data']['object']['plan']['name']

        subject = "Your Account at Signl Has Been Cancelled"
        body = body+"Your account at Signl was recently cancelled.  We're sorry to see you go. If you have any feedback for us, or have canceled your subscription for a specific reason, please let us know at info@blastoff.co.\n\n"
        body = body+"If you think you've received this email in error, please contact us immediately (also at info@blastoff.co).\n\n\nBe Well,\nThe Signl Team\n\n"
        body = body+"\n\nSignl\nAddress: 20 Jay St. New York City\nEmail: info@blastoff.co\nPhone: 862.205.4769\nWebsite: http://www.blastoff.co\n\n"
        
        recipient.tier = 0
        recipient.save()

        #pm_write(systemUser, recipient, subject, body, skip_notification=True)
        sendEmail(sender, recipient.email, subject, body)
    # 6. Application of a promotional voucher
    elif event['type'] == "customer.discount.created":
        pass
    # 7. Credit card information is no longer valid (two events here)
    elif event['type'] == "invoice.payment_failed":
        planName = event['data']['object']['lines']['data'][0]['plan']['name']
        #description = event['data']['object']['lines']['data'][0]['description']
        invoiceId = event['data']['object']['id']
        startDate = time.strftime("%D %H:%M %Z", time.localtime(int(event['data']['object']['period_start'])))
        endDate = time.strftime("%D %H:%M %Z", time.localtime(int(event['data']['object']['period_end'])))

        subject = "Your Payment to Signl Has Failed"
        body = body+"Uh-oh! Your latest payment to Signl has failed to go through.\nAs always, you can access your account information at www.blastoff.co/.\n\n"
        body = body+"Note: The details of the declined transaction are included below.\n\n"
        body = body+"======================================"
        body = body+"RECEIPT #: "+invoiceId +"\nBill to:\n"+user.first_name+" "+user.last_name+"\n\n"+planName+" -- "+startDate+" to "+endDate+"\n\n"
        body = body+"Total:$"+amount[:-2]+".00"+"\n\nIf you have any questions, please email us at billing@blastoff.co\n\n\nThanks,\nThe Signl Team\n\n"
        body = body+"\n\nSignl\nAddress: 20 Jay St. New York City\nEmail: info@blastoff.co\nPhone: 862.205.4769\nWebsite: http://www.blastoff.co\n\n"
        #pm_write(systemUser, recipient, subject, body, skip_notification=True)
        sendEmail(sender, recipient.email, subject, body)
    else:
        print "not in event case"

    return HttpResponse(content='OK', content_type=None, status=200)


from django.core.mail import send_mail
def sendEmail(sender, recipient, subject, body):
    try:
        s=send_mail(subject, body, 'Signl <info@blastoff.co>',[recipient], fail_silently=False)
    except:
        print "send email error %s " % recipient
    print "sent email to %s " % recipient


