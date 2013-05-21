# Create your views here.
from models import * 
from django.http import HttpResponse
from signl.utils import sendMsgAlert
import csv
import mimetypes
import os

def respond_as_attachment(request, file_path, original_filename):
    fp = open(file_path, 'rb')
    response = HttpResponse(fp.read())
    fp.close()
    type, encoding = mimetypes.guess_type(original_filename)
    if type is None:
        type = 'application/octet-stream'
    response['Content-Type'] = type
    response['Content-Length'] = str(os.stat(file_path).st_size)
    if encoding is not None:
        response['Content-Encoding'] = encoding

    # To inspect details for the below code, see http://greenbytes.de/tech/tc2231/
    if u'WebKit' in request.META['HTTP_USER_AGENT']:
        # Safari 3.0 and Chrome 2.0 accepts UTF-8 encoded string directly.
        filename_header = 'filename=%s' % original_filename.encode('utf-8')
    elif u'MSIE' in request.META['HTTP_USER_AGENT']:
        # IE does not support internationalized filename at all.
        # It can only recognize internationalized URL, so we do the trick via routing rules.
        filename_header = ''
    else:
        # For others like Firefox, we follow RFC2231 (encoding extension in HTTP headers).
        filename_header = 'filename*=UTF-8\'\'%s' % urllib.quote(original_filename.encode('utf-8'))
    response['Content-Disposition'] = 'attachment; ' + filename_header
    return response

# for distributed system crawler, when the worker startup, it request a new appannie account for crawling.
def getNextAccount(request):
    key = request.GET.get('key')
    if key == "missmydata2":
        accounts = CrawlerAccount.objects.filter(type="appannie",isUsed=False)[:1]
        if not accounts.exists():
            sendMsgAlert("running out of app annie account")
        else:
            account = accounts[0]
            account.isUsed = True
            account.save()
            return HttpResponse("APPANNIE_ACCT = '%s'\nAPPANNIE_PASS = '%s'" % (account.accountName,account.accountPass))
    else:
        return HttpResponse('error')

def releaseAccount(accountName):
    try:
        account = CrawlerAccount.objects.get(accountName=accountName)
    except:
        return False
    else:
        account.isUsed = False
        account.save()
        return True
        
def releaseAllAccounts():
    try:
        accounts = CrawlerAccount.objects.filter(type="appannie")
    except:
        return False
    else:
        for item in accounts:
            item.isUser = False
            item.save()
        return True

