from django.db import models
from django.contrib import admin

class SpotRequest(models.Model):
    request_id = models.CharField( max_length=100 )
    state = models.CharField( max_length=50 )
    startTime = models.DateTimeField(auto_now_add=True)
    endTime =models.DateTimeField(blank = True, null = True)

    def __unicode__(self):
        return str(self.request_id)

class Instance(models.Model):
    instance_id = models.CharField( max_length=100 )
    state = models.CharField( max_length=50 )
    request = models.ForeignKey(SpotRequest)
    startTime = models.DateTimeField(auto_now_add=True)
    endTime =models.DateTimeField(blank = True, null = True)

    def __unicode__(self):
        return str(self.instance_id)

admin.site.register(Instance)
admin.site.register(SpotRequest)
