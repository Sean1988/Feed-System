from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from datetime import datetime
from uuslug import uuslug
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

class MyUserManager(BaseUserManager):


    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=MyUserManager.normalize_email(email)
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(email,
            password=password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True,
    )
    slug = models.CharField(max_length=150, unique=True, blank = True, null = True )    
    tier = models.IntegerField( default = 0 )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150)
    industry = models.CharField(max_length=150)
    headline = models.CharField(max_length=100, blank=True, null=True)
    linkedinId = models.CharField(max_length=100, blank=True,null=True)
    icon = models.CharField(max_length = 200, blank=True,null=True)
    stripeId = models.CharField(max_length=100, blank=True,null=True)
    
    comp = models.ForeignKey('company.Company', related_name="comp", blank=True, null=True)
    tracker = models.ManyToManyField('company.Company', blank=True, null=True )
    tag = models.ManyToManyField('company.Tag', blank=True, null=True )

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_company = models.BooleanField(default=False) 
    register_time = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    #email setting
    wkFd = models.BooleanField(default=True)
    wkIdsy = models.BooleanField(default=True)
    idsyAlert = models.BooleanField(default=True)
    momAlert = models.BooleanField(default=True)
    trackSug = models.BooleanField(default=True)


    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    #REQUIRED_FIELDS = ['slug','first_name','last_name']

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # Return user first_name
        return self.first_name

    def __unicode__(self):
        return self.email
    
    def isPaidUser(self):
        if self.tier == 1:
            return True
        else:
            return False
    
    def save(self, *args, **kwargs):
        if self.slug == None and self.first_name !=None and self.first_name != "":
            self.slug = uuslug(self.first_name, instance=self)
        super(MyUser, self).save(*args, **kwargs)

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


