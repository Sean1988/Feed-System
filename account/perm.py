def check_permission(request,tag):
    if request.user.tier == 0 or request.user.is_anonymous():
    	return True
    elif request.user.tier == 1:
        if request.user.tag.count() == 0:
            return 2
        elif request.user.tag.all()[0] != tag:
            return True
    elif request.user.tier == 2:
        return False

    return False
