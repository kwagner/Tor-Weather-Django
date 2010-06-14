from django.db import models
from django.core.mail import send_mail
import datetime
import TorCtl.TorCtl
import socket
#import weather.config
from weather.weatherapps import emails
import base64

# Supposedly required to make class methods.
# This is called on methods after their definitions.
class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable

class Router(models.Model):
    fingerprint = models.CharField(max_length=200)
    name = models.CharField(max_length=100)
    welcomed = models.BooleanField()
    last_seen = models.DateTimeField('date last seen')
    
    def __unicode__(self):
        return self.fingerprint

    def add_new_router(fingerprint, name, welcomed=False, 
                       last_seen=datetime.datetime.now()):
        routr = Router(fingerprint = fingerprint, name = name, 
                       welcomed = welcomed)
        routr.save()
        return routr

    # Supposedly makes add_new_router a class method.
    add_new_router = Callable(add_new_router)

class Subscriber(models.Model):
    email = models.EmailField(max_length=75)
    router = models.ForeignKey(Router)
    confirmed = models.BooleanField()

    #change this when more is known?
    confirm_auth = models.CharField(max_length=250) 
    unsubs_auth = models.CharField(max_length=250)
    pref_auth = models.CharField(max_length=250)

    sub_date = models.DateField()

    def __unicode__(self):
        return self.email

    def add_new_subscriber(email, router_id, confirmed=False,
            confirm_auth="", unsubs_auth="", pref_auth="",
            sub_date=datetime.datetime.now()):
        
        g = StringGenerator()
        if confirm_auth == "":
            confirm_auth = g.get_rand_string()
        if unsubs_auth == "":
            unsubs_auth = g.get_rand_string()
        if pref_auth == "":
            pref_auth = g.get_rand_string()
        
        subr = Subscriber(email = email, router = router_id,
                confirmed = confirmed, confirm_auth = confirm_auth,
                unsubs_auth = unsubs_auth, pref_auth = pref_auth, 
                sub_date = sub_date)
        subr.save()
        return subr
    
    # supposedly makes add_new_subscriber() a class method
    add_new_subscriber = Callable(add_new_subscriber)
        
class SubscribeForm(forms.Form):
    email = forms.EmailField(max_length=75)
    router_id = forms.CharField(max_length=200)
    grace_pd = forms.IntegerField(default=1)

class Subscription(models.Model):
    subscriber = models.ForeignKey(Subscriber)
    name = models.CharField(max_length=200)
    threshold = models.CharField(max_length=200)
    grace_pd = models.IntegerField()
    emailed = models.BooleanField()
    triggered = models.BooleanField()
    last_changed = models.DateTimeField('date of last change')
    
    def __unicode__(self):
        return self.name

    def should_email()
        time_since_changed = datetime.datetime.now() - last_changed
        hours_since_changed = time_since_changed.hours / 3600
        if triggered and not emailed and \
                (hours_since_changed > grace_pd):
            return true
        else:
            return false

    def add_new_subscription(subscriber_id, name, threshold, grace_pd = 5,
                             emailed = False, triggered = False,
                             last_changed = datetime.datetime.now()):
        subn = Subscription(subscriber = subscriber_id, name = name,
                            threshold = threshold, grace_pd = grace_pd,
                            emailed = emailed, triggered = triggered,
                            last_changed = last_changed)
        subn.save()
        return subn

    # Supposedly makes add_new_subscription a class method.
    add_new_subscription = Callable(add_new_subscription)

class Emailer(models.Model):
    """A class for sending email messages"""
    
    def send_generic_mail(recipient, messageType, 

    def send_generic_mail(recipient, subject, messageText, 
                          sender = 'tor-ops@torproject.org'):
        """
        Send an email to single recipient recipient with subject subject and
        message messageText, from sender with default value 
        tor-ops@torproject.org.
        
        @type recipient: string
        @param recipient: The recipient of this email.
        @type subject: string
        @param subject: The subject of this email.
        @type messageText: string
        @param messageText: The content of this email.
        @type sender: string
        @param sender: The sender of this email. Default value of 
                       'tor-ops@torporject.org'.
        """

        to = [recipient] #send_mail takes a list of recipients
        send_mail('[Tor Weather]' + subject, messageText, sender, to,
                  fail_silently=True)

    def send_email(recipient, messageType):
        """
        Send an email to a single recipient recipient of form specified
        by messageType (which determines the subject and message text).
        """

        messageTextDict = {'confirmation' : emails.CONFIRMATION_MAIL,
                           'confirmed'    : emails.CONFIRMED_MAIL,
                           'node_down'    : emails.NODE_DOWN_MAIL,
                           'out_of_date'  : emails.OUT_OF_DATE_MAIL,
                           't_shirt'      : emails.T_SHIRT_MAIL,
                           'welcome'      : emails.WELCOME_MAIL,}
        subjectDict = {'confirmation' : 'Confirmation Needed',
                       'confirmed'    : 'Confirmation Successful',
                       'node_down'    : 'Node Down!',
                       'out_of_date'  : 'Node Out of Date!',
                       't_shirt'      : 'Congratulations! Have a t-shirt!',
                       'welcome'      : 'Welcome to Tor!'.}

        messageText = emailDict[messageType]
        subjectText = subjectDict[messageType]

        send_generic_mail(recipient, subjectText, messageText)

class StringGenerator:
    def get_rand_string():
        # Code pulled from original Weather, not sure why it cuts off
        # the last character
        r = base64.urlsafe_b64encode(os.urandom(18))[:-1]

        # some email clients don't like URLs ending in -
        if r.endswith("-"):
            r = r.replace("-", "x")
        return r

class CheckSubscriptions:
    def __init__(self)
        self.pinger = TorPing()

    def check_node_down():
        subscriptions = Subscription.objects.filter(name = "node_down")
        for subscription in subscriptions:
            is_up = pinger.ping(subscription.node_id) 
            if is_up:
                if subscription.triggered:
                   subscription.triggered = False
                   subscription.last_changed = datetime.datetime
            else:
                if subscription.triggered:
                    if subscription.should_email():
                        recipient = subscription.subscriber.email
                        Emailer.send_node_down_email(recipient)
                        subscription.emailed = True 
                else:
                    subscription.triggered = True
                    subscription.last_changed = datetime.datetime

    def check_out_of_date():
# -------------------------------------------------------------------------
# Put code here.
# -------------------------------------------------------------------------

    def check_below_bandwidth():
# -------------------------------------------------------------------------
# Put code here.
# -------------------------------------------------------------------------

    def check_earn_tshirt():
# -------------------------------------------------------------------------
# Put code here.
# -------------------------------------------------------------------------

class TorPing:
    "Check to see if various tor nodes respond to SSL hanshakes"
    def __init__(self, control_host = "127.0.0.1", control_port = 9051):

        "Keep the connection to the control port lying around"
        self.control_host = control_host
        self.control_port = control_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((control_host,control_port))
        except:
            errormsg = "Could not connect to Tor control port" + \
                       "Is Tor running on %s with its control port opened on %s?" \
                        % (control_host, control_port)
            logging.error(errormsg)
            print >> sys.stderr, errormsg
            raise
        self.control = TorCtl.Connection(self.sock)
        self.control.authenticate(weather.config.authenticator)
    def __del__(self):
        self.sock.close()
        del self.sock
        self.sock = None                # prevents double deletion exceptions

        # it would be better to fix TorCtl!
        try:
            self.control.close()
        except:
            pass

        del self.control
        self.control = None

    def ping(self, nodeId):
        "Let's see if this tor node is up by only asking Tor."
        try:
            info = self.control.get_info(str("ns/id/" + nodeId))
        except TorCtl.ErrorReply, e:
            # If we're getting here, we're likely seeing:
            # ErrorReply: 552 Unrecognized key "ns/id/46D9..."
            # This means that the node isn't recognized by 
            return False

        except:
            return False

        # If we're here, we were able to fetch information about the router
        return True
