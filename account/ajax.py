import simplejson as json
from account.models import * 
from django.http import HttpResponse
from company.models import Company, Tag
from signl.utils import ajax_login_required


@ajax_login_required
def autoFillIndustry(request):
    if request.POST:
        companyName = request.POST.get('name')
        if companyName != None and companyName != "":
            try:
                company = Company.objects.filter(name=companyName).order_by('rank')
            except:
                return HttpResponse(json.dumps({'success':False}))
            else:
                if company.exists():
                    return HttpResponse(json.dumps({'success':True,'tag':company[0].defaultTag.tagName}))
                else:
                    return HttpResponse(json.dumps({'success':False}))

        else:
            return HttpResponse(json.dumps({'success':False}))
    return HttpResponse(json.dumps({'success':False}))


@ajax_login_required
def ajaxChangeIndustry(request):
    if request.POST:
        name = request.POST.get('name')
        user = request.user
        if name != None and name != "":
            try:
                tag = Tag.objects.get(tagName=name)
            except:
                print "1111"
                user.industry = name
                user.save()
                return HttpResponse(json.dumps({'success':True}))
            else:
                print "2222"
                user.tag.add(tag)
                user.industry = name
                user.save()
                return HttpResponse(json.dumps({'success':True}))
        else:
            return HttpResponse(json.dumps({'success':False,'msg':'message is not valid'}))
    return HttpResponse(json.dumps({'success':False,'msg':"Wrong Method"}))


@ajax_login_required
def ajaxChangeCompany(request):
    if request.POST:
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        user = request.user
        if slug != None and slug != "":
            try:
                company = Company.objects.get(slug=slug)
            except:
                return HttpResponse(json.dumps({'success':False,'msg':"Can not find Company"}))
            else:
                user.comp = company
                user.company_name = company.name
                user.save()
                return HttpResponse(json.dumps({'success':True}))
        elif name !=None and name != "":
            try:
                company = Company.objects.get(name=name)
            except:
                user.company_name = name
                try:
                    user.save()
                except:
                    return HttpResponse(json.dumps({'success':False,'msg':"Company name is not valid"}))
                else:
                    return HttpResponse(json.dumps({'success':True}))          
            else:
                user.comp = company
                user.company_name = company.name
                user.save()
                return HttpResponse(json.dumps({'success':True}))
        else:
            return HttpResponse(json.dumps({'success':False,'msg':'message is not valid'}))
    return HttpResponse(json.dumps({'success':False,'msg':"Wrong Method"}))
