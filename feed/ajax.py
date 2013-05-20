import simplejson as json
from django.http import HttpResponse
from signl.utils import ajax_login_required

@ajax_login_required
def ajaxChangeFeedTutorial(request):
    if request.POST:
        action = request.POST.get('action')
        user = request.user
        if action == 'dismiss':
            user.feedTutorial = False
            user.save()
            return HttpResponse(json.dumps({'success':True}))
        else:
            return HttpResponse(json.dumps({'success':False,'msg':'function not found'}))
    return HttpResponse(json.dumps({'success':False,'msg':"Wrong Method"}))

