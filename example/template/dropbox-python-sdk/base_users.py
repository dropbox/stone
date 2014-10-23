import copy
import types

from .dropbox import assert_only_one, Dropbox, Namespace

class Empty(object):

    def __init__(self,
                 **kwargs):
        pass

    def __repr__(self):
        return 'Empty()'

    @classmethod
    def from_json(cls, obj):
        return Empty(**obj)

    def to_json(self):
        d = dict()
        return d

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
        Args:
            quota (long): The user's total quota allocation (bytes).
            private (long): The user's used quota outside of shared folders
                (bytes).
            shared (long): The user's used quota in shared folders (bytes).
            datastores (long): The user's used quota in datastores (bytes).
        """
        assert isinstance(quota, (int, long)), 'quota must be of type (int, long)'
        self.quota = quota

        assert isinstance(private, (int, long)), 'private must be of type (int, long)'
        self.private = private

        assert isinstance(shared, (int, long)), 'shared must be of type (int, long)'
        self.shared = shared

        assert isinstance(datastores, (int, long)), 'datastores must be of type (int, long)'
        self.datastores = datastores

    def __repr__(self):
        return 'Space(%r)' % self.quota

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

class Team(object):
    """
    Information about a team.
    """

    def __init__(self,
                 id,
                 name,
                 **kwargs):
        """
        Args:
            id (str): The team's unique ID.
            name (str): The name of the team.
        """
        assert isinstance(id, types.StringTypes), 'id must be of type types.StringTypes'
        self.id = id

        assert isinstance(name, types.StringTypes), 'name must be of type types.StringTypes'
        self.name = name

    def __repr__(self):
        return 'Team(%r)' % self.id

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return Team(**obj)

    def to_json(self):
        d = dict(id=self.id,
                 name=self.name)
        return d

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
        Args:
            given_name (str): Also known as a first name.
            surname (str): Also known as a last name or family name.
            familiar_name (str): Locale-dependent familiar name. Generally
                matches :field:`given_name` or :field:`display_name`.
            display_name (str): A name that can be used directly to represent
                the name of a user's Dropbox account.
        """
        assert isinstance(given_name, types.StringTypes), 'given_name must be of type types.StringTypes'
        self.given_name = given_name

        assert isinstance(surname, types.StringTypes), 'surname must be of type types.StringTypes'
        self.surname = surname

        assert isinstance(familiar_name, types.StringTypes), 'familiar_name must be of type types.StringTypes'
        self.familiar_name = familiar_name

        assert isinstance(display_name, types.StringTypes), 'display_name must be of type types.StringTypes'
        self.display_name = display_name

    def __repr__(self):
        return 'Name(%r)' % self.given_name

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

class BasicAccountInfo(object):
    """
    Basic information about a user's account.
    """

    def __init__(self,
                 account_id,
                 name,
                 **kwargs):
        """
        Args:
            account_id (str): The user's unique Dropbox ID.
            name (Name): Details of a user's name.
        """
        assert isinstance(account_id, types.StringTypes), 'account_id must be of type types.StringTypes'
        self.account_id = account_id

        assert isinstance(name, Name), 'name must be of type dropbox.data_types.Name'
        self.name = name

    def __repr__(self):
        return 'BasicAccountInfo(%r)' % self.account_id

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        obj['name'] = Name.from_json(obj['name'])
        return BasicAccountInfo(**obj)

    def to_json(self):
        d = dict(account_id=self.account_id,
                 name=self.name.to_json())
        return d

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
        Args:
            email (str): The user's e-mail address.
            country (str): The user's two-letter country code, if available.
            locale (str): The language setting that user specified.
            referral_link (str): The user's :link:`referral link
                https://www.dropbox.com/referrals`.
            space (Space): The user's quota.
            team (Team): If this account is a member of a team.
            is_paired (bool): Whether the user has a personal and work account.
                If the authorized account is personal, then :field:`team` will
                always be :val:`Null`, but :field:`is_paired` will indicate if a
                work account is linked.
        """
        super(MeInfo, self).__init__(
            account_id,
            name,
        )

        assert isinstance(email, types.StringTypes), 'email must be of type types.StringTypes'
        self.email = email

        if country is not None:
            assert isinstance(country, types.StringTypes), 'country must be of type types.StringTypes'
        self.country = country

        assert isinstance(locale, types.StringTypes), 'locale must be of type types.StringTypes'
        self.locale = locale

        assert isinstance(referral_link, types.StringTypes), 'referral_link must be of type types.StringTypes'
        self.referral_link = referral_link

        assert isinstance(space, Space), 'space must be of type dropbox.data_types.Space'
        self.space = space

        if team is not None:
            assert isinstance(team, Team), 'team must be of type dropbox.data_types.Team'
        self.team = team

        assert isinstance(is_paired, bool), 'is_paired must be of type bool'
        self.is_paired = is_paired

    def __repr__(self):
        return 'MeInfo(%r)' % self.email

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

class AccountInfo(object):
    """
    The amount of detail revealed about an account depends on the user being
    queried and the user making the query.
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
        The amount of detail revealed about an account depends on the user being
        queried and the user making the query.

        Only one argument may be specified.

        """
        assert_only_one(me=me,
                        teammate=teammate,
                        user=user,
                        **kwargs)
        self.me = None
        self.teammate = None
        self.user = None

        if me is not None:
            assert isinstance(me, MeInfo), 'me must be of type dropbox.data_types.MeInfo'
            self.me = me
            self._tag = 'me'

        if teammate is not None:
            assert isinstance(teammate, BasicAccountInfo), 'teammate must be of type dropbox.data_types.BasicAccountInfo'
            self.teammate = teammate
            self._tag = 'teammate'

        if user is not None:
            assert isinstance(user, BasicAccountInfo), 'user must be of type dropbox.data_types.BasicAccountInfo'
            self.user = user
            self._tag = 'user'

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
        Args:
            account_id (str): A user's account identifier. Use :val:`"me"` to
                get information for the current account.
        """
        assert isinstance(account_id, types.StringTypes), 'account_id must be of type types.StringTypes'
        self.account_id = account_id

    def __repr__(self):
        return 'InfoRequest(%r)' % self.account_id

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return InfoRequest(**obj)

    def to_json(self):
        d = dict(account_id=self.account_id)
        return d

class InfoError(object):

    NoAccount = object()

    def __init__(self,
                 no_account=None,
                 **kwargs):
        """
        Only one argument may be specified.

        Args:
            no_account: The specified :field:`account_id` does not exist.
        """
        assert_only_one(no_account=no_account,
                        **kwargs)
        self.no_account = None

        if no_account is not None:
            assert isinstance(no_account, bool), 'no_account must be of type bool'
            self.no_account = no_account
            self._tag = 'no_account'

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

class Users(Namespace):
    def info(self,
             account_id):
        """
        Get information about a user's account.

        Args:
            account_id: A user's account identifier. Use :val:`"me"` to get
                information for the current account.

        Raises:
            ApiError with the following codes:
                no_account: The specified :field:`account_id` does not exist.
        """
        o = InfoRequest(account_id)
        r = self._dropbox.request(Dropbox.Host.API,
                                  'users/info',
                                  Dropbox.OpStyle.RPC,
                                  o.to_json(),
                                  None)
        return AccountInfo.from_json(r.obj_segment)

    def info_me(self):
        """
        Get information about the authorized user's account.
        """
        o = Empty()
        r = self._dropbox.request(Dropbox.Host.API,
                                  'users/info/me',
                                  Dropbox.OpStyle.RPC,
                                  o.to_json(),
                                  None)
        return AccountInfo.from_json(r.obj_segment)

