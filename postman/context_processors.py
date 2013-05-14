from __future__ import unicode_literals

from postman.models import Message


def inbox(request):
    """Provide the count of unread messages for an authenticated user."""
    if request.user.is_authenticated():
        response = {'postman_unread_count': Message.objects.inbox_unread_count(request.user)}
        if request.user.tier == 1 or request.user.tier == 0 :
            try:
                response['homeTag'] = request.user.tag.all()[0].tagName
            except:
                pass
        return response
    else:
        return {}
