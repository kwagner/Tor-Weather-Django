"""
The models module handles the bulk of Tor Weather's database management. The 
module contains three models that correspond to database tables (L{Subscriber}, 
L{Subscription}, and L{Router}) as well as two form classes (L{SubscribeForm} 
and L{PreferencesForm}), which specify the fields to appear on the sign-up 
and change preferences pages.
"""
from datetime import datetime
import base64
import os

import emails
from weather.config import url_helper

from django.db import models
from django import forms

from copy import copy

class Router(models.Model):
    """A model that stores information about every router on the Tor network.
    If a router hasn't been seen on the network for at least one year, it is
    removed from the database.  
    @type fingerprint: str
    @ivar fingerprint: The router's fingerprint.
    @type name: str
    @ivar name: The name associated with the router.
    @type welcomed: bool
    @ivar welcomed: true if the router operater has received a welcome email,
                    false if they haven't. Default value is C{False}.
    @type last_seen: datetime
    @ivar last_seen: The most recent time the router was listed on a consensus 
                     document. Default value is C{datetime.now()}.
    @type up: bool
    @ivar up: C{True} if this router was up last time a new network consensus
              was published, false otherwise. Default value is C{True}.
    @type exit: bool
    @ivar exit: C{True} if this router accepts exits to port 80, C{False} if
        not.
    """

    fingerprint = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    welcomed = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=datetime.now)
    up = models.BooleanField(default=True)
    exit = models.BooleanField()

    def __unicode__(self):
        return self.fingerprint


class SubscriberManager(models.Manager):
    """In Django, each model class has at least one Manager (by default,
    there is one named 'objects' for each model). The Manager acts as the
    interface through which database query operations are provided to the 
    models. The SubscriberManager class is a custom Manager for the Subscriber
    model, which contains the method get_rand_string to generate a random
    string for user authentication keys."""

    @staticmethod
    def get_rand_string():
        """Returns a random, url-safe string of 24 characters (no '+' or '/'
        characters). The generated string does not end in '-'.
        
        @rtype: str
        @return: A randomly generated, 24 character string (url-safe).
        """

        r = base64.urlsafe_b64encode(os.urandom(18))

        # some email clients don't like URLs ending in -
        if r.endswith("-"):
            r = r.replace("-", "x")
        return r

          
class Subscriber(models.Model):
    """
    A model to store information about Tor Weather subscribers, including their
    authorization keys.

    @type email: str
    @ivar email: The subscriber's email.
    @type router: Router
    @ivar router: A foreign key link to the router model corresponding to the
        node this subscriber is watching.
    @type confirmed: bool
    @ivar confirmed: True if the subscriber has confirmed the subscription by
        following the link in their confirmation email and False otherwise. 
        Default value upon creation is C{False}.
    @type confirm_auth: str
    @ivar confirm_auth: This user's confirmation key, which is incorporated into
        the confirmation url.
    @type unsubs_auth: str
    @ivar unsubs_auth: This user's unsubscribe key, which is incorporated into 
        the unsubscribe url.
    @type pref_auth: str
    @ivar pref_auth: The key for this user's Tor Weather preferences page.
    @type sub_date: datetime.datetime
    @ivar sub_date: The date this user subscribed to Tor Weather. Default value
                    upon creation is datetime.now().
    """
    email = models.EmailField(max_length=75)
    router = models.ForeignKey(Router)
    confirmed = models.BooleanField(default = False)
    confirm_auth = models.CharField(max_length=250, 
                    default=SubscriberManager.get_rand_string) 
    unsubs_auth = models.CharField(max_length=250, 
                    default=SubscriberManager.get_rand_string)
    pref_auth = models.CharField(max_length=250, 
                    default=SubscriberManager.get_rand_string)

    sub_date = models.DateTimeField(default=datetime.now)

    objects = SubscriberManager()

    def __unicode__(self):
        return self.email


class SubscriptionManager(models.Manager):
    """The custom Manager for the Subscription class. The Manager contains
    a method to get the number of hours since the time stored in the
    'last_changed' field in a Subscription object.
    """

    @staticmethod
    def hours_since_changed(last_changed):
        """Returns the time that has passed since the datetime parameter
        last_changed in hours.

        @type last_changed: datetime.datetime
        @param last_changed: The date and time of the most recent change
            for some flag.
        @rtype: int
        @return: The number of hours since last_changed.
        """
        time_since_changed = datetime.now() - last_changed
        hours_since_changed = (time_since_changed.hours * 24) + \
                              (time_since_changed.seconds / 3600)
        return hours_since_changed
    

class Subscription(models.Model):
    """The model storing information about a specific subscription. Each type
    of email notification that a user selects generates a new subscription. 
    For instance, each subscriber who elects to be notified about low bandwidth
    will have a low_bandwidth subscription.
    
    @ivar subscriber: A link to the subscriber model representing the owner
        of this subscription.
    @type emailed: bool
    @ivar emailed: True if the user has been emailed about the subscription
        (trigger must also be True), False if the user has not been emailed. 
        Default upon creation is C{False}.
    """
    subscriber = models.ForeignKey(Subscriber)
    emailed = models.BooleanField(default=False)

    # In Django, Manager objects handle table-wide methods (i.e filtering)
    objects = SubscriptionManager()

class NodeDownSub(Subscription):
    """A subscription class for node-down subscriptions, which send 
    notifications to the user if their node is down for the downtime grace
    period they specify. 

    @type grace_pd: int
    @ivar grace_pd: The amount of time (hours) before a notification is sent
        after a node is seen down.
    """
    triggered = models.BooleanField(default=False)
    grace_pd = models.IntegerField()
    last_changed = models.DateTimeField(default=datetime.now)

    def is_grace_passed(self):
        """Check if the grace period has passed for this subscription
        
        @rtype: bool
        @return: C{True} if C{triggered} and 
        C{SubscriptionManager.hours_since_changed()}, otherwise C{False}.
        """

        if self.triggered and SubscriptionManager.hours_since_changed() >= \
                grace_pd:
            return True
        else:
            return False

class VersionSub(Subscription):
    """

    @type threshold: str
    @ivar threshold: The threshold for sending a notification (i.e. send a 
        notification if the version is obsolete vs. out of date)
    """
# -----------------------------------------------------------------------
# FILL IN LATER, FIX DOCUMENTATION
# -----------------------------------------------------------------------

    #only send notifications if the version is of type notify_type
    notify_type = models.CharField(max_length=250)


class BandwidthSub(Subscription):    
    """
    """
    grace_pd = models.IntegerField(default = 1)
    last_changed = models.DateTimeField(default=datetime.now)
    triggered = models.BooleanField(default=False)
    threshold = models.IntegerField(default = 20)

    def is_grace_passed(self):
        """Check if the grace period has passed for this subscription

        @rtype: bool
        @return: C{True} if C{triggered} and 
        C{SubscriptionManager.hours_since_changed()}, otherwise C{False}.
        """

        if self.triggered and SubscriptionManager.hours_since_changed() >= \
                grace_pd:
            return True
        else:
            return False

class TShirtSub(Subscription):
    """A subscription class for T-shirt notifications. An email is sent
    to the user if the router they're monitoring has earned them a T-shirt.
    The router must be running for 61 days (2 months). If it's an exit node,
    it's avg bandwidth must be at least 100 KB/s. Otherwise, it must be at 
    least 500 KB/s.
    
    @type avg_bandwidth: int
    @ivar avg_bandwidth: The router's average bandwidth
    @type hours_since_triggered: int
    @ivar hours_since_triggered: The hours this router has been up"""
    avg_bandwidth = models.IntegerField(default = 0)
    last_changed = models.DateTimeField(default = datetime.now)

    def get_hours_since_triggered(self):
        """Returns the time in hours that the router has been up."""
        if self.triggered == False:
            return 0
        time_since_triggered = datetime.now() - self.last_changed
        # timedelta objects only store days, seconds, and microseconds :(
        hours = time_since_triggered.seconds / 3600 + \
                time_since_triggered.days * 24
        return hours

    def should_email(hours_up):
        """Returns true if the router being watched has been up for 1464 hours
        (61 days, or approx 2 months). If it's an exit node, the avg bandwidth
        must be above 100 KB/s. If not, it must be > 500 KB/s.
        
        @type hours_up: int
        @param hours_up: The hours that this router has been up (0 if the
            router was last seen down)
        @rtype: bool
        @return: C{True} if the user earned a T-shirt, C{False} if not.
        """
        if not self.emailed and self.triggered and hours_up >= 1464:
            if self.subscriber.router.exit:
                if self.avg_bandwidth > 100000:
                    return True
            else:
                if self.avg_bandwidth > 500000:
                    return True
        return False

class GenericForm(forms.Form):
    """The basic form class that is inherited by the SubscribeForm class
    and the PreferencesForm class.
   
    @type _INIT_GET_NODE_DOWN: Bool
    @cvar _INIT_GET_NODE_DOWN: The initial value of the get_node_down checkbox
        when the form is loaded.
    @type _INIT_GET_VERSION: Bool
    @cvar _INIT_GET_VERSION: The initial value of the get_version checkbox when
        the form is loaded.
    @type _INIT_GET_BAND_LOW: Bool
    @cvar _INIT_GET_BAND_LOW: The initial value of the get_band_low checkbox
        when the form is loaded.
    @type _MAX_NODE_DOWN_GRACE_PD: int
    @cvar _MAX_NODE_DOWN_GRACE_PD: The maximum node down grace period in hours
    @type _MIN_NODE_DOWN_GRACE_PD: int
    @cvar _MIN_NODE_DOWN_GRACE_PD: The minimum node down grace period in hours
    @type _MAX_BAND_LOW_GRACE_PD: int
    @cvar _MAX_BAND_LOW_GRACE_PD: The maximum low bandwidth grace period in 
        hours
    @type _MIN_BAND_LOW_GRACE_PD: int
    @cvar _MIN_BAND_LOW_GRACE_PD: The minimum low bandwidth grace period in 
        hours
    @type _INIT_BAND_LOW_THRESHOLD: int
    @cvar _INIT_BAND_LOW_THRESHOLD: The initial low bandwidth threshold (KB/s)
    @type _MIN_BAND_LOW_THRESHOLD: int
    @cvar _MIN_BAND_LOW_THRESHOLD: The minimum low bandwidth threshold (KB/s)
    @type _MAX_BAND_LOW_THRESHOLD: int
    @cvar _MAX_BAND_LOW_THRESHOLD: The maximum low bandwidth threshold (KB/s)
    @type get_node_down: bool
    @ivar get_node_down: C{True} if the user wants to subscribe to node down 
        notifications, C{False} if not.
    @type node_down_grace_pd: int
    @ivar node_down_grace_pd: Time before receiving a node down notification in 
        hours. Default = 1. Range = 1-4500.
    @type get_version: bool
    @ivar get_version: C{True} if the user wants to receive version 
        notifications about their router, C{False} if not.
    @type version_type: str
    @ivar version_type: The type of version notifications the user 
        wants
    @type get_band_low: bool
    @ivar get_band_low: C{True} if the user wants to receive low bandwidth 
        notifications, C{False} if not.
    @type band_low_threshold: int
    @ivar band_low_threshold: The user's threshold (in KB/s) for low bandwidth
        notifications. Default = 20 KB/s.
    @type band_low_grace_pd: int
    @ivar band_low_grace_pd: The number of hours of low bandwidth below 
        threshold for sending a notification. Default = 1. Range = 1-4500.
    @type get_t_shirt: bool
    @ivar get_t_shirt: C{True} if the user wants to receive a t-shirt 
        notification, C{False} if not.
    """
    
    _INIT_GET_NODE_DOWN = True
    _INIT_GET_VERSION = False
    _INIT_GET_BAND_LOW = False
    _INIT_NODE_DOWN_GRACE_PD = 1
    _MAX_NODE_DOWN_GRACE_PD = 4500
    _MIN_NODE_DOWN_GRACE_PD = 1
    _INIT_BAND_LOW_GRACE_PD = 1
    _MAX_BAND_LOW_GRACE_PD = 4500
    _MIN_BAND_LOW_GRACE_PD = 1
    _INIT_BAND_LOW_THRESHOLD = 20
    _MIN_BAND_LOW_THRESHOLD = 0
    _MAX_BAND_LOW_THRESHOLD = 100000

    get_node_down = forms.BooleanField(initial=_INIT_GET_NODE_DOWN,
            required=False,
            label='Receive notifications when node is down')
    node_down_grace_pd = forms.IntegerField(initial=_INIT_NODE_DOWN_GRACE_PD,
            required=False,
            max_value=_MAX_NODE_DOWN_GRACE_PD,
            min_value=_MIN_NODE_DOWN_GRACE_PD,
            label='How many hours of downtime before \
                       we send a notifcation?',
            help_text='Enter a value between 1 and 4500 (roughly six months)')
    
    get_version = forms.BooleanField(initial=_INIT_GET_VERSION,
            required=False,
            label='Receive notifications when node is out of date')
    version_type = forms.ChoiceField(required=False,
            choices=((u'UNRECOMMENDED', u'Recommended Updates'),
                     (u'OBSOLETE', u'Required Updates')),
                label='For what kind of updates would you like to be \
                        notified?',
                help_text='\'Recommended Updates\' will send a notification \
                        when the node\'s version of Tor becomes \
                        unrecommended; \'Required Updates\' \
                        will send a notification when the \
                        node\'s version of Tor becomes obsolete.')
    
    get_band_low = forms.BooleanField(initial=_INIT_GET_BAND_LOW,
            required=False,
            label='Receive notifications when node has low bandwidth')
    band_low_threshold = forms.IntegerField(initial=_INIT_BAND_LOW_THRESHOLD,
            required=False, max_value=_MAX_BAND_LOW_THRESHOLD,
            min_value=_MIN_BAND_LOW_THRESHOLD, label='What critical bandwidth \
            would you like to be informed of?')
    band_low_grace_pd = forms.IntegerField(initial=_INIT_BAND_LOW_GRACE_PD,
            required=False, max_value=_MAX_BAND_LOW_GRACE_PD,
            min_value=_MIN_BAND_LOW_GRACE_PD,
            label='How many hours of low bandwidth before \
                       we send a notification?',
            help_text='Enter a value between 1 and 4500 (roughly six \
                       months); default value is 1 hour.')
    
    get_t_shirt = forms.BooleanField(initial=False, required=False,
            label='Receive notification when node has earned a t-shirt')

    def set_blanks(self, data, errors):
        """Returns the dictionary of errors raised by the form validation that
        checks for required fields; main purpose is to set empty fields to 
        their default valies. Abstracted out of clean() so that form
        subclasses can get the error dictionary. Does not have any side effects
        on the data or errors dictionaries passed in as arguments."""

        # Copies the error dictionary so it doesn't cause any side-effects.
        err = copy(errors)

        # Only sets default values for required fields if their
        # 'parent' checkbox is checked. That is, a default value for fields
        # pertinent to get_node_down is only saved if get_node_down is checked.
        # Was constructed in this way when we wanted blank fields to throw 
        # validation errors, not to submit a default value. It still slightly
        # convenient this way to suppress errors in non-checked areas in case
        # people enter a ridiculous value and then uncheck the box.

        # If the node down subscription box is checked.
        if data['get_node_down']:
            # If there are no other errors for the node_down_grace_pd field and
            # it is empty (either not in cleaned_data, meaning it had an error)
            # or in it as None).
            if 'node_down_grace_pd' not in err \
            and ('node_down_grace_pd' not in data
            or data['node_down_grace_pd'] == None):
                # Sets the value to the default 
                data['node_down_grace_pd'] = \
                        GenericForm._INIT_NODE_DOWN_GRACE_PD
        # If the node down subscription box isn't checked, and there are
        # errors for node_down_grace_pd, then ignore them.
        elif 'node_down_grace_pd' in err:
            del err['node_down_grace_pd']

        # If the band low subscription is checked.
        if data['get_band_low']:
            # If there are no errors for the band_low_grace_pd field and it is
            # empty (either not in cleaned_data or in it as None).
            if 'band_low_grace_pd' not in err \
            and ('band_low_grace_pd' not in data
            or data['band_low_grace_pd'] == None):
                # Sets the value to the default.
                data['band_low_grace_pd'] = \
                        GenericForm._INIT_BAND_LOW_GRACE_PD
            # If there are no errors for the band_low_threshold field and it is
            # empty (either not in claned_data or in it as None).
            if 'band_low_threshold' not in err \
            and ('band_low_threshold' not in data
            or data['band_low_threshold'] == None):
                # Sets the value to the default.
                data['band_low_threshold'] = \
                        GenericForm._INIT_BAND_LOW_THRESHOLD
        # If the band low subscription box isn't checked.
        else:
            # If there are errors for band_low_threshold, then ignore them.
            if 'band_low_threshold' in err:
                del err['band_low_threshold']
            # If there are errors for band_low_grace_pd, then ignore them.
            if 'band_low_grace_pd' in err:
                del err['band_low_grace_pd']

        return err

    def check_if_sub_checked(self, data):
        """Throws a validation error if no subscriptions are checked. 
        Abstracted out of clean() so that there isn't any redundancy in 
        subclass clean() methods."""

        # Ensures that at least one subscription must be checked.
        if not (data['get_node_down'] or
                data['get_version'] or
                data['get_band_low'] or
                data['get_t_shirt']):
            raise forms.ValidationError('You must choose at least one \
                                         type of subscription!')

    def clean(self):
        self._errors = self.set_blanks(self.cleaned_data, self._errors)
        
        self.check_if_sub_checked(self.cleaned_data)

        return self.cleaned_data

    def save_subscriptions(self, subscriber):
        # Create the various subscriptions if they are specified.
        if self.cleaned_data['get_node_down']:
            node_down_sub = NodeDownSub(subscriber=subscriber,
                    grace_pd=self.cleaned_data['node_down_grace_pd'])
            print node_down_sub
            node_down_sub.save()
        if self.cleaned_data['get_version']:
            version_sub = VersionSub(subscriber=subscriber,
                    notify_type = self.cleaned_data['version_threshold'])
            version_sub.save()
        if self.cleaned_data['get_band_low']:
            band_low_sub = BandwidthSub(subscriber=subscriber,
                    threshold=self.cleaned_data['band_low_threshold'],
                    grace_pd=self.cleaned_data['band_low_grace_pd'])
            band_low_sub.save()
        if self.cleaned_data['get_t_shirt']:
            t_shirt_sub = TShirtSub(subscriber=subscriber)
            t_shirt_sub.save()

class SubscribeForm(GenericForm):
    """Inherits from L{GenericForm}. The SubscribeForm class contains
    all the fields in the GenericForm class and additional fields for 
    the user's email and the fingerprint of the router the user wants to
    monitor.
    
    @type email_1: EmailField
    @ivar email_1: A field for the user's email 
    @type email_2: EmailField
    @ivar email_2: A field for the user's email (enter twice for security)
    @type fingerprint: str
    @ivar fingerprint: The fingerprint of the router the user wants to 
        monitor.
    """
    email_1 = forms.EmailField(label='Enter Email:',
            max_length=75)
    email_2 = forms.EmailField(label='Re-enter Email:',
            max_length=75)
    fingerprint = forms.CharField(label='Node Fingerprint:',
            max_length=50)

    def clean(self):
        """"""
        
        # Calls the same helper methods used in the GenericForm clean() method.
        data = self.cleaned_data
        self._errors = GenericForm.set_blanks(self, data, self._errors)
        GenericForm.check_if_sub_checked(self, data)

        # Makes sure email_1 and email_2 match and creates error messages
        # if they don't as well as deleting the cleaned data so that it isn't
        # erroneously used.
        if 'email_1' in data and 'email_2' in data:
            email_1 = data['email_1']
            email_2 = data['email_2']

            if not email_1 == email_2:
                msg = 'Email addresses must match.'
                self._errors['email_1'] = self.error_class([msg])
                self._errors['email_2'] = self.error_class([msg])
                
                del data['email_1']
                del data['email_2']
       
        return data

    def clean_fingerprint(self):
        """Uses Django's built-in 'clean' form processing functionality to
        test whether the fingerprint entered is a router we have in the
        current database, and presents an appropriate error message if it
        isn't (along with helpful information).
        """
        fingerprint = self.cleaned_data.get('fingerprint')
        fingerprint.replace(' ', '')

        if self.is_valid_router(fingerprint):
            return fingerprint
        else:
            info_extension = url_helper.get_fingerprint_info_ext(fingerprint)
            msg = 'We could not locate a Tor node with that fingerprint. \
                   (<a href=%s>More info</a>)' % info_extension
            raise forms.ValidationError(msg)

    def is_valid_router(self, fingerprint):
        """Helper function to check if a router exists in the database.
        """
        router_query_set = Router.objects.filter(fingerprint=fingerprint)

        if router_query_set.count() == 0:
            return False
        else:
            return True

    def save_subscriber(self):
        """Attempts to save the new subscriber, but throws a catchable error
        if a subscriber already exists with the given email and fingerprint.
        PRE-CONDITION: fingerprint is a valid fingerprint for a 
        router in the Router database.
        """

        email = self.cleaned_data['email_1']
        fingerprint = self.cleaned_data['fingerprint']
        router = Router.objects.get(fingerprint=fingerprint)

        # Get all subscribers that have both the email and fingerprint
        # entered in the form. 
        subscriber_query_set = Subscriber.objects.filter(email=email, 
                                    router__fingerprint=fingerprint)
        
        # Redirect the user if such a subscriber exists, else create one.
        if subscriber_query_set.count() > 0:
            subscriber = subscriber_query_set[0]
            url_extension = url_helper.get_error_ext('already_subscribed', 
                                               subscriber.pref_auth)
            raise Exception(url_extension)
            #raise UserAlreadyExistsError(url_extension)
        else:
            subscriber = Subscriber(email=email, router=router)
            subscriber.save()
            return subscriber
            
class PreferencesForm(GenericForm):
   pass 