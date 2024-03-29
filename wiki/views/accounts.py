# -*- coding: utf-8 -*-
"""Here is a very basic handling of accounts.
If you have your own account handling, don't worry, 
just switch off account handling in 
settings.WIKI_ACCOUNT_HANDLING = False

and remember to set
settings.WIKI_SIGNUP_URL = '/your/signup/url'
SETTINGS.LOGIN_URL
SETTINGS.LOGOUT_URL
"""

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from account.models import MyUser
User = MyUser
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic.base import View
from django.views.generic.edit import CreateView, FormView

from wiki import forms
from wiki.conf import settings


class Signup(CreateView):
    model = User
    form_class = forms.UserCreationForm
    template_name = "wiki/accounts/signup.html"
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_anonymous():
            return redirect('wiki:root')    
        if not settings.ACCOUNT_HANDLING:
            return redirect(settings.SIGNUP_URL)
        return super(Signup, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = CreateView.get_context_data(self, **kwargs)
        context['honeypot_class'] = context['form'].honeypot_class
        context['honeypot_jsfunction'] = context['form'].honeypot_jsfunction
        return context
    
    def get_success_url(self, *args):
        messages.success(self.request, _(u'You are now signed up... and now you can sign in!'))
        return reverse("wiki:login")


class Logout(View):
    
    def dispatch(self, request, *args, **kwargs):
        if not settings.ACCOUNT_HANDLING:
            return redirect(settings.LOGOUT_URL)
        return super(Logout, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        messages.info(request, _(u"You are no longer logged in. Bye bye!"))
        return redirect("wiki:root")


class Login(FormView):
    
    form_class = AuthenticationForm
    template_name = "wiki/accounts/login.html"
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_anonymous():
            return redirect('wiki:root')    
        if not settings.ACCOUNT_HANDLING:
            return redirect(settings.LOGIN_URL)
        return super(Login, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        self.request.session.set_test_cookie()
        kwargs = super(Login, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def post(self, request, *args, **kwargs):
        self.referer = request.session.get('login_referer', '')
        return FormView.post(self, request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        self.referer = request.META.get('HTTP_REFERER', '')
        request.session['login_referer'] = self.referer
        return FormView.get(self, request, *args, **kwargs)
    
    def form_valid(self, form, *args, **kwargs):
        auth_login(self.request, form.get_user())
        messages.info(self.request, _(u"You are now logged in! Have fun!"))
        if self.request.GET.get("next", None):
            return redirect(self.request.GET['next'])
        if django_settings.LOGIN_REDIRECT_URL:
            return redirect(django_settings.LOGIN_REDIRECT_URL)
        else:
            if not self.referer:
                return redirect("wiki:root")
            return redirect(self.referer)
    
