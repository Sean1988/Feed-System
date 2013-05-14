from django.db import models
from django.contrib import admin
from account.tools import * 
from uuslug import uuslug
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey

class Tag(MPTTModel):
    tagId = models.IntegerField( default = 0 )
    tagType = models.CharField( max_length=100 )
    tagName = models.CharField( max_length=200 )
    keywords = models.CharField( max_length=300 )
    isBlastoff = models.BooleanField(default=False)
    slug =  models.CharField( max_length=200, unique=True, blank = True, null = True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    fetched = models.IntegerField(default=0)
    companyNum = models.IntegerField(default=0)


    class MPTTMeta:
        order_insertion_by = ['tagName']

    def __unicode__(self):
        return str(self.tagName)

class Company(models.Model):
    companyId = models.IntegerField( default = 0 )
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL)
    cbpermalink = models.CharField( max_length=100, blank = True, null = True )
    angelListSlug =  models.CharField( max_length=100, blank = True, null = True )
    name = models.CharField( max_length=100, blank = True, null = True )
    slug = models.CharField(max_length=150, unique=True, blank = True, null = True )
    website = models.CharField( max_length=300, blank = True, null = True )
    linkedInId = models.IntegerField( default = 0 )
    defaultTag = models.ForeignKey(Tag, related_name="defaultTag", blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, null=True )
    twitter = models.CharField( max_length=300, blank = True, null = True )
    appleStore = models.CharField( max_length=500, blank = True, null = True )
    googlePlay = models.CharField( max_length=500, blank = True, null = True )
    growth = models.FloatField( default = 0 )
    icon = models.URLField(blank = True, null = True)
    thumb = models.URLField(blank = True, null = True)
    smooth = models.FloatField(default = 0)
    rank = models.IntegerField( default = 999999 )
    email = models.EmailField(max_length=255,blank = True, null = True ) 
    phoneNumber = models.CharField( max_length=50, blank = True, null = True )
    overview = models.TextField( max_length=15000, blank = True, null = True )
    totalFunding = models.BigIntegerField( default=0 )

    hasUser = models.BooleanField(default=False)
    justLaunched = models.BooleanField(default=False)
    hasApp = models.BooleanField(default=False)
    analysed =  models.BooleanField(default=False)
    linkedinFetched =  models.BooleanField(default=False)        
    appFetched =  models.BooleanField(default=False)
    fetched = models.IntegerField( default = 0 )
    emailSent =  models.BooleanField(default=False)

    def __unicode__(self):
        try:
            return str(self.name)
        except:
            return "company" 

    def save(self, *args, **kwargs):
        if self.email != None and self.admin == None:
            createAdminForCompany(self)
        if self.slug == None and self.name !=None and self.name != "":
            self.slug = uuslug(self.name, instance=self)
        super(Company, self).save(*args, **kwargs)


class Funding(models.Model):
    company = models.ForeignKey( Company )
    roundCode = models.CharField( max_length=100, blank = True, null = True )
    raisedAmount = models.BigIntegerField( default = 0 )
    currency =  models.CharField( max_length=20, blank = True, null = True )
    date = models.DateField( blank=True , null=True)

    def __unicode__(self):
        try:
            return str(self.company.name)+" "+ self.roundCode
        except:
            return self.roundCode
            
class CompanyAdmin(admin.ModelAdmin):
    #list_display = ('first_name', 'last_name', 'email')
    search_fields = ('name', 'website')


class TagAdmin(admin.ModelAdmin):
    #list_display = ('first_name', 'last_name', 'email')                                                                                                                           
    search_fields = ('tagName','tagType')

admin.site.register(Tag,TagAdmin)
admin.site.register(Company,CompanyAdmin)
admin.site.register(Funding)


def calTagCompanyNum():
    tags = Tag.objects.filter(isBlastoff=True)
    for item in tags:
        comps = Company.objects.filter(tags=item)
        item.companyNum = len(comps)
        item.save()
#def syncCompanyToUser():
#    all = Company.objects.filter(email__isnull=False)
#    for item in all:
#        user = User.objects.create_user(email = email, password = password)
