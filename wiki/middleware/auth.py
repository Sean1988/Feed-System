from django.http import HttpResponseRedirect

class WikiCheckPermission(object):  
    def process_request(self, request):
        if 'wiki' in request.get_full_path():
            if not request.user.is_authenticated() or not request.user.has_module_perms('wiki'):
                return HttpResponseRedirect('/')
        return None  