"""
The models module handles the bulk of Tor Weather's database management. The 
module contains three models that correspond to database tables (L{Subscriber}, 
L{Subscription}, and L{Router}) as well as two form classes (L{SubscribeForm} 
and L{PreferencesForm}), which specify the fields to appear on the sign-up 
and change preferences pages.

@group Helper Functions: insert_fingerprint_spaces, get_rand_string, hours_since_changed
"""
from datetime import datetime
import base64
import os
import re
from copy import copy

from config import url_helper

from django.db import models
from django import forms
from django.core import validators
from django.core.exceptions import ValidationError

def insert_fingerprint_spaces(fingerprint):
    """Insert a space into C{fingerprint} every four characters.

    @type fingerprint: str
    @param fingerprint: A router L{fingerprint}

    @rtype: str
    @return: C{fingerprint} with spaces inserted every four characters.
    """

    return ' '.join(re.findall('.{4}', str(fingerprint)))

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

def hours_since_changed(last_changed):
    """Returns the number of hours passed since C{last_changed}.

    @type last_changed: datetime
    @param last_changed: The datetime of the most recent change
        for some flag.
    @rtype: int
    @return: The number of hours since C{last_changed}.
    """
    time_since_changed = datetime.now() - last_changed
    hours_since_changed = (time_since_changed.hours * 24) + \
                              (time_since_changed.seconds / 3600)
    return hours_since_changed

class Router(models.Model):
    """Model for Tor network routers. Django uses class variables to specify   
    model fields, but these fields are practically used and thought of as
    instance variables, so this documentation will refer to them as such.
    Fields are specified as their django field classes, with parentheses 
    indicating the python type they are validated against and are treated as
    practically.
   
    @type _FINGERPRINT_MAX_LEN: int
    @cvar _FINGERPRINT_MAX_LEN: Maximum valid length for L{fingerprint}
        fields.
    @type _NAME_MAX_LEN: int
    @cvar _NAME_MAX_LEN: Maximum valid length for L{name} fields.
    @type _DEFAULTS: dict {str: various}
    @cvar _DEFAULTS: Dictionary mapping field names to their default
        parameters. These are the values that fields will be instantiated with
        if they are not specified in the field's construction.

    @type fingerprint: CharField (str)
    @ivar fingerprint: The L{Router}'s fingerprint.
    @type name: CharField (str)
    @ivar name: The L{Router}'s name.
    @type welcomed: BooleanField (bool)
    @ivar welcomed: Whether the L{Router} operator has received a welcome
        email.
    @type last_seen: DateTimeField (datetime)
    @ivar last_seen: The most recent time the L{Router} was seen in consensus.
    @type up: BooleanField (bool)
    @ivar up: Whether this L{Router} was up the last time a new consensus
        document was published.
    @type exit: BooleanField (bool)
    @ivar exit: Whether this L{Router} is an exit node (if it accepts exits 
        to port 80).
    """
    
    _FINGERPRINT_MAX_LEN = 40
    _NAME_MAX_LEN = 100
    _DEFAULTS = { 'name': "Unnamed",
                  'welcomed': False,
                  'last_seen': datetime.now,
                  'up': True }

    fingerprint = models.CharField(max_length=_FINGERPRINT_MAX_LEN,
            unique=True)
    name = models.CharField(max_length=_NAME_MAX_LEN,
            default=_DEFAULTS['name'])
    welcomed = models.BooleanField(default=_DEFAULTS['welcomed'])
    last_seen = models.DateTimeField(default=_DEFAULTS['last_seen'])
    up = models.BooleanField(default=_DEFAULTS['up'])
    exit = models.BooleanField()

    def __unicode__(self):
        """Returns a simple description of this L{Router}, namely its L{name}
        and L{fingerprint}.
        
        @rtype: str
        @return: Simple description of L{Router} object.
        """

        return self.name + ": " + self.spaced_fingerprint()

    def spaced_fingerprint(self):
        """Returns the L{fingerprint} for this L{Router} as a string with
        spaces inserted every 4 characters.
        
        @rtype: str
        @return: The L{Router}'s L{fingerprint} with spaces inserted.
        """

        return insert_fingerprint_spaces(self.fingerprint)

class Subscriber(models.Model):
    """Model for Tor Weather subscribers. Django uses class variables to 
    specify model fields, but these fields are practically used and thought of
    as instance variables, so this documentation will refer to them as such.
    Fields are specified as their django field classes, with parentheses
    indicating the python type they are validated against and treated as 
    practically.

    @type _EMAIL_MAX_LEN: int
    @cvar _EMAIL_MAX_LEN: Maximum length for L{email} field.
    @type _AUTH_MAX_LEN: int
    @cvar _AUTH_MAX_LEN: Maximum length for L{confirm_auth}, L{unsubs_auth},
        L{pref_auth}
    @type _DEFAULTS: Dictionary mapping field names to their default
        parameters. These are the values that fields will be instantiated with
        if they are not specified in the field's construction.

    @type email: EmailField (str)
    @ivar email: The L{Subscriber}'s email address.
    @type router: L{Router}
    @ivar router: The L{Router} the L{Subscriber} is subscribed to.
    @type confirmed: BooleanField (bool)
    @ivar confirmed: Whether the user has confirmed their subscription through
        an email confirmation link.
    @type confirm_auth: CharField (str)
    @ivar confirm_auth: Confirmation authorization code.
    @type unsubs_auth: CharField (str)
    @ivar unsubs_auth: Unsubscription authorization code.
    @type pref_auth: CharField (str)
    @ivar pref_auth: Preferences access authorization code.
    @type sub_date: DateTimeField (datetime)
    @ivar sub_date: Datetime at which the L{Subscriber} subscribed.
    """

    _EMAIL_MAX_LEN = 75
    _AUTH_MAX_LEN = 25
    _DEFAULTS = { 'confirmed': False,
                  'confirm_auth': get_rand_string,
                  'unsubs_auth': get_rand_string,
                  'pref_auth': get_rand_string,
                  'sub_date': datetime.now }

    email = models.EmailField(max_length=_EMAIL_MAX_LEN)
    router = models.ForeignKey(Router)
    confirmed = models.BooleanField(default=_DEFAULTS['confirmed'])
    confirm_auth = models.CharField(max_length=_AUTH_MAX_LEN,
            default=_DEFAULTS['confirm_auth'])
    unsubs_auth = models.CharField(max_length=_AUTH_MAX_LEN,
            default=_DEFAULTS['unsubs_auth'])
    pref_auth = models.CharField(max_length=_AUTH_MAX_LEN,
            default=_DEFAULTS['pref_auth'])
    sub_date = models.DateTimeField(default=_DEFAULTS['sub_date'])

    def __unicode__(self):
        """Returns a simple description of this L{Subscriber}, namely
        its L{email}.
        
        @rtype: str
        @return: Simple description of L{Subscriber}.
        """
        return self.email
 
    def _has_sub_type(self, sub_type):
        """Checks if this L{Subscriber} has a L{Subscription} of type
        C{sub_type}.

        @type sub_type: str
        @param sub_type: The type of L{Subscription} to check. This must be the 
            exact name of a subclass of L{Subscription} (L{NodeDownSub},
            L{VersionSub}, L{BandwidthSub}, or L{TShirtSub}).
        @rtype: bool
        @return: Whether this L{Subscriber} has a L{Subscription} of type
            C{sub_type}. Also returns C{False} if C{sub_type} is not a valid
            name of a 
        @return: C{True} if this subscriber object has a L{Subscription} of 
                 C{sub_type}, C{False} otherwise. Also returns C{False} if 
                 C{sub_type} is not a valid name of a L{Subscription} subclass.
        """

        if sub_type == 'NodeDownSub':
            sub = NodeDownSub
        elif sub_type == 'VersionSub':
            sub = VersionSub
        elif sub_type == 'BandwidthSub':
            sub = BandwidthSub
        elif sub_type == 'TShirtSub':
            sub = TShirtSub
        else:
            return False
   
        try:
            sub.objects.get(subscriber = self)
        except sub.DoesNotExist:
            return False
        except Exception, e:
            raise e
        else:
            return True

    def has_node_down_sub(self):
        """Checks if this L{Subscriber} has a L{NodeDownSub}.

        @rtype: bool
        @return: Whether a L{NodeDownSub} exists for this L{Subscriber}.
        """
        
        return self._has_sub_type('NodeDownSub')

    def has_version_sub(self):
        """Checks if this L{Subscriber} has a L{VersionSub}.
        
        @rtype: bool
        @return: Whether a L{VersionSub} exists for this L{Subscriber}.
        """

        return self._has_sub_type('VersionSub')

    def has_bandwidth_sub(self):
        """Checks if this L{Subscriber} has a L{BandwidthSub}.

        @rtype: bool
        @return: Whether a L{BandwidthSub} exists for this L{Subscriber}.
        """

        return self._has_sub_type('BandwidthSub')

    def has_t_shirt_sub(self):
        """Checks if this L{Subscriber} has a L{TShirtSub}.
        
        @rtype: bool
        @return: Whether a L{TShirtSub} exists for this L{Subscriber}.
        """

        return self._has_sub_type('TShirtSub')

    def get_preferences(self):
        """Compiles a dictionary of preferences for this L{Subscriber}.
        Key names are the names of fields in L{GenericForm}, L{SubscribeForm},
        and L{PreferencesForm}. This is mainly to be used to determine a user's
        current preferences in order to generate an initial preferences page.
        Checks the database for L{Subscription}s corresponding to the
        L{Subscriber}, and returns a dictionary with the settings of all
        L{Subscription}s found. The dictionary does not contain entries for 
        fields of L{Subscription}s not subscribed to (except for the
        L{GenericForm.get_node_down}, C{GenericForm.get_version}, 
        C{GenericForm.get_band_low}, and C{GenericForm.get_t_shirt}
        fields, which will be C{False} if a L{Subscription} doesn't exist).

        @rtype: Dict {str: various}
        @return: Dictionary of current preferences for this L{Subscriber}.
        """
        
        data = {}

        data['get_node_down'] = self.has_node_down_sub()
        if data['get_node_down']:
            n = NodeDownSub.objects.get(subscriber = self)
            data['node_down_grace_pd'] = n.grace_pd
        else:
            data['node_down_grace_pd'] = GenericForm._INIT_PREFIX + \
                    str(GenericForm._NODE_DOWN_GRACE_PD_INIT)

        data['get_version'] = self.has_version_sub()
        if data['get_version']:
            v = VersionSub.objects.get(subscriber = self)
            data['version_type'] = v.notify_type
        else:
            data['version_type'] = u'UNRECOMMENDED'

        data['get_band_low'] = self.has_bandwidth_sub()
        if data['get_band_low']:
            b = BandwidthSub.objects.get(subscriber = self)
            data['band_low_threshold'] = b.threshold
        else:
            data['band_low_threshold'] = GenericForm._INIT_PREFIX + \
                    str(GenericForm._BAND_LOW_THRESHOLD_INIT)

        data['get_t_shirt'] = self.has_t_shirt_sub()

        return data
         
class Subscription(models.Model):
    """Generic (abstract) mdoel for Tor Weather subscriptions. Only contains
    fields which are used by all types of Tor Weather subscriptions. Django
    uses class variables to specify model fields, but these fields are
    practically used and thought as instance variables, so this documentation
    will refer to them as such. Fields are specified as their django field 
    classes, with parantheses indicating the python type they are validated
    against and treated as practically.

    @type _DEFAULTS: dict {str: various}
    @cvar _DEFAULTS: Dictionary mapping field names to their default
        parameters. These are the values that fields will be instantiated
        with if they are not specified in the field's construction.

    @type subscriber: L{Subscriber}
    @ivar subscriber: The L{Subscriber} who is subscribed to this
        L{Subscription}.
    @type emailed: BooleanField (bool)
    @ivar emailed: Whether the user has already been emailed about this
        L{Subscription} since it has been triggered.
    """

    _DEFAULTS = { 'emailed': False }

    subscriber = models.ForeignKey(Subscriber)
    emailed = models.BooleanField(default=False)

class NodeDownSub(Subscription):
    """A subscription class for node-down subscriptions, which send 
    notifications to the user if their node is down for the downtime grace
    period they specify. 

    @type triggered: bool
    @ivar triggered: C{True} if the node is down, C{False} if it is up.
    @type grace_pd: int
    @ivar grace_pd: The amount of time (hours) before a notification is sent
                    after a node is seen down.
    @type last_changed: datetime
    @ivar last_changed: The datetime object representing the time the triggered
                        flag was last changed.
    """
    triggered = models.BooleanField(default=False)
    grace_pd = models.IntegerField()
    last_changed = models.DateTimeField(default=datetime.now)

    def is_grace_passed(self):
        """Check if the grace period has passed for this subscription
        
        @rtype: bool
        @return: C{True} if C{triggered} and 
        C{hours_since_changed()} >= C{grace_pd}, otherwise
        C{False}.
        """

        if self.triggered and hours_since_changed() >= \
                grace_pd:
            return True
        else:
            return False

class VersionSub(Subscription):
    """Subscription class for version notifications. Subscribers can choose
    between two notification types: OBSOLETE or UNRECOMMENDED. For OBSOLETE
    notifications, the user is sent an email if their router's version of Tor
    does not appear in the list of recommended versions (obtained via TorCtl).
    For UNRECOMMENDED notifications, the user is sent an email if their  
    router's version of Tor is not the most recent stable (non-alpha/beta)   
    version of Tor in the list of recommended versions.

    @type notify_type: str
    @ivar notify_type: Either UNRECOMMENDED (notify users if the router isn't 
        running the most recent stable version of Tor) or OBSOLETE (notify 
        users
        if their router is running a version of Tor that doesn't appear on the
        list of recommended versions).
    """
    #only send notifications if the version is of type notify_type 
    notify_type = models.CharField(max_length=250)

class BandwidthSub(Subscription):    
    """Subscription class for low bandwidth notifications. Subscribers 
    determine a threshold bandwidth in KB/s (default is 20KB/s). If the 
    observed bandwidth field in the descriptor file for their router is ever   
    below that threshold, the user is sent a notification. According to the 
    directory specifications, the observed bandwidth field "is an estimate of 
    the capacity this server can handle. The server remembers the max 
    bandwidth sustained output over any ten second period in the past day, and 
    another sustained input. The 'observed' value is the lesser of these two 
    numbers." An email is sent as soon as we this observed bandwidth crosses 
    the threshold (no grace pd).

    @type threshold: int
    @ivar threshold: The threshold for the bandwidth (in KB/s) that the user 
        specifies for receiving notifications.
    """
    threshold = models.IntegerField(default = 20)
    
    def more_ino(self):
        """Returns a description of this subscription. Meant to be used for
        testing purposes in the shell

        @rtype: str
        @return: A representation of this subscription's fields.
        """

        return 'Bandwidth Subscription' + \
               '\nSubscriber: ' + self.subscriber.email + ' ' + \
                   self.subscriber.router.name + ' ' + \
                   self.subscriber.router.fingerprint + \
               '\nEmailed: ' + str(self.emailed) + \
               '\nThreshold: ' + self.threshold

class TShirtSub(Subscription):
    """A subscription class for T-shirt notifications. An email is sent
    to the user if the router they're monitoring has earned them a T-shirt.
    The router must be running for 61 days (2 months). If it's an exit node,
    it's avg bandwidth must be at least 100 KB/s. Otherwise, it must be at 
    least 500 KB/s.

    @type triggered: bool
    @ivar triggered: C{True} if this router is up, 
    @type avg_bandwidth: int
    @ivar avg_bandwidth: The router's average bandwidth in KB/s
    @type last_changed: datetime
    @ivar last_changed: The datetime object representing the last time the 
        triggered flag was changed.
    """
    triggered = models.BooleanField(default = False)
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

    def should_email(self, hours_up):
        """Returns true if the router being watched has been up for 1464 hours
        (61 days, or approx 2 months). If it's an exit node, the avg bandwidth
        must be at or above 100 KB/s. If not, it must be >= 500 KB/s.
        
        @type hours_up: int
        @param hours_up: The hours that this router has been up (0 if the
            router was last seen down)
        @rtype: bool
        @return: C{True} if the user earned a T-shirt, C{False} if not.
        """
        if not self.emailed and self.triggered and hours_up >= 1464:
            if self.subscriber.router.exit:
                if self.avg_bandwidth >= 100:
                    return True
            else:
                if self.avg_bandwidth >= 500:
                    return True
        return False

class PrefixedIntegerField(forms.IntegerField):
    """An Integer Field that accepts input of the form "-prefix- -integer-"
    and parses it as simply -integer- in its to_python method. Replaces the
    previous process of overwriting post data, which was an ugly workaround.
    A PrefixedIntegerField will not accept empty input, but will throw a
    validationerror specifying that it was left empty, so that this error can
    be intercepted and dealth with cleanly.
    """

    _PREFIX = 'Default value is '

    default_error_messages = {
        'invalid': 'Enter a whole number.',
        'max_value': 'Ensure this value is less than or equal to \
                %(limit_value)s.',
        'min_value': 'Ensure this value is greater than or equal to \
                %(limit_value)s.',
        'empty': 'yo, dawg; I am empty and no user should see this error',
    }

    def __init__(self, max_value=None, min_value=None, *args, **kwargs):
        forms.IntegerField.__init__(self, *args, **kwargs)

        if max_value is not None:
            self.validators.append(validators.MaxValueValidator(max_value))
        if min_value is not None:
            self.validators.append(validators.MinValueValidator(min_value))

    def to_python(self, value):
        prefix = PrefixedIntegerField._PREFIX

        if value == '':
            raise ValidationError(self.error_messages['empty'])

        try:
            if value.startswith(prefix):
                value = int(forms.IntegerField.to_python(self, 
                    value[len(prefix):]))
            else:
                value = int(forms.IntegerField.to_python(self,
                                                value))
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid'])

        return value

class GenericForm(forms.Form):
    """The basic form class that is inherited by the SubscribeForm class
    and the PreferencesForm class. Class variables specifying the types of 
    fields that instances of GenericForm receive are labeled as instance
    variables in this epydoc documentation since the specifications for fields
    can be thought of as the fields that act like instance variables.
   
    @type _GET_NODE_DOWN_INIT: bool
    @cvar _GET_NODE_DOWN_INIT: Initial display value and default submission
        value of the L{get_node_down} checkbox.
    @type _GET_NODE_DOWN_LABEL: str
    @cvar _GET_NODE_DOWN_LABEL: Text displayed next to L{get_node_down} 
        checkbox.
    @type _NODE_DOWN_GRACE_PD_INIT: int
    @cvar _NODE_DOWN_GRACE_PD_INIT: Initial display value and default
        submission value of the L{node_down_grace_pd} field.
    @type _NODE_DOWN_GRACE_PD_MAX: int
    @cvar _NODE_DOWN_GRACE_PD_MAX: Maximum allowed value for the
        L{node_down_grace_pd} field.
    @type _NODE_DOWN_GRACE_PD_MAX_DESC: str
    @cvar _NODE_DOWN_GRACE_PD_MAX_DESC: English approximation of
        L{_NODE_DOWN_GRACE_PD_MAX} for display purposes.
    @type _NODE_DOWN_GRACE_PD_MIN: int
    @cvar _NODE_DOWN_GRACE_PD_MIN: Minimum allowed value for the 
        L{node_down_grace_pd} field.
    @type _NODE_DOWN_GRACE_PD_LABEL: str
    @cvar _NODE_DOWN_GRACE_PD_LABEL: Text displayed above 
        L{node_down_grace_pd} checkbox.
    @type _NODE_DOWN_GRACE_PD_HELP_TEXT: str
    @cvar _NODE_DOWN_GRACE_PD_HELP_TEXT: Text displayed next to 
        L{node_down_grace_pd} checkbox.
    
    @type _GET_VERSION_INIT: bool
    @cvar _GET_VERSION_INIT: Initial display value and default submission 
        value of the L{get_version} checkbox.
    @type _GET_VERSION_LABEL: str
    @cvar _GET_VERSION_LABEL: Text displayed next to L{get_version} checkbox.
    @type _VERSION_TYPE_CHOICE_1: str
    @cvar _VERSION_TYPE_CHOICE_1: Backend name for the first choice of the
        L{version_type} field.
    @type _VERSION_TYPE_CHOICE_1_H: str
    @cvar _VERSION_TYPE_CHOICE_1_H: Frontend (human readable) name for the
        first choice of the L{version_type} field.
    @type _VERSION_TYPE_CHOICE_2: str
    @cvar _VERSION_TYPE_CHOICE_2: Backend name for the second choice of the 
        L{version_type} field.
    @type _VERSION_TYPE_CHOICE_2_H: str
    @cvar _VERSION_TYPE_CHOICE_2_H: Frontend (human readable) name for the
        second choice of the L{version_type} field.
    @type _VERSION_TYPE_CHOICES: list [tuple (str)]
    @cvar _VERSION_TYPE_CHOICES: List of tuples of backend and frontend names
        for each choice of the L{version_type} field.
    @type _VERSION_TYPE_INIT: str
    @cvar _VERSION_TYPE_INIT: Initial display value of the L{version_type} 
        field.
    @type _VERSION_INFO: str
    @cvar _VERSION_INFO: Text explaining the version subscription,  displayed
        in the expandable version section of the form, with HTML enabled.

    @type _GET_BAND_LOW_INIT: bool
    @cvar _GET_BAND_LOW_INIT: Initial display value and default submission
        value of the L{get_version} checkbox.
    @type _GET_BAND_LOW_LABEL: str
    @cvar _GET_BAND_LOW_LABEL: Text displayed next to L{get_version} checkbox.
    @type _BAND_LOW_THRESHOLD_INIT: int
    @cvar _BAND_LOW_THRESHOLD_INIT: Initial display value and default
        submission value of the L{band_low_threshold} field.
    @type _BAND_LOW_THRESHOLD_MIN: int
    @cvar _BAND_LOW_THRESHOLD_MIN: Minimum allowed value for the 
        L{band_low_threshold} field.
    @type _BAND_LOW_THRESHOLD_MAX: int
    @cvar _BAND_LOW_THRESHOLD_MAX: Maximum allowed value for the 
        L{band_low_threshold} field.
    @type _BAND_LOW_THRESHOLD_LABEL: str
    @cvar _BAND_LOW_THRESHOLD_LABEL: Text displayed above the
        L{band_low_threshold} field.
    @type _BAND_LOW_THRESHOLD_HELP_TEXT: str
    @cvar _BAND_LOW_THRESHOLD_HELP_TEXT: Text displayed next to the
        L{band_low_threshold} field.

    @type _T_SHIRT_URL: str
    @cvar _T_SHIRT_URL: URL for information about T-Shirts on Tor wesbite
    @type _GET_T_SHIRT_LABEL: str
    @cvar _GET_T_SHIRT_LABEL: Text displayed above the L{get_t_shirt} checkbox.
    @type _GET_T_SHIRT_INIT: bool
    @cvar _GET_T_SHIRT_INIT: Initial display value and default submission 
        value of the L{get_t_shirt} checkbox.
    @type _T_SHIRT_INFO: str
    @cvar _T_SHIRT_INFO: Text explaining the t-shirt subscription, displayed
        in the expandable version section of the form, with HTML enabled.

    @type _INIT_PREFIX: str
    @cvar _INIT_PREFIX: Prefix for display of default values.
    @type _CLASS_SHORT: str
    @cvar _CLASS_SHORT: HTML/CSS class to use for integer input fields.
    @type _CLASS_RADIO: str
    @cvar _CLASS_RADIO: HTML/CSS class to use for Radio button lists.
    @type _CLASS_CHECK: str
    @cvar _CLASS_CHECK: HTML/CSS class to use for checkboxes.
    @type _INIT_MAPPING: dict {string: various}
    @cvar _INIT_MAPPING: Dictionary of initial values for fields in 
        L{GenericForm}. Points to each of the fields' _XXX_INIT fields.

    @type get_node_down: forms.BooleanField
    @ivar get_node_down: Checkbox letting users choose to subscribe to a
        L{NodeDownSub}.
    @type node_down_grace_pd: PrefixedIntegerField
    @ivar node_down_grace_pd: Integer field (displaying prefix) letting users
        specify their grace period for a L{NodeDownSub}.

    @type get_version: forms.BooleanField
    @ivar get_version: Checkbox letting users choose to subscribe to a 
        L{VersionSub}.
    @type version_type: forms.ChoiceField
    @ivar version_type: Radio button list letting users choose the type of
        L{VersionSub} to subscribe to.
    
    @type get_band_low: forms.BooleanField
    @ivar get_band_low: Checkbox letting users choose to subscribe to a
        L{BandwidthSub}.
    @type band_low_threshold: PrefixedIntegerField
    @ivar band_low_threshold: Integer field (displaying prefix) letting users
        specify their threshold for a L{BandwidthSub}.

    @type get_t_shirt: forms.BooleanField
    @ivar get_t_shirt: Checkbox letting users choose to subscribe to a 
        L{TShirtSub}.
    """
      
    # NOTE: Most places inherit the min, max, and default values for fields
    # from here, but one notable exception is in the javascript file when
    # checking if textboxes haven't been altered.
    _GET_NODE_DOWN_INIT = True
    _GET_NODE_DOWN_LABEL = 'Email me when the node is down'
    _NODE_DOWN_GRACE_PD_INIT = 1
    _NODE_DOWN_GRACE_PD_MAX = 4500
    _NODE_DOWN_GRACE_PD_MIN = 1
    _NODE_DOWN_GRACE_PD_LABEL = 'How long before we send a notifcation?'
    _NODE_DOWN_GRACE_PD_HELP_TEXT = 'Enter a value between one hour and six \
            months'
    _NODE_DOWN_GRACE_PD_UNIT_CHOICE_1 = 'hours'
    _NODE_DOWN_GRACE_PD_UNIT_CHOICE_2 = 'days'
    _NODE_DOWN_GRACE_PD_UNIT_CHOICE_3 = 'weeks'
    _NODE_DOWN_GRACE_PD_UNIT_CHOICE_4 = 'months'
    _NODE_DOWN_GRACE_PD_UNIT_CHOICES = [ ('H', 'hours'),
                                         ('D', 'days'),
                                         ('W', 'weeks'),
                                         ('M', 'months') ]
    _NODE_DOWN_GRACE_PD_UNIT_INIT = ('H', 'hours')
    
    _GET_VERSION_INIT = False
    _GET_VERSION_LABEL = 'Email me when the node\'s Tor version is out of date'
    _VERSION_TYPE_CHOICE_1 = 'UNRECOMMENDED'
    _VERSION_TYPE_CHOICE_1_H = 'Recommended Updates'
    _VERSION_TYPE_CHOICE_2 = 'OBSOLETE'
    _VERSION_TYPE_CHOICE_2_H = 'Required Updates'
    _VERSION_TYPE_CHOICES = [ ('UNRECOMMENDED', 'Recommended Updates'),
                              ('OBSOLETE', 'Required Updates') ]
    _VERSION_TYPE_INIT = ('RECOMMENDED', 'Recommended Updates')
    _VERSION_SECTION_INFO = '<p><em>Recommended Updates:</em>  Emails when\
    the router is not running the most up-to-date stable version of Tor.</p> \
    <p><em>Required Updates:</em>  Emails when the router is running \
    an obsolete version of Tor.</p>'

    _GET_BAND_LOW_INIT = False
    _GET_BAND_LOW_LABEL = 'Email me when the router has low bandwidth capacity'
    _BAND_LOW_THRESHOLD_INIT = 20
    _BAND_LOW_THRESHOLD_MIN = 0
    _BAND_LOW_THRESHOLD_MAX = 100000
    _BAND_LOW_THRESHOLD_LABEL = 'For what citical bandwidth, in kB/s, should \
            we send notifications?'
    _BAND_LOW_THRESHOLD_HELP_TEXT = 'Enter a value between ' + \
            str(_BAND_LOW_THRESHOLD_MIN) + ' and ' + \
            str(_BAND_LOW_THRESHOLD_MAX)
   
    _GET_T_SHIRT_INIT = False
    _GET_T_SHIRT_LABEL = 'Email me when my router has earned me a \
            <a target=_BLANK href="' + url_helper.get_t_shirt_url() + \
            '">Tor t-shirt</a>'
    _T_SHIRT_SECTION_INFO = '<em>Note:</em> You must be the router\'s \
    operator to claim your T-shirt.'

    _INIT_PREFIX = 'Default value is '
    _CLASS_SHORT = 'short-input'
    _CLASS_RADIO = 'radio-list'
    _CLASS_CHECK = 'checkbox-input'
    _INIT_MAPPING = {'get_node_down': _GET_NODE_DOWN_INIT,
                     'node_down_grace_pd': _INIT_PREFIX + \
                             str(_NODE_DOWN_GRACE_PD_INIT),
                     'node_down_grace_pd_unit': _NODE_DOWN_GRACE_PD_UNIT_INIT,
                     'get_version': _GET_VERSION_INIT,
                     'version_type': _VERSION_TYPE_INIT,
                     'get_band_low': _GET_BAND_LOW_INIT,
                     'band_low_threshold': _INIT_PREFIX + \
                             str(_BAND_LOW_THRESHOLD_INIT),
                     'get_t_shirt': _GET_T_SHIRT_INIT}

    # These variables look like class variables, but are actually Django
    # shorthand for instance variables. Upon __init__, these fields will
    # be generated in instance's list of fields.
    get_node_down = forms.BooleanField(required=False,
            label=_GET_NODE_DOWN_LABEL,
            widget=forms.CheckboxInput(attrs={'class':_CLASS_CHECK}))
    node_down_grace_pd = PrefixedIntegerField(required=False,
            min_value=_NODE_DOWN_GRACE_PD_MIN,
            label=_NODE_DOWN_GRACE_PD_LABEL,
            help_text=_NODE_DOWN_GRACE_PD_HELP_TEXT,
            widget=forms.TextInput(attrs={'class':_CLASS_SHORT}))
    node_down_grace_pd_unit = forms.ChoiceField(required=False,
            choices=(_NODE_DOWN_GRACE_PD_UNIT_CHOICES))

    get_version = forms.BooleanField(required=False,
            label=_GET_VERSION_LABEL,
            widget=forms.CheckboxInput(attrs={'class':_CLASS_CHECK}))
    version_type = forms.ChoiceField(required=True,
            choices=(_VERSION_TYPE_CHOICES),
            widget=forms.RadioSelect(attrs={'class':_CLASS_RADIO}))
    
    get_band_low = forms.BooleanField(required=False,
            label=_GET_BAND_LOW_LABEL,
            widget=forms.CheckboxInput(attrs={'class':_CLASS_CHECK}))
    band_low_threshold = PrefixedIntegerField(required=False, 
            max_value=_BAND_LOW_THRESHOLD_MAX,
            min_value=_BAND_LOW_THRESHOLD_MIN, 
            label=_BAND_LOW_THRESHOLD_LABEL,
            help_text=_BAND_LOW_THRESHOLD_HELP_TEXT,
            widget=forms.TextInput(attrs={'class':_CLASS_SHORT}))
    
    get_t_shirt = forms.BooleanField(required=False,
            label=_GET_T_SHIRT_LABEL,
            widget=forms.CheckboxInput(attrs={'class':_CLASS_CHECK}))

    def __init__(self, data = None, initial = None):
        if data == None:
            if initial == None:
                forms.Form.__init__(self, initial=GenericForm._INIT_MAPPING)
            else:
                forms.Form.__init__(self, initial=initial)
        else:
            forms.Form.__init__(self, data)

        self.version_section_text = GenericForm._VERSION_SECTION_INFO
        self.t_shirt_section_text = GenericForm._T_SHIRT_SECTION_INFO

    def check_if_sub_checked(self):
        """Throws a validation error if no subscriptions are checked. 
        Abstracted out of clean() so that there isn't any redundancy in 
        subclass clean() methods."""
        data = self.cleaned_data

        # Ensures that at least one subscription must be checked.
        if not (data['get_node_down'] or
                data['get_version'] or
                data['get_band_low'] or
                data['get_t_shirt']):
            raise forms.ValidationError('You must choose at least one \
                                         type of subscription!')

    def delete_hidden_errors(self):
        data = self.cleaned_data
        errors = self._errors

        if 'node_down_grace_pd' in errors and not data['get_node_down']:
            del errors['node_down_grace_pd']
            data['node_down_grace_pd'] = GenericForm._NODE_DOWN_GRACE_PD_INIT
        if 'version_type' in errors and not data['get_version']:
            del errors['version_type']
            data['version_type'] = GenericForm._VERSION_TYPE_INIT
        if 'band_low_threshold' in errors and not data['get_band_low']:
            del errors['band_low_threshold']
            data['band_low_threshold'] = GenericForm._BAND_LOW_THRESHOLD_INIT

    def convert_node_down_grace_pd_unit(self):
        data = self.cleaned_data
        unit = data['node_down_grace_pd_unit']

        if 'node_down_grace_pd' in data:
            grace_pd = data['node_down_grace_pd']

            if unit == 'D':
                grace_pd = grace_pd * 24
            elif unit == 'W':
                grace_pd = grace_pd * 24 * 7
            elif unit == 'M':
                grace_pd = grace_pd * 24 * 30

            if grace_pd > GenericForm._NODE_DOWN_GRACE_PD_MAX:
                del data['node_down_grace_pd']
                del data['node_down_grace_pd_unit']
                self._errors['node_down_grace_pd'] = \
                        self.error_class(['Ensure this time period is \
                        at most six months (4500 hours).'])

    def clean(self):
        """Calls the check_if_sub_checked to ensure that at least one 
        subscription type has been selected. (This is a Django thing, called
        every time the is_valid method is called on a GenericForm POST 
        request).
                
        @return: The 'cleaned' data from the POST request.
        """
        self.check_if_sub_checked()

        self.convert_node_down_grace_pd_unit()

        self.delete_hidden_errors()

        return self.cleaned_data

class SubscribeForm(GenericForm):
    """Inherits from L{GenericForm}. The SubscribeForm class contains
    all the fields in the GenericForm class and additional fields for 
    the user's email and the fingerprint of the router the user wants to
    monitor.
    
    @type _EMAIL_1_LABEL: str
    @cvar _EMAIL_1_LABEL: Text displayed above L{email_1} field.
    @type _EMAIL_MAX_LEN: str
    @cvar _EMAIL_MAX_LEN: Maximum length of L{email_1} field.
    @type _EMAIL_2_LABEL: str
    @type _FINGERPRINT_LABEL: Text displayed above L{email_2} field.
    @type _FINGERPRINT_MAX_LEN:
    @type _SEARCH_LABEL:
    @type _SEARCH_MAX_LEN:
    @type _SEARCH_ID:
    @type _CLASS_EMAIL:
    @type _CLASS_LONG:

    @type email_1:
    @type email_2:
    @type fingerprint:
    @type router_search:

    @type email_1: EmailField
    @ivar email_1: A field for the user's email 
    @type email_2: EmailField
    @ivar email_2: A field for the user's email (enter twice for security)
    @type fingerprint: str
    @ivar fingerprint: The fingerprint of the router the user wants to 
        monitor.
    """

    _EMAIL_1_LABEL = 'Enter Email:'
    _EMAIL_MAX_LEN = 75
    _EMAIL_2_LABEL = 'Re-enter Email:'
    _FINGERPRINT_LABEL = 'Node Fingerprint:'
    _FINGERPRINT_MAX_LEN = 80
    _SEARCH_LABEL = 'Enter router name, then click the arrow:'
    _SEARCH_MAX_LEN = 80
    _SEARCH_ID = 'router_search'
    _CLASS_EMAIL = 'email-input'
    _CLASS_LONG = 'long-input'

    email_1 = forms.EmailField(label=_EMAIL_1_LABEL,
            widget=forms.TextInput(attrs={'class':_CLASS_EMAIL}),
            max_length=_EMAIL_MAX_LEN)
    email_2 = forms.EmailField(label='Re-enter Email:',
            widget=forms.TextInput(attrs={'class':_CLASS_EMAIL}),
            max_length=_EMAIL_MAX_LEN)
    fingerprint = forms.CharField(label=_FINGERPRINT_LABEL,
            widget=forms.TextInput(attrs={'class':_CLASS_LONG}),
            max_length=_FINGERPRINT_MAX_LEN)
    router_search = forms.CharField(label=_SEARCH_LABEL,
            max_length=_SEARCH_MAX_LEN,
            widget=forms.TextInput(attrs={'id':_SEARCH_ID,                  
                'autocomplete': 'off'}),
            required=False)

    def __init__(self, data = None, initial = None):
        if data == None:
            if initial == None:
                GenericForm.__init__(self)
            else:
                GenericForm.__init__(self, initial=initial)
        else:
            GenericForm.__init__(self, data)

    def clean(self):
        """Called when the is_valid method is evaluated for a SubscribeForm 
        after a POST request."""
        
        # Calls the same helper methods used in the GenericForm clean() method.
        data = self.cleaned_data
        GenericForm.check_if_sub_checked(self)
        GenericForm.convert_node_down_grace_pd_unit(self)
        GenericForm.delete_hidden_errors(self)

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

        # If the field is empty, then deletes the empty validation error and 
        # inserts the default value into the cleaned data.
        if 'node_down_grace_pd' in self._errors:
            if PrefixedIntegerField.default_error_messages['empty'] in \
                    str(self._errors['node_down_grace_pd']):
               del self._errors['node_down_grace_pd']
               data['node_down_grace_pd'] = \
                       GenericForm._NODE_DOWN_GRACE_PD_INIT

        # If the field is empty, then deletes the empty validation error and
        # inserts the default value into the cleaned data.
        if 'band_low_threshold' in self._errors:
            if PrefixedIntegerField.default_error_messages['empty'] in \
                    str(self._errors['band_low_threshold']):
                del self._errors['band_low_threshold']
                data['band_low_threshold'] = \
                        GenericForm._BAND_LOW_THRESHOLD_INIT

        return data

    def clean_fingerprint(self):
        """Uses Django's built-in 'clean' form processing functionality to
        test whether the fingerprint entered is a router we have in the
        current database, and presents an appropriate error message if it
        isn't (along with helpful information).

        @rtype: str
        @return: String representation of the entered fingerprint, if it
            is a valid router fingerprint.
        @raise ValidationError: Raises a validation error if no valid 
        """
        fingerprint = self.cleaned_data.get('fingerprint')
        
        # Removes spaces from fingerprint field.
        fingerprint = re.sub(r' ', '', fingerprint)

        if self.is_valid_router(fingerprint):
            return fingerprint
        else:
            info_extension = url_helper.get_fingerprint_info_ext(fingerprint)
            msg = 'We could not locate a Tor node with that fingerprint. \
                   (<a target=_BLANK href=%s>More info</a>)' % info_extension
            raise forms.ValidationError(msg)

    def is_valid_router(self, fingerprint):
        """Helper function to check if a router exists in the database.

        @type fingerprint: str
        @param fingerprint: String representation of a router's fingerprint.
        @rtype: bool
        @return: Whether a router with the specified fingerprint exists in
            the database.
        """

        # The router fingerprint field is unique, so we only need to worry
        # about the router not existing, not there being two routers.
        try:
            Router.objects.get(fingerprint=fingerprint)
        except Router.DoesNotExist:
            return False
        else:
            return True

    def create_subscriber(self):
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
 
    def create_subscriptions(self, subscriber):
        """Create the subscriptions if they are specified.
        
        @type subscriber: Subscriber
        @param subscriber: The subscriber whose subscriptions are being saved.
        """
        # Create the various subscriptions if they are specified.
        if self.cleaned_data['get_node_down']:
            node_down_sub = NodeDownSub(subscriber=subscriber,
                    grace_pd=self.cleaned_data['node_down_grace_pd'])
            node_down_sub.save()
        if self.cleaned_data['get_version']:
            version_sub = VersionSub(subscriber=subscriber,
                    notify_type = self.cleaned_data['version_type'])
            version_sub.save()
        if self.cleaned_data['get_band_low']:
            band_low_sub = BandwidthSub(subscriber=subscriber,
                    threshold=self.cleaned_data['band_low_threshold'])
            band_low_sub.save()
        if self.cleaned_data['get_t_shirt']:
            t_shirt_sub = TShirtSub(subscriber=subscriber)
            t_shirt_sub.save()
         
class PreferencesForm(GenericForm):
    """The form for changing preferences, as displayed on the preferences 
    page. The form displays the user's current settings for all subscription 
    types (i.e. if they haven't selected a subscription type, the box for that 
    field is unchecked). The PreferencesForm form inherits L{GenericForm}.
    """
    
    _USER_INFO_STR = '<p><span>Email:</span> %s</p> \
            <p><span>Router name:</span> %s</p> \
            <p><span>Router id:</span> %s</p>'

    def __init__(self, user, data = None):
        # If no data, is provided, then create using preferences as initial
        # form data. Otherwise, use provided data.
        if data == None:
            GenericForm.__init__(self, initial=user.get_preferences())
        else:
            GenericForm.__init__(self, data)
 
        self.user = user

        self.user_info = PreferencesForm._USER_INFO_STR % (self.user.email, \
                self.user.router.name, user.router.spaced_fingerprint())

    def change_subscriptions(self, old_data, new_data):
        """Change the subscriptions and options if they are specified.
        
        @type new_data: dict {unicode: various}
        @param new_data: New preferences.
        """

        old_data = self.user.get_preferences()

        # If there already was a subscription, get it and update it or delete
        # it depending on the current value.
        if old_data['get_node_down']:
            n = NodeDownSub.objects.get(subscriber = self.user)
            if new_data['get_node_down']:
                n.grace_pd = new_data['node_down_grace_pd']
                n.save()
            else:
                n.delete()
        # If there wasn't a subscription before and it is checked now, then 
        # make one.
        elif new_data['get_node_down']:
            n = NodeDownSub(subscriber=subscriber, 
                    grace_pd=new_data['node_down_grace_pd'])
            n.save()

        # If there already was a subscription, get it and update it or delete
        # it depending on the current value.
        if old_data['get_version']:
            v = VersionSub.objects.get(subscriber = self.user)
            if new_data['get_version']:
                v.notify_type = new_data['version_type']
                v.save()
            else:
                v.delete()
        # If there wasn't a subscription before and it is checked now, then 
        # make one.
        elif new_data['get_version']:
            v = VersionSub(subscriber=self.user, 
                    notify_type=new_data['version_type'])
            v.save()

        # If there already was a subscription, get it and update it or delete
        # it depending on the current value.
        if old_data['get_band_low']:
            b = BandwidthSub.objects.get(subscriber = self.user)
            if new_data['get_band_low']:
                b.threshold = new_data['band_low_threshold']
                b.save()
            else:
                b.delete()
        # If there wasn't a subscription before and it is checked now, then
        # make one.
        elif new_data['get_band_low']:
            b = BandwidthSub(subscriber=self.user,
                    threshold=new_data['band_low_threshold'])
            b.save()

        # If there already was a subscription, get it and delete it if it's no
        # longer selected.
        if old_data['get_t_shirt']:
            t = TShirtSub.objects.get(subscriber = self.user)
            if not new_data['get_t_shirt']:
                t.delete()
        # If there wasn't a subscription before and it is checked now, then
        # make one.
        elif new_data['get_t_shirt']:
            t = TShirtSub(subscriber=self.user)
            t.save()
