from django.shortcuts import render
from feed.views import * 
from account.models import * 

def feedEmail(request):
    user= MyUser.objects.get(email="root@blastoff.co")
    if not user.comp and not user.tracker.exists():
        feed_list = getDefaultFeed()
    else:
        feed_list = selectFeedFromCompAndTag(user)
    feed_list = feed_list[:6]

    print len(feed_list)
    return render(request, 'weekly_digest.html', locals())
