import copy
import numbers
import six

from .dropbox import Dropbox, Namespace
from .util import assert_only_one

class Empty(object):

    def __init__(self,
                 **kwargs):
        pass

    @classmethod
    def from_json(cls, obj):
        return Empty(**obj)

    def to_json(self):
        d = dict()
        return d

    def __repr__(self):
        return 'Empty()'

class Space(object):
    """
    The space quota info for a user.
    """

    def __init__(self,
                 quota,
                 private,
                 shared,
                 datastores,
                 **kwargs):
        """
        :param long quota: The user's total quota allocation (bytes).
        :param long private: The user's used quota outside of shared folders
            (bytes).
        :param long shared: The user's used quota in shared folders (bytes).
        :param long datastores: The user's used quota in datastores (bytes).
        """
        assert isinstance(quota, numbers.Integral), 'quota must be of type numbers.Integral'
        self.quota = quota

        assert isinstance(private, numbers.Integral), 'private must be of type numbers.Integral'
        self.private = private

        assert isinstance(shared, numbers.Integral), 'shared must be of type numbers.Integral'
        self.shared = shared

        assert isinstance(datastores, numbers.Integral), 'datastores must be of type numbers.Integral'
        self.datastores = datastores

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return Space(**obj)

    def to_json(self):
        d = dict(quota=self.quota,
                 private=self.private,
                 shared=self.shared,
                 datastores=self.datastores)
        return d

    def __repr__(self):
        return 'Space(%r)' % self.quota

class Team(object):
    """
    Information about a team.
    """

    def __init__(self,
                 id,
                 name,
                 **kwargs):
        """
        :param str id: The team's unique ID.
        :param str name: The name of the team.
        """
        assert isinstance(id, six.string_types), 'id must be of type six.string_types'
        self.id = id

        assert isinstance(name, six.string_types), 'name must be of type six.string_types'
        self.name = name

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return Team(**obj)

    def to_json(self):
        d = dict(id=self.id,
                 name=self.name)
        return d

    def __repr__(self):
        return 'Team(%r)' % self.id

class Name(object):
    """
    Contains several ways a name might be represented to make
    internationalization more convenient.
    """

    def __init__(self,
                 given_name,
                 surname,
                 familiar_name,
                 display_name,
                 **kwargs):
        """
        :param str given_name: Also known as a first name.
        :param str surname: Also known as a last name or family name.
        :param str familiar_name: Locale-dependent familiar name. Generally
            matches ``given_name`` or ``display_name``.
        :param str display_name: A name that can be used directly to represent
            the name of a user's Dropbox account.
        """
        assert isinstance(given_name, six.string_types), 'given_name must be of type six.string_types'
        self.given_name = given_name

        assert isinstance(surname, six.string_types), 'surname must be of type six.string_types'
        self.surname = surname

        assert isinstance(familiar_name, six.string_types), 'familiar_name must be of type six.string_types'
        self.familiar_name = familiar_name

        assert isinstance(display_name, six.string_types), 'display_name must be of type six.string_types'
        self.display_name = display_name

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return Name(**obj)

    def to_json(self):
        d = dict(given_name=self.given_name,
                 surname=self.surname,
                 familiar_name=self.familiar_name,
                 display_name=self.display_name)
        return d

    def __repr__(self):
        return 'Name(%r)' % self.given_name

class BasicAccountInfo(object):
    """
    Basic information about a user's account.
    """

    def __init__(self,
                 account_id,
                 name,
                 **kwargs):
        """
        :param str account_id: The user's unique Dropbox ID.
        :param name: Details of a user's name.
        :type name: :class:`Name`
        """
        assert isinstance(account_id, six.string_types), 'account_id must be of type six.string_types'
        self.account_id = account_id

        assert isinstance(name, Name), 'name must be of type Name'
        self.name = name

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        obj['name'] = Name.from_json(obj['name'])
        return BasicAccountInfo(**obj)

    def to_json(self):
        d = dict(account_id=self.account_id,
                 name=self.name.to_json())
        return d

    def __repr__(self):
        return 'BasicAccountInfo(%r)' % self.account_id

class MeInfo(BasicAccountInfo):
    """
    Information about a user's account.
    """

    def __init__(self,
                 account_id,
                 name,
                 email,
                 country,
                 locale,
                 referral_link,
                 space,
                 team,
                 is_paired,
                 **kwargs):
        """
        :param str email: The user's e-mail address.
        :param str country: The user's two-letter country code, if available.
        :param str locale: The language setting that user specified.
        :param str referral_link: The user's `referral link
            <https://www.dropbox.com/referrals>`_.
        :param space: The user's quota.
        :type space: :class:`Space`
        :param team: If this account is a member of a team.
        :type team: :class:`Team`
        :param bool is_paired: Whether the user has a personal and work account.
            If the authorized account is personal, then ``team`` will always be
            'Null', but ``is_paired`` will indicate if a work account is linked.
        """
        super(MeInfo, self).__init__(
            account_id,
            name,
        )

        assert isinstance(email, six.string_types), 'email must be of type six.string_types'
        self.email = email

        if country is not None:
            assert isinstance(country, six.string_types), 'country must be of type six.string_types'
        self.country = country

        assert isinstance(locale, six.string_types), 'locale must be of type six.string_types'
        self.locale = locale

        assert isinstance(referral_link, six.string_types), 'referral_link must be of type six.string_types'
        self.referral_link = referral_link

        assert isinstance(space, Space), 'space must be of type Space'
        self.space = space

        if team is not None:
            assert isinstance(team, Team), 'team must be of type Team'
        self.team = team

        assert isinstance(is_paired, bool), 'is_paired must be of type bool'
        self.is_paired = is_paired

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        obj['name'] = Name.from_json(obj['name'])
        obj['space'] = Space.from_json(obj['space'])
        obj['team'] = Team.from_json(obj['team'])
        return MeInfo(**obj)

    def to_json(self):
        d = dict(account_id=self.account_id,
                 name=self.name.to_json(),
                 email=self.email,
                 country=self.country,
                 locale=self.locale,
                 referral_link=self.referral_link,
                 space=self.space.to_json(),
                 team=self.team.to_json(),
                 is_paired=self.is_paired)
        return d

    def __repr__(self):
        return 'MeInfo(%r)' % self.email

class AccountInfo(object):
    """
    The amount of detail revealed about an account depends on the user being
    queried and the user making the query.

    :ivar Me: None
    :ivar Teammate: None
    :ivar User: None
    """

    Me = MeInfo
    Teammate = BasicAccountInfo
    User = BasicAccountInfo

    def __init__(self,
                 me=None,
                 teammate=None,
                 user=None,
                 **kwargs):
        """
        Only one argument can be set.

        :type me: :class:`MeInfo`
        :type teammate: :class:`BasicAccountInfo`
        :type user: :class:`BasicAccountInfo`
        """
        assert_only_one(me=me,
                        teammate=teammate,
                        user=user,
                        **kwargs)
        self.me = None
        self.teammate = None
        self.user = None

        if me is not None:
            assert isinstance(me, MeInfo), 'me must be of type MeInfo'
            self.me = me
            self._tag = 'me'

        if teammate is not None:
            assert isinstance(teammate, BasicAccountInfo), 'teammate must be of type BasicAccountInfo'
            self.teammate = teammate
            self._tag = 'teammate'

        if user is not None:
            assert isinstance(user, BasicAccountInfo), 'user must be of type BasicAccountInfo'
            self.user = user
            self._tag = 'user'

    def is_me(self):
        return self._tag == 'me'

    def is_teammate(self):
        return self._tag == 'teammate'

    def is_user(self):
        return self._tag == 'user'

    @classmethod
    def from_json(self, obj):
        obj = copy.copy(obj)
        assert len(obj) == 1, 'One key must be set, not %d' % len(obj)
        if 'me' in obj:
            obj['me'] = MeInfo.from_json(obj['me'])
        if 'teammate' in obj:
            obj['teammate'] = BasicAccountInfo.from_json(obj['teammate'])
        if 'user' in obj:
            obj['user'] = BasicAccountInfo.from_json(obj['user'])
        return AccountInfo(**obj)

    def to_json(self):
        if self._tag == 'me':
            return dict(me=self.me.to_json())
        if self._tag == 'teammate':
            return dict(teammate=self.teammate.to_json())
        if self._tag == 'user':
            return dict(user=self.user.to_json())

    def __repr__(self):
        return 'AccountInfo(%r)' % self._tag

class InfoRequest(object):

    def __init__(self,
                 account_id,
                 **kwargs):
        """
        :param str account_id: A user's account identifier. Use '"me"' to get
            information for the current account.
        """
        assert isinstance(account_id, six.string_types), 'account_id must be of type six.string_types'
        self.account_id = account_id

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return InfoRequest(**obj)

    def to_json(self):
        d = dict(account_id=self.account_id)
        return d

    def __repr__(self):
        return 'InfoRequest(%r)' % self.account_id

class InfoError(object):

    NoAccount = object()

    def __init__(self,
                 no_account=None,
                 **kwargs):
        """
        Only one argument can be set.

        :param bool no_account: The specified ``account_id`` does not exist.
        """
        assert_only_one(no_account=no_account,
                        **kwargs)
        self.no_account = None

        if no_account is not None:
            assert isinstance(no_account, bool), 'no_account must be of type bool'
            self.no_account = no_account
            self._tag = 'no_account'

    def is_no_account(self):
        return self._tag == 'no_account'

    @classmethod
    def from_json(self, obj):
        obj = copy.copy(obj)
        assert len(obj) == 1, 'One key must be set, not %d' % len(obj)
        if obj == 'no_account':
            return obj
        return InfoError(**obj)

    def to_json(self):
        if self._tag == 'no_account':
            return self._tag

    def __repr__(self):
        return 'InfoError(%r)' % self._tag

class BaseUsers(Namespace):
    """Methods for routes in the users namespace"""

    def info(self,
             account_id):
        """
        Get information about a user's account.

        :param str account_id: A user's account identifier. Use '"me"' to get
            information for the current account.
        :rtype: :class:`AccountInfo`
        :raises: :class:`dropbox.exceptions.ApiError`

        Error codes:
            no_account: The specified ``account_id`` does not exist.
        """
        o = InfoRequest(account_id).to_json()
        r = self._dropbox.request(Dropbox.Host.API,
                                  'users/info',
                                  Dropbox.RouteStyle.RPC,
                                  o,
                                  None)
        return AccountInfo.from_json(r.obj_segment)

    def info_me(self):
        """
        Get information about the authorized user's account.

        :rtype: :class:`MeInfo`
        """
        o = Empty().to_json()
        r = self._dropbox.request(Dropbox.Host.API,
                                  'users/info/me',
                                  Dropbox.RouteStyle.RPC,
                                  o,
                                  None)
        return MeInfo.from_json(r.obj_segment)

