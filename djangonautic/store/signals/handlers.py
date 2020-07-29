from paypal.standard.models import ST_PP_COMPLETED, ST_PP_FAILED
from paypal.standard.ipn.signals import valid_ipn_received, invalid_ipn_received
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

def payment_receiver(sender, **kwargs):
    ipn_obj = sender
    User = get_user_model()
    userName = ipn_obj.payer_id
    email = ipn_obj.payer_email
    group = Group.objects.get(name=ipn_obj.item_name)
    current_site = Site.objects.get_current().domain
    
    if ipn_obj.txn_type == "subscr_signup":
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            user = None
        if user is not None:
            mail_subject = "Account renewal was successful"
            message = render_to_string('mails/acc_renewal.html', {
                'firstName': ipn_obj.first_name,
                'lastName': ipn_obj.last_name,
                'domain': current_site
            })
            mail = EmailMessage(mail_subject, message, settings.EMAIL_HOST_USER, to=[email])
            mail.send()
            print("User account renewal was successful!")
        else:
            user = User.objects.create_user(userName, email, None)
            user.first_name = ipn_obj.first_name
            user.last_name = ipn_obj.last_name
            user.is_active = False
            user.save()
            group.user_set.add(user)
            mail_subject = "Welcome to ScoutAfricanTalents"
            message = render_to_string('mails/signup-confirmation.html', {
                'firstname': ipn_obj.first_name,
                'lastname': ipn_obj.last_name
            })
            mail = EmailMessage(mail_subject, message, settings.EMAIL_HOST_USER, to=[email])
            mail.send()
            print("New user signup was successful!")
   
    elif ipn_obj.txn_type == "subscr_payment":
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            user = None
        if user is not None:
            user.is_active = True
            user.save()
            mail_subject = "Payment Confirmation"
            message = render_to_string('mails/payment-confirmed.html', {
                    'firstname':user.first_name,
                    'lastname':user.last_name,
                    'domain':current_site
            })
            mail = EmailMessage(mail_subject, message, settings.EMAIL_HOST_USER, to=[user.email])
            mail.send()
            print("User payment was confirmed!")
        else:
            mail_subject = "Payment Received"
            message = render_to_string('mails/payment-received.html', {
                'firstname':ipn_obj.first_name,
                'lastname':ipn_obj.last_name,
                'domain':current_site
            })
            mail = EmailMessage(mail_subject, message, settings.EMAIL_HOST_USER, to=[email])
            mail.send()
            print("User payment was confirmed before signup link was sent!")
    
    elif ipn_obj.txn_type == "subscr_eot":
        try:
            user = User.objects.get(email=email)
            if user.is_active == True:
                user.is_active = False
                user.save()
        except ObjectDoesNotExist:
            user = None
        mail_subject = "Your Subscription Has Expired"
        message = render_to_string('mails/end-of-membership.html', {
                'firstname':user.first_name,
                'lastname':user.last_name,
                'domain':current_site
        })
        mail = EmailMessage(mail_subject, message, settings.EMAIL_HOST_USER, to=[user.email])
        mail.send()
        print("User Account has expired!")

    elif ipn_obj.txn_type == "subscr_failed":
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            user = None
        mail_subject = "Your Payment Was Unsuccessful"
        message = render_to_string('mails/subscription_failed.html', {
                'firstname':user.first_name,
                'lastname':user.last_name,
                'domain':current_site
        })
        mail = EmailMessage(mail_subject, message, settings.EMAIL_HOST_USER, to=[user.email])
        mail.send()
        print("We were unable to process the user's payment!") 

    else:
        print("User creation failed!!!")
valid_ipn_received.connect(payment_receiver)