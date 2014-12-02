import copy
import datetime
import numbers
import six

import babel_data_types as dt

class Empty(dt.Struct):

    _field_names_ = {
    }

    _fields_ = [
    ]

    def __init__(self):
        pass

    def validate(self):
        return all([
        ])

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls._field_names_:
                raise KeyError("Unknown key: %r" % key)
        empty = Empty()
        return empty

    def to_dict(self, transformer):
        d = dict()
        return d

    def __repr__(self):
        return 'Empty()'

class Space(dt.Struct):
    """
    The space quota info for a user.

    :ivar quota: The user's total quota allocation (bytes).
    :ivar private: The user's used quota outside of shared folders (bytes).
    :ivar shared: The user's used quota in shared folders (bytes).
    :ivar datastores: The user's used quota in datastores (bytes).
    """

    __quota_data_type = dt.UInt64()
    __private_data_type = dt.UInt64()
    __shared_data_type = dt.UInt64()
    __datastores_data_type = dt.UInt64()

    _field_names_ = {
        'quota',
        'private',
        'shared',
        'datastores',
    }

    _fields_ = [
        ('quota', False, __quota_data_type),
        ('private', False, __private_data_type),
        ('shared', False, __shared_data_type),
        ('datastores', False, __datastores_data_type),
    ]

    def __init__(self):
        self._quota = None
        self.__has_quota = False
        self._private = None
        self.__has_private = False
        self._shared = None
        self.__has_shared = False
        self._datastores = None
        self.__has_datastores = False

    def validate(self):
        return all([
            self.__has_quota,
            self.__has_private,
            self.__has_shared,
            self.__has_datastores,
        ])

    @property
    def quota(self):
        """
        The user's total quota allocation (bytes).
        :rtype: long
        """
        if self.__has_quota:
            return self._quota
        else:
            raise KeyError("missing required field 'quota'")

    @quota.setter
    def quota(self, val):
        self.__quota_data_type.validate(val)
        self._quota = val
        self.__has_quota = True

    @quota.deleter
    def quota(self, val):
        self._quota = None
        self.__has_quota = False

    @property
    def private(self):
        """
        The user's used quota outside of shared folders (bytes).
        :rtype: long
        """
        if self.__has_private:
            return self._private
        else:
            raise KeyError("missing required field 'private'")

    @private.setter
    def private(self, val):
        self.__private_data_type.validate(val)
        self._private = val
        self.__has_private = True

    @private.deleter
    def private(self, val):
        self._private = None
        self.__has_private = False

    @property
    def shared(self):
        """
        The user's used quota in shared folders (bytes).
        :rtype: long
        """
        if self.__has_shared:
            return self._shared
        else:
            raise KeyError("missing required field 'shared'")

    @shared.setter
    def shared(self, val):
        self.__shared_data_type.validate(val)
        self._shared = val
        self.__has_shared = True

    @shared.deleter
    def shared(self, val):
        self._shared = None
        self.__has_shared = False

    @property
    def datastores(self):
        """
        The user's used quota in datastores (bytes).
        :rtype: long
        """
        if self.__has_datastores:
            return self._datastores
        else:
            raise KeyError("missing required field 'datastores'")

    @datastores.setter
    def datastores(self, val):
        self.__datastores_data_type.validate(val)
        self._datastores = val
        self.__has_datastores = True

    @datastores.deleter
    def datastores(self, val):
        self._datastores = None
        self.__has_datastores = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls._field_names_:
                raise KeyError("Unknown key: %r" % key)
        space = Space()
        if 'quota' not in obj:
            raise KeyError("missing required field 'quota'")
        space.quota = transformer.convert_from(space.__quota_data_type, obj['quota'])
        if 'private' not in obj:
            raise KeyError("missing required field 'private'")
        space.private = transformer.convert_from(space.__private_data_type, obj['private'])
        if 'shared' not in obj:
            raise KeyError("missing required field 'shared'")
        space.shared = transformer.convert_from(space.__shared_data_type, obj['shared'])
        if 'datastores' not in obj:
            raise KeyError("missing required field 'datastores'")
        space.datastores = transformer.convert_from(space.__datastores_data_type, obj['datastores'])
        return space

    def to_dict(self, transformer):
        d = dict(quota=transformer.convert_to(self.__quota_data_type, self._quota),
                 private=transformer.convert_to(self.__private_data_type, self._private),
                 shared=transformer.convert_to(self.__shared_data_type, self._shared),
                 datastores=transformer.convert_to(self.__datastores_data_type, self._datastores))
        return d

    def __repr__(self):
        return 'Space(%r)' % self._quota

class Team(dt.Struct):
    """
    Information about a team.

    :ivar id: The team's unique ID.
    :ivar name: The name of the team.
    """

    __id_data_type = dt.String(pattern=None)
    __name_data_type = dt.String(pattern=None)

    _field_names_ = {
        'id',
        'name',
    }

    _fields_ = [
        ('id', False, __id_data_type),
        ('name', False, __name_data_type),
    ]

    def __init__(self):
        self._id = None
        self.__has_id = False
        self._name = None
        self.__has_name = False

    def validate(self):
        return all([
            self.__has_id,
            self.__has_name,
        ])

    @property
    def id(self):
        """
        The team's unique ID.
        :rtype: str
        """
        if self.__has_id:
            return self._id
        else:
            raise KeyError("missing required field 'id'")

    @id.setter
    def id(self, val):
        self.__id_data_type.validate(val)
        self._id = val
        self.__has_id = True

    @id.deleter
    def id(self, val):
        self._id = None
        self.__has_id = False

    @property
    def name(self):
        """
        The name of the team.
        :rtype: str
        """
        if self.__has_name:
            return self._name
        else:
            raise KeyError("missing required field 'name'")

    @name.setter
    def name(self, val):
        self.__name_data_type.validate(val)
        self._name = val
        self.__has_name = True

    @name.deleter
    def name(self, val):
        self._name = None
        self.__has_name = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls._field_names_:
                raise KeyError("Unknown key: %r" % key)
        team = Team()
        if 'id' not in obj:
            raise KeyError("missing required field 'id'")
        team.id = transformer.convert_from(team.__id_data_type, obj['id'])
        if 'name' not in obj:
            raise KeyError("missing required field 'name'")
        team.name = transformer.convert_from(team.__name_data_type, obj['name'])
        return team

    def to_dict(self, transformer):
        d = dict(id=transformer.convert_to(self.__id_data_type, self._id),
                 name=transformer.convert_to(self.__name_data_type, self._name))
        return d

    def __repr__(self):
        return 'Team(%r)' % self._id

class Name(dt.Struct):
    """
    Contains several ways a name might be represented to make
    internationalization more convenient.

    :ivar given_name: Also known as a first name.
    :ivar surname: Also known as a last name or family name.
    :ivar familiar_name: Locale-dependent familiar name. Generally matches
        ``given_name`` or ``display_name``.
    :ivar display_name: A name that can be used directly to represent the name
        of a user's Dropbox account.
    """

    __given_name_data_type = dt.String(pattern=None)
    __surname_data_type = dt.String(pattern=None)
    __familiar_name_data_type = dt.String(pattern=None)
    __display_name_data_type = dt.String(pattern=None)

    _field_names_ = {
        'given_name',
        'surname',
        'familiar_name',
        'display_name',
    }

    _fields_ = [
        ('given_name', False, __given_name_data_type),
        ('surname', False, __surname_data_type),
        ('familiar_name', False, __familiar_name_data_type),
        ('display_name', False, __display_name_data_type),
    ]

    def __init__(self):
        self._given_name = None
        self.__has_given_name = False
        self._surname = None
        self.__has_surname = False
        self._familiar_name = None
        self.__has_familiar_name = False
        self._display_name = None
        self.__has_display_name = False

    def validate(self):
        return all([
            self.__has_given_name,
            self.__has_surname,
            self.__has_familiar_name,
            self.__has_display_name,
        ])

    @property
    def given_name(self):
        """
        Also known as a first name.
        :rtype: str
        """
        if self.__has_given_name:
            return self._given_name
        else:
            raise KeyError("missing required field 'given_name'")

    @given_name.setter
    def given_name(self, val):
        self.__given_name_data_type.validate(val)
        self._given_name = val
        self.__has_given_name = True

    @given_name.deleter
    def given_name(self, val):
        self._given_name = None
        self.__has_given_name = False

    @property
    def surname(self):
        """
        Also known as a last name or family name.
        :rtype: str
        """
        if self.__has_surname:
            return self._surname
        else:
            raise KeyError("missing required field 'surname'")

    @surname.setter
    def surname(self, val):
        self.__surname_data_type.validate(val)
        self._surname = val
        self.__has_surname = True

    @surname.deleter
    def surname(self, val):
        self._surname = None
        self.__has_surname = False

    @property
    def familiar_name(self):
        """
        Locale-dependent familiar name. Generally matches ``given_name`` or
        ``display_name``.
        :rtype: str
        """
        if self.__has_familiar_name:
            return self._familiar_name
        else:
            raise KeyError("missing required field 'familiar_name'")

    @familiar_name.setter
    def familiar_name(self, val):
        self.__familiar_name_data_type.validate(val)
        self._familiar_name = val
        self.__has_familiar_name = True

    @familiar_name.deleter
    def familiar_name(self, val):
        self._familiar_name = None
        self.__has_familiar_name = False

    @property
    def display_name(self):
        """
        A name that can be used directly to represent the name of a user's
        Dropbox account.
        :rtype: str
        """
        if self.__has_display_name:
            return self._display_name
        else:
            raise KeyError("missing required field 'display_name'")

    @display_name.setter
    def display_name(self, val):
        self.__display_name_data_type.validate(val)
        self._display_name = val
        self.__has_display_name = True

    @display_name.deleter
    def display_name(self, val):
        self._display_name = None
        self.__has_display_name = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls._field_names_:
                raise KeyError("Unknown key: %r" % key)
        name = Name()
        if 'given_name' not in obj:
            raise KeyError("missing required field 'given_name'")
        name.given_name = transformer.convert_from(name.__given_name_data_type, obj['given_name'])
        if 'surname' not in obj:
            raise KeyError("missing required field 'surname'")
        name.surname = transformer.convert_from(name.__surname_data_type, obj['surname'])
        if 'familiar_name' not in obj:
            raise KeyError("missing required field 'familiar_name'")
        name.familiar_name = transformer.convert_from(name.__familiar_name_data_type, obj['familiar_name'])
        if 'display_name' not in obj:
            raise KeyError("missing required field 'display_name'")
        name.display_name = transformer.convert_from(name.__display_name_data_type, obj['display_name'])
        return name

    def to_dict(self, transformer):
        d = dict(given_name=transformer.convert_to(self.__given_name_data_type, self._given_name),
                 surname=transformer.convert_to(self.__surname_data_type, self._surname),
                 familiar_name=transformer.convert_to(self.__familiar_name_data_type, self._familiar_name),
                 display_name=transformer.convert_to(self.__display_name_data_type, self._display_name))
        return d

    def __repr__(self):
        return 'Name(%r)' % self._given_name

class BasicAccountInfo(dt.Struct):
    """
    Basic information about a user's account.

    :ivar account_id: The user's unique Dropbox ID.
    :ivar name: Details of a user's name.
    """

    __account_id_data_type = dt.String(min_length=40, max_length=40, pattern=None)

    _field_names_ = {
        'account_id',
        'name',
    }

    _fields_ = [
        ('account_id', False, __account_id_data_type),
        ('name', False, Name),
    ]

    def __init__(self):
        self._account_id = None
        self.__has_account_id = False
        self._name = None
        self.__has_name = False

    def validate(self):
        return all([
            self.__has_account_id,
            self.__has_name,
        ])

    @property
    def account_id(self):
        """
        The user's unique Dropbox ID.
        :rtype: str
        """
        if self.__has_account_id:
            return self._account_id
        else:
            raise KeyError("missing required field 'account_id'")

    @account_id.setter
    def account_id(self, val):
        self.__account_id_data_type.validate(val)
        self._account_id = val
        self.__has_account_id = True

    @account_id.deleter
    def account_id(self, val):
        self._account_id = None
        self.__has_account_id = False

    @property
    def name(self):
        """
        Details of a user's name.
        :rtype: Name
        """
        if self.__has_name:
            return self._name
        else:
            raise KeyError("missing required field 'name'")

    @name.setter
    def name(self, val):
        if not isinstance(val, Name):
            raise TypeError('name is of type %r but must be of type Name' % type(val).__name__)
        val.validate()
        self._name = val
        self.__has_name = True

    @name.deleter
    def name(self, val):
        self._name = None
        self.__has_name = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls._field_names_:
                raise KeyError("Unknown key: %r" % key)
        basic_account_info = BasicAccountInfo()
        if 'account_id' not in obj:
            raise KeyError("missing required field 'account_id'")
        basic_account_info.account_id = transformer.convert_from(basic_account_info.__account_id_data_type, obj['account_id'])
        if 'name' not in obj:
            raise KeyError("missing required field 'name'")
        basic_account_info.name = Name.from_dict(transformer, obj['name'])
        return basic_account_info

    def to_dict(self, transformer):
        d = dict(account_id=transformer.convert_to(self.__account_id_data_type, self._account_id),
                 name=self._name.to_dict(transformer))
        return d

    def __repr__(self):
        return 'BasicAccountInfo(%r)' % self._account_id

class MeInfo(BasicAccountInfo):
    """
    Information about a user's account.

    :ivar email: The user's e-mail address.
    :ivar country: The user's two-letter country code, if available.
    :ivar locale: The language setting that user specified.
    :ivar referral_link: The user's `referral link
        <https://www.dropbox.com/referrals>`_.
    :ivar space: The user's quota.
    :ivar team: If this account is a member of a team.
    :ivar is_paired: Whether the user has a personal and work account. If the
        authorized account is personal, then ``team`` will always be 'Null', but
        ``is_paired`` will indicate if a work account is linked.
    """

    __email_data_type = dt.String(pattern=None)
    __country_data_type = dt.String(min_length=2, max_length=2, pattern=None)
    __locale_data_type = dt.String(min_length=2, max_length=2, pattern=None)
    __referral_link_data_type = dt.String(pattern=None)
    __is_paired_data_type = dt.Boolean()

    _field_names_ = BasicAccountInfo._field_names_.union({
        'email',
        'country',
        'locale',
        'referral_link',
        'space',
        'team',
        'is_paired',
    })

    _fields_ = BasicAccountInfo._fields_ + [
        ('email', False, __email_data_type),
        ('country', True, __country_data_type),
        ('locale', False, __locale_data_type),
        ('referral_link', False, __referral_link_data_type),
        ('space', False, Space),
        ('team', True, Team),
        ('is_paired', False, __is_paired_data_type),
    ]

    def __init__(self):
        super(MeInfo, self).__init__()
        self._email = None
        self.__has_email = False
        self._country = None
        self.__has_country = False
        self._locale = None
        self.__has_locale = False
        self._referral_link = None
        self.__has_referral_link = False
        self._space = None
        self.__has_space = False
        self._team = None
        self.__has_team = False
        self._is_paired = None
        self.__has_is_paired = False

    def validate(self):
        return all([
            self.__has_account_id,
            self.__has_name,
            self.__has_email,
            self.__has_locale,
            self.__has_referral_link,
            self.__has_space,
            self.__has_is_paired,
        ])

    @property
    def email(self):
        """
        The user's e-mail address.
        :rtype: str
        """
        if self.__has_email:
            return self._email
        else:
            raise KeyError("missing required field 'email'")

    @email.setter
    def email(self, val):
        self.__email_data_type.validate(val)
        self._email = val
        self.__has_email = True

    @email.deleter
    def email(self, val):
        self._email = None
        self.__has_email = False

    @property
    def country(self):
        """
        The user's two-letter country code, if available.
        :rtype: str
        """
        if self.__has_country:
            return self._country
        else:
            return None

    @country.setter
    def country(self, val):
        self.__country_data_type.validate(val)
        self._country = val
        self.__has_country = True

    @country.deleter
    def country(self, val):
        self._country = None
        self.__has_country = False

    @property
    def locale(self):
        """
        The language setting that user specified.
        :rtype: str
        """
        if self.__has_locale:
            return self._locale
        else:
            raise KeyError("missing required field 'locale'")

    @locale.setter
    def locale(self, val):
        self.__locale_data_type.validate(val)
        self._locale = val
        self.__has_locale = True

    @locale.deleter
    def locale(self, val):
        self._locale = None
        self.__has_locale = False

    @property
    def referral_link(self):
        """
        The user's `referral link <https://www.dropbox.com/referrals>`_.
        :rtype: str
        """
        if self.__has_referral_link:
            return self._referral_link
        else:
            raise KeyError("missing required field 'referral_link'")

    @referral_link.setter
    def referral_link(self, val):
        self.__referral_link_data_type.validate(val)
        self._referral_link = val
        self.__has_referral_link = True

    @referral_link.deleter
    def referral_link(self, val):
        self._referral_link = None
        self.__has_referral_link = False

    @property
    def space(self):
        """
        The user's quota.
        :rtype: Space
        """
        if self.__has_space:
            return self._space
        else:
            raise KeyError("missing required field 'space'")

    @space.setter
    def space(self, val):
        if not isinstance(val, Space):
            raise TypeError('space is of type %r but must be of type Space' % type(val).__name__)
        val.validate()
        self._space = val
        self.__has_space = True

    @space.deleter
    def space(self, val):
        self._space = None
        self.__has_space = False

    @property
    def team(self):
        """
        If this account is a member of a team.
        :rtype: Team
        """
        if self.__has_team:
            return self._team
        else:
            return None

    @team.setter
    def team(self, val):
        if not isinstance(val, Team):
            raise TypeError('team is of type %r but must be of type Team' % type(val).__name__)
        val.validate()
        self._team = val
        self.__has_team = True

    @team.deleter
    def team(self, val):
        self._team = None
        self.__has_team = False

    @property
    def is_paired(self):
        """
        Whether the user has a personal and work account. If the authorized
        account is personal, then ``team`` will always be 'Null', but
        ``is_paired`` will indicate if a work account is linked.
        :rtype: bool
        """
        if self.__has_is_paired:
            return self._is_paired
        else:
            raise KeyError("missing required field 'is_paired'")

    @is_paired.setter
    def is_paired(self, val):
        self.__is_paired_data_type.validate(val)
        self._is_paired = val
        self.__has_is_paired = True

    @is_paired.deleter
    def is_paired(self, val):
        self._is_paired = None
        self.__has_is_paired = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls._field_names_:
                raise KeyError("Unknown key: %r" % key)
        me_info = MeInfo()
        if 'account_id' not in obj:
            raise KeyError("missing required field 'account_id'")
        me_info.account_id = transformer.convert_from(me_info.__account_id_data_type, obj['account_id'])
        if 'name' not in obj:
            raise KeyError("missing required field 'name'")
        me_info.name = Name.from_dict(transformer, obj['name'])
        if 'email' not in obj:
            raise KeyError("missing required field 'email'")
        me_info.email = transformer.convert_from(me_info.__email_data_type, obj['email'])
        if 'locale' not in obj:
            raise KeyError("missing required field 'locale'")
        me_info.locale = transformer.convert_from(me_info.__locale_data_type, obj['locale'])
        if 'referral_link' not in obj:
            raise KeyError("missing required field 'referral_link'")
        me_info.referral_link = transformer.convert_from(me_info.__referral_link_data_type, obj['referral_link'])
        if 'space' not in obj:
            raise KeyError("missing required field 'space'")
        me_info.space = Space.from_dict(transformer, obj['space'])
        if 'is_paired' not in obj:
            raise KeyError("missing required field 'is_paired'")
        me_info.is_paired = transformer.convert_from(me_info.__is_paired_data_type, obj['is_paired'])
        me_info.country = transformer.convert_from(me_info.__country_data_type, obj.get('country'))
        if obj.get('team') is not None:
            me_info.team = Team.from_dict(transformer, obj['team'])
        return me_info

    def to_dict(self, transformer):
        d = dict(account_id=transformer.convert_to(self.__account_id_data_type, self._account_id),
                 name=self._name.to_dict(transformer),
                 email=transformer.convert_to(self.__email_data_type, self._email),
                 locale=transformer.convert_to(self.__locale_data_type, self._locale),
                 referral_link=transformer.convert_to(self.__referral_link_data_type, self._referral_link),
                 space=self._space.to_dict(transformer),
                 is_paired=transformer.convert_to(self.__is_paired_data_type, self._is_paired))
        if self._country is not None:
            d['country'] = transformer.convert_to(self.__country_data_type, self._country)
        if self._team is not None:
            d['team'] = self._team.to_dict(transformer)
        return d

    def __repr__(self):
        return 'MeInfo(%r)' % self._email

class AccountInfo(dt.Union):
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

    def __init__(self):
        self._me = None
        self._teammate = None
        self._user = None
        self.__tag = None

    def validate(self):
        return self.__tag is not None

    def is_me(self):
        return self.__tag == 'me'

    def is_teammate(self):
        return self.__tag == 'teammate'

    def is_user(self):
        return self.__tag == 'user'

    @property
    def me(self):
        if not self.is_me():
            raise KeyError("tag 'me' not set")
        return self._me

    @me.setter
    def me(self, val):
        if not isinstance(val, MeInfo):
            raise TypeError('me is of type %r but must be of type MeInfo' % type(val).__name__)
        val.validate()
        self._me = val
        self.__tag = 'me'

    @property
    def teammate(self):
        if not self.is_teammate():
            raise KeyError("tag 'teammate' not set")
        return self._teammate

    @teammate.setter
    def teammate(self, val):
        if not isinstance(val, BasicAccountInfo):
            raise TypeError('teammate is of type %r but must be of type BasicAccountInfo' % type(val).__name__)
        val.validate()
        self._teammate = val
        self.__tag = 'teammate'

    @property
    def user(self):
        if not self.is_user():
            raise KeyError("tag 'user' not set")
        return self._user

    @user.setter
    def user(self, val):
        if not isinstance(val, BasicAccountInfo):
            raise TypeError('user is of type %r but must be of type BasicAccountInfo' % type(val).__name__)
        val.validate()
        self._user = val
        self.__tag = 'user'

    @classmethod
    def from_dict(cls, transformer, obj):
        account_info = cls()
        if isinstance(obj, dict) and len(obj) != 1:
            raise KeyError("Union can only have one key set not %d" % len(obj))
        if isinstance(obj, dict) and 'me' == obj.keys()[0]:
            account_info.me = MeInfo.from_dict(transformer, obj['me'])
        if isinstance(obj, dict) and 'teammate' == obj.keys()[0]:
            account_info.teammate = BasicAccountInfo.from_dict(transformer, obj['teammate'])
        if isinstance(obj, dict) and 'user' == obj.keys()[0]:
            account_info.user = BasicAccountInfo.from_dict(transformer, obj['user'])
        return account_info

    def to_dict(self, transformer):
        if self.is_me():
            return dict(me=self.me.to_dict(transformer))
        if self.is_teammate():
            return dict(teammate=self.teammate.to_dict(transformer))
        if self.is_user():
            return dict(user=self.user.to_dict(transformer))

    def __repr__(self):
        return 'AccountInfo(%r)' % self.__tag

class InfoRequest(dt.Struct):

    __account_id_data_type = dt.String(min_length=40, max_length=40, pattern=None)

    _field_names_ = {
        'account_id',
    }

    _fields_ = [
        ('account_id', False, __account_id_data_type),
    ]

    def __init__(self):
        self._account_id = None
        self.__has_account_id = False

    def validate(self):
        return all([
            self.__has_account_id,
        ])

    @property
    def account_id(self):
        """
        A user's account identifier.
        :rtype: str
        """
        if self.__has_account_id:
            return self._account_id
        else:
            raise KeyError("missing required field 'account_id'")

    @account_id.setter
    def account_id(self, val):
        self.__account_id_data_type.validate(val)
        self._account_id = val
        self.__has_account_id = True

    @account_id.deleter
    def account_id(self, val):
        self._account_id = None
        self.__has_account_id = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls._field_names_:
                raise KeyError("Unknown key: %r" % key)
        info_request = InfoRequest()
        if 'account_id' not in obj:
            raise KeyError("missing required field 'account_id'")
        info_request.account_id = transformer.convert_from(info_request.__account_id_data_type, obj['account_id'])
        return info_request

    def to_dict(self, transformer):
        d = dict(account_id=transformer.convert_to(self.__account_id_data_type, self._account_id))
        return d

    def __repr__(self):
        return 'InfoRequest(%r)' % self._account_id

class InfoError(dt.Union):

    NoAccount = object()

    def __init__(self):
        pass
        self.__tag = None

    def validate(self):
        return self.__tag is not None

    def is_no_account(self):
        return self.__tag == 'no_account'

    def set_no_account(self):
        self.__tag = 'no_account'

    @classmethod
    def from_dict(cls, transformer, obj):
        info_error = cls()
        if isinstance(obj, dict) and len(obj) != 1:
            raise KeyError("Union can only have one key set not %d" % len(obj))
        if obj == 'no_account':
            info_error.set_no_account()
        return info_error

    def to_dict(self, transformer):
        if self.is_no_account():
            return 'no_account'

    def __repr__(self):
        return 'InfoError(%r)' % self.__tag

