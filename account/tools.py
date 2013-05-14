#from django.contrib.auth import get_user_model
#User = get_user_model() 
import hmac
import hashlib
from account.models import * 

KEY = "awpblastoff"
PASSWORD = "blastoffcorp1"
def getAccountLinkToken(slug):  
    return hmac.new(str(slug), KEY, hashlib.sha256).hexdigest()


def createAdminForCompany(company):
    result = MyUser.objects.get_or_create(email = company.email)
    user = result[0]
    if result[1] == True:
        user.first_name=company.name
        user.is_company=True
        user.save()
    company.admin = user

'''
def syncCompanyToUser():
    all = Company.objects.filter(admin__isnull=True,email__isnull=False)
    for item in all:
        print item.id
    	password = "blastoffcorp1"
        print item.email
        print item.slug
    	try:
            user = User.objects.create_user(email = item.email,password = password)
            user.first_name=item.name
            user.is_company=True
            user.slug=item.slug
            user.save()
        except Exception , e:
        	print str(e)
        else:
        	item.admin = user
        	item.save()
'''
