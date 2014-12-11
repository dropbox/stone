import babel_data_types as dt

class Empty(object):

    __slots__ = [
    ]

    _field_names_ = {
    }

    _fields_ = [
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return 'Empty()'

class Usage(object):
    """
    The space quota info for a user.

    :ivar quota: The user's total quota allocation (bytes).
    :ivar usage_individual: The user's used quota not including shared folders
        (bytes).
    :ivar usage_shared: The user's used quota in shared folders (bytes).
    :ivar usage_datastores: The user's used quota in datastores (bytes).
    """

    __slots__ = [
        '_quota',
        '__has_quota',
        '_usage_individual',
        '__has_usage_individual',
        '_usage_shared',
        '__has_usage_shared',
        '_usage_datastores',
        '__has_usage_datastores',
    ]

    __quota_data_type = dt.UInt64()
    __usage_individual_data_type = dt.UInt64()
    __usage_shared_data_type = dt.UInt64()
    __usage_datastores_data_type = dt.UInt64()

    _field_names_ = {
        'quota',
        'usage_individual',
        'usage_shared',
        'usage_datastores',
    }

    _fields_ = [
        ('quota', False, __quota_data_type),
        ('usage_individual', False, __usage_individual_data_type),
        ('usage_shared', False, __usage_shared_data_type),
        ('usage_datastores', False, __usage_datastores_data_type),
    ]

    def __init__(self):
        self._quota = None
        self.__has_quota = False
        self._usage_individual = None
        self.__has_usage_individual = False
        self._usage_shared = None
        self.__has_usage_shared = False
        self._usage_datastores = None
        self.__has_usage_datastores = False

    @property
    def quota(self):
        """
        The user's total quota allocation (bytes).
        :rtype: long
        """
        if self.__has_quota:
            return self._quota
        else:
            raise AttributeError("missing required field 'quota'")

    @quota.setter
    def quota(self, val):
        self.__quota_data_type.validate(val)
        self._quota = val
        self.__has_quota = True

    @quota.deleter
    def quota(self):
        self._quota = None
        self.__has_quota = False

    @property
    def usage_individual(self):
        """
        The user's used quota not including shared folders (bytes).
        :rtype: long
        """
        if self.__has_usage_individual:
            return self._usage_individual
        else:
            raise AttributeError("missing required field 'usage_individual'")

    @usage_individual.setter
    def usage_individual(self, val):
        self.__usage_individual_data_type.validate(val)
        self._usage_individual = val
        self.__has_usage_individual = True

    @usage_individual.deleter
    def usage_individual(self):
        self._usage_individual = None
        self.__has_usage_individual = False

    @property
    def usage_shared(self):
        """
        The user's used quota in shared folders (bytes).
        :rtype: long
        """
        if self.__has_usage_shared:
            return self._usage_shared
        else:
            raise AttributeError("missing required field 'usage_shared'")

    @usage_shared.setter
    def usage_shared(self, val):
        self.__usage_shared_data_type.validate(val)
        self._usage_shared = val
        self.__has_usage_shared = True

    @usage_shared.deleter
    def usage_shared(self):
        self._usage_shared = None
        self.__has_usage_shared = False

    @property
    def usage_datastores(self):
        """
        The user's used quota in datastores (bytes).
        :rtype: long
        """
        if self.__has_usage_datastores:
            return self._usage_datastores
        else:
            raise AttributeError("missing required field 'usage_datastores'")

    @usage_datastores.setter
    def usage_datastores(self, val):
        self.__usage_datastores_data_type.validate(val)
        self._usage_datastores = val
        self.__has_usage_datastores = True

    @usage_datastores.deleter
    def usage_datastores(self):
        self._usage_datastores = None
        self.__has_usage_datastores = False

    def __repr__(self):
        return 'Usage(quota=%r)' % self._quota

class Team(object):
    """
    Information about a team.

    :ivar id: The team's unique ID.
    :ivar name: The name of the team.
    """

    __slots__ = [
        '_id',
        '__has_id',
        '_name',
        '__has_name',
    ]

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

    @property
    def id(self):
        """
        The team's unique ID.
        :rtype: str
        """
        if self.__has_id:
            return self._id
        else:
            raise AttributeError("missing required field 'id'")

    @id.setter
    def id(self, val):
        self.__id_data_type.validate(val)
        self._id = val
        self.__has_id = True

    @id.deleter
    def id(self):
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
            raise AttributeError("missing required field 'name'")

    @name.setter
    def name(self, val):
        self.__name_data_type.validate(val)
        self._name = val
        self.__has_name = True

    @name.deleter
    def name(self):
        self._name = None
        self.__has_name = False

    def __repr__(self):
        return 'Team(id=%r)' % self._id

class Name(object):
    """
    Contains several ways a name might be represented to make
    internationalization more convenient.

    :ivar given_name: Also known as a first name.
    :ivar surname: Also known as a last name or family name.
    :ivar familiar_name: Locale-dependent name. In the US, a person's familiar
        name is their ``given_name``, but elsewhere, it could be any combination
        of a person's ``given_name`` and ``surname``.
    :ivar display_name: A name that can be used directly to represent the name
        of a user's Dropbox account.
    """

    __slots__ = [
        '_given_name',
        '__has_given_name',
        '_surname',
        '__has_surname',
        '_familiar_name',
        '__has_familiar_name',
        '_display_name',
        '__has_display_name',
    ]

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

    @property
    def given_name(self):
        """
        Also known as a first name.
        :rtype: str
        """
        if self.__has_given_name:
            return self._given_name
        else:
            raise AttributeError("missing required field 'given_name'")

    @given_name.setter
    def given_name(self, val):
        self.__given_name_data_type.validate(val)
        self._given_name = val
        self.__has_given_name = True

    @given_name.deleter
    def given_name(self):
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
            raise AttributeError("missing required field 'surname'")

    @surname.setter
    def surname(self, val):
        self.__surname_data_type.validate(val)
        self._surname = val
        self.__has_surname = True

    @surname.deleter
    def surname(self):
        self._surname = None
        self.__has_surname = False

    @property
    def familiar_name(self):
        """
        Locale-dependent name. In the US, a person's familiar name is their
        ``given_name``, but elsewhere, it could be any combination of a person's
        ``given_name`` and ``surname``.
        :rtype: str
        """
        if self.__has_familiar_name:
            return self._familiar_name
        else:
            raise AttributeError("missing required field 'familiar_name'")

    @familiar_name.setter
    def familiar_name(self, val):
        self.__familiar_name_data_type.validate(val)
        self._familiar_name = val
        self.__has_familiar_name = True

    @familiar_name.deleter
    def familiar_name(self):
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
            raise AttributeError("missing required field 'display_name'")

    @display_name.setter
    def display_name(self, val):
        self.__display_name_data_type.validate(val)
        self._display_name = val
        self.__has_display_name = True

    @display_name.deleter
    def display_name(self):
        self._display_name = None
        self.__has_display_name = False

    def __repr__(self):
        return 'Name(given_name=%r)' % self._given_name

class Account(object):
    """
    The amount of detail revealed about an account depends on the user being
    queried and the user making the query.

    :ivar account_id: The user's unique Dropbox ID.
    :ivar name: Details of a user's name.
    """

    __slots__ = [
        '_account_id',
        '__has_account_id',
        '_name',
        '__has_name',
    ]

    __account_id_data_type = dt.String(min_length=40, max_length=40, pattern=None)
    __name_data_type = dt.Struct(Name)

    _field_names_ = {
        'account_id',
        'name',
    }

    _fields_ = [
        ('account_id', False, __account_id_data_type),
        ('name', False, __name_data_type),
    ]

    def __init__(self):
        self._account_id = None
        self.__has_account_id = False
        self._name = None
        self.__has_name = False

    @property
    def account_id(self):
        """
        The user's unique Dropbox ID.
        :rtype: str
        """
        if self.__has_account_id:
            return self._account_id
        else:
            raise AttributeError("missing required field 'account_id'")

    @account_id.setter
    def account_id(self, val):
        self.__account_id_data_type.validate(val)
        self._account_id = val
        self.__has_account_id = True

    @account_id.deleter
    def account_id(self):
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
            raise AttributeError("missing required field 'name'")

    @name.setter
    def name(self, val):
        self.__name_data_type.validate_type_only(val)
        self._name = val
        self.__has_name = True

    @name.deleter
    def name(self):
        self._name = None
        self.__has_name = False

    def __repr__(self):
        return 'Account(account_id=%r)' % self._account_id

class BasicAccount(Account):
    """
    Basic information about any account.

    :ivar is_teammate: Whether this user is a teammate of the current user. If
        this account is the current user's account, then this will be 'true'.
    """

    __slots__ = [
        '_is_teammate',
        '__has_is_teammate',
    ]

    __is_teammate_data_type = dt.Boolean()

    _field_names_ = Account._field_names_.union({
        'is_teammate',
    })

    _fields_ = Account._fields_ + [
        ('is_teammate', False, __is_teammate_data_type),
    ]

    def __init__(self):
        super(BasicAccount, self).__init__()
        self._is_teammate = None
        self.__has_is_teammate = False

    @property
    def is_teammate(self):
        """
        Whether this user is a teammate of the current user. If this account is
        the current user's account, then this will be 'true'.
        :rtype: bool
        """
        if self.__has_is_teammate:
            return self._is_teammate
        else:
            raise AttributeError("missing required field 'is_teammate'")

    @is_teammate.setter
    def is_teammate(self, val):
        self.__is_teammate_data_type.validate(val)
        self._is_teammate = val
        self.__has_is_teammate = True

    @is_teammate.deleter
    def is_teammate(self):
        self._is_teammate = None
        self.__has_is_teammate = False

    def __repr__(self):
        return 'BasicAccount(account_id=%r)' % self._account_id

class FullAccount(Account):
    """
    Detailed information about the current user's account.

    :ivar email: The user's e-mail address.
    :ivar country: The user's two-letter country code, if available. Country
        codes are based on `ISO 3166-1
        <http://en.wikipedia.org/wiki/ISO_3166-1>`_.
    :ivar locale: The language that the user specified. Locale tags will be
        `IETF language tags <http://en.wikipedia.org/wiki/IETF_language_tag>`_.
    :ivar referral_link: The user's `referral link
        <https://www.dropbox.com/referrals>`_.
    :ivar usage: The user's quota.
    :ivar team: If this account is a member of a team.
    :ivar is_paired: Whether the user has a personal and work account. If the
        current  account is personal, then ``team`` will always be 'Null', but
        ``is_paired`` will indicate if a work account is linked.
    """

    __slots__ = [
        '_email',
        '__has_email',
        '_country',
        '__has_country',
        '_locale',
        '__has_locale',
        '_referral_link',
        '__has_referral_link',
        '_usage',
        '__has_usage',
        '_team',
        '__has_team',
        '_is_paired',
        '__has_is_paired',
    ]

    __email_data_type = dt.String(pattern=None)
    __country_data_type = dt.String(min_length=2, max_length=2, pattern=None)
    __locale_data_type = dt.String(min_length=2, max_length=2, pattern=None)
    __referral_link_data_type = dt.String(pattern=None)
    __usage_data_type = dt.Struct(Usage)
    __team_data_type = dt.Struct(Team)
    __is_paired_data_type = dt.Boolean()

    _field_names_ = Account._field_names_.union({
        'email',
        'country',
        'locale',
        'referral_link',
        'usage',
        'team',
        'is_paired',
    })

    _fields_ = Account._fields_ + [
        ('email', False, __email_data_type),
        ('country', True, __country_data_type),
        ('locale', False, __locale_data_type),
        ('referral_link', False, __referral_link_data_type),
        ('usage', False, __usage_data_type),
        ('team', True, __team_data_type),
        ('is_paired', False, __is_paired_data_type),
    ]

    def __init__(self):
        super(FullAccount, self).__init__()
        self._email = None
        self.__has_email = False
        self._country = None
        self.__has_country = False
        self._locale = None
        self.__has_locale = False
        self._referral_link = None
        self.__has_referral_link = False
        self._usage = None
        self.__has_usage = False
        self._team = None
        self.__has_team = False
        self._is_paired = None
        self.__has_is_paired = False

    @property
    def email(self):
        """
        The user's e-mail address.
        :rtype: str
        """
        if self.__has_email:
            return self._email
        else:
            raise AttributeError("missing required field 'email'")

    @email.setter
    def email(self, val):
        self.__email_data_type.validate(val)
        self._email = val
        self.__has_email = True

    @email.deleter
    def email(self):
        self._email = None
        self.__has_email = False

    @property
    def country(self):
        """
        The user's two-letter country code, if available. Country codes are
        based on `ISO 3166-1 <http://en.wikipedia.org/wiki/ISO_3166-1>`_.
        :rtype: str
        """
        if self.__has_country:
            return self._country
        else:
            return None

    @country.setter
    def country(self, val):
        if val is None:
            del self.country
            return
        self.__country_data_type.validate(val)
        self._country = val
        self.__has_country = True

    @country.deleter
    def country(self):
        self._country = None
        self.__has_country = False

    @property
    def locale(self):
        """
        The language that the user specified. Locale tags will be `IETF language
        tags <http://en.wikipedia.org/wiki/IETF_language_tag>`_.
        :rtype: str
        """
        if self.__has_locale:
            return self._locale
        else:
            raise AttributeError("missing required field 'locale'")

    @locale.setter
    def locale(self, val):
        self.__locale_data_type.validate(val)
        self._locale = val
        self.__has_locale = True

    @locale.deleter
    def locale(self):
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
            raise AttributeError("missing required field 'referral_link'")

    @referral_link.setter
    def referral_link(self, val):
        self.__referral_link_data_type.validate(val)
        self._referral_link = val
        self.__has_referral_link = True

    @referral_link.deleter
    def referral_link(self):
        self._referral_link = None
        self.__has_referral_link = False

    @property
    def usage(self):
        """
        The user's quota.
        :rtype: Usage
        """
        if self.__has_usage:
            return self._usage
        else:
            raise AttributeError("missing required field 'usage'")

    @usage.setter
    def usage(self, val):
        self.__usage_data_type.validate_type_only(val)
        self._usage = val
        self.__has_usage = True

    @usage.deleter
    def usage(self):
        self._usage = None
        self.__has_usage = False

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
        if val is None:
            del self.team
            return
        self.__team_data_type.validate_type_only(val)
        self._team = val
        self.__has_team = True

    @team.deleter
    def team(self):
        self._team = None
        self.__has_team = False

    @property
    def is_paired(self):
        """
        Whether the user has a personal and work account. If the current
        account is personal, then ``team`` will always be 'Null', but
        ``is_paired`` will indicate if a work account is linked.
        :rtype: bool
        """
        if self.__has_is_paired:
            return self._is_paired
        else:
            raise AttributeError("missing required field 'is_paired'")

    @is_paired.setter
    def is_paired(self, val):
        self.__is_paired_data_type.validate(val)
        self._is_paired = val
        self.__has_is_paired = True

    @is_paired.deleter
    def is_paired(self):
        self._is_paired = None
        self.__has_is_paired = False

    def __repr__(self):
        return 'FullAccount(account_id=%r)' % self._account_id

class GetAccountReq(object):

    __slots__ = [
        '_account_id',
        '__has_account_id',
    ]

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

    @property
    def account_id(self):
        """
        A user's account identifier.
        :rtype: str
        """
        if self.__has_account_id:
            return self._account_id
        else:
            raise AttributeError("missing required field 'account_id'")

    @account_id.setter
    def account_id(self, val):
        self.__account_id_data_type.validate(val)
        self._account_id = val
        self.__has_account_id = True

    @account_id.deleter
    def account_id(self):
        self._account_id = None
        self.__has_account_id = False

    def __repr__(self):
        return 'GetAccountReq(account_id=%r)' % self._account_id

class GetAccountError(object):

    __no_account_data_type = dt.Any()
    __unknown_data_type = dt.Symbol()
    _catch_all_ = 'unknown'

    _field_names_ = {
        'no_account',
        'unknown',
    }

    _fields_ = {
        'no_account': __no_account_data_type,
        'unknown': __unknown_data_type,
    }

    def __init__(self):
        self._no_account = None
        self._tag = None

    @classmethod
    def create_and_set_no_account(cls):
        """
        :rtype: GetAccountError
        """
        c = cls()
        c.set_no_account()
        return c

    @classmethod
    def create_and_set_unknown(cls):
        """
        :rtype: GetAccountError
        """
        c = cls()
        c.set_unknown()
        return c

    def is_no_account(self):
        return self._tag == 'no_account'

    def is_unknown(self):
        return self._tag == 'unknown'

    def set_no_account(self):
        self._tag = 'no_account'

    def set_unknown(self):
        self._tag = 'unknown'

    def __repr__(self):
        return 'GetAccountError(%r)' % self._tag

class GetAccountRoute(object):
    """
    Get information about a user's account.
    """
    request_data_type = dt.Struct(GetAccountReq)
    response_data_type = dt.Struct(BasicAccount)
    error_data_type = dt.Union(GetAccountError)

    attrs = {}

class GetMyAccountRoute(object):
    """
    Get information about the current user's account.
    """
    request_data_type = dt.Struct(Empty)
    response_data_type = dt.Struct(FullAccount)
    error_data_type = dt.Struct(Empty)

    attrs = {}

