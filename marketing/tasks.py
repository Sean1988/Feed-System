from celery import task
from signl.settings import MAILGUN_API_KEY 
import requests
MAILGUN_URL = "https://api.mailgun.net/v2"


@task(queue='digest-email',ignore_result=True)
def send_simple_message(sender,receiver,subject,content,tag,campaign_id):
    return requests.post(
        "%s/signl.com/messages"%MAILGUN_URL,
        auth=("api", MAILGUN_API_KEY),
        data={"from": sender,
              "to": [receiver],
              "subject": subject,
              "html": content,
              "o:tracking": True,
              "o:tracking-clicks":True,
              "o:tracking-opens" : True,
              "o:tag": tag,
              "o:campaign": campaign_id
              }).content
