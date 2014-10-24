class Empty(object):

    def __init__(self):
        pass

class Space(object):
    """
    The space quota info for a user.
    """

    def __init__(self,
                 quota,
                 private,
                 shared,
                 datastores):
        # The user's total quota allocation (bytes).
        self.quota = quota
        # The user's used quota outside of shared folders (bytes).
        self.private = private
        # The user's used quota in shared folders (bytes).
        self.shared = shared
        # The user's used quota in datastores (bytes).
        self.datastores = datastores

class Team(object):
    """
    Information about a team.
    """

    def __init__(self,
                 id,
                 name):
        # The team's unique ID.
        self.id = id
        # The name of the team.
        self.name = name

class Name(object):
    """
    Contains several ways a name might be represented to make
    internationalization more convenient.
    """

    def __init__(self,
                 given_name,
                 surname,
                 familiar_name,
                 display_name):
        # Also known as a first name.
        self.given_name = given_name
        # Also known as a last name or family name.
        self.surname = surname
        # Locale-dependent familiar name. Generally matches :field:`given_name`
        # or :field:`display_name`.
        self.familiar_name = familiar_name
        # A name that can be used directly to represent the name of a user's
        # Dropbox account.
        self.display_name = display_name

class BasicAccountInfo(object):
    """
    Basic information about a user's account.
    """

    def __init__(self,
                 account_id,
                 name):
        # The user's unique Dropbox ID.
        self.account_id = account_id
        # Details of a user's name.
        self.name = name

class MeInfo(object):
    """
    Information about a user's account.
    """

    def __init__(self,
                 email,
                 country,
                 locale,
                 referral_link,
                 space,
                 team,
                 is_paired):
        # The user's e-mail address.
        self.email = email
        # The user's two-letter country code, if available.
        self.country = country
        # The language setting that user specified.
        self.locale = locale
        # The user's :link:`referral link https://www.dropbox.com/referrals`.
        self.referral_link = referral_link
        # The user's quota.
        self.space = space
        # If this account is a member of a team.
        self.team = team
        # Whether the user has a personal and work account. If the authorized
        # account is personal, then :field:`team` will always be :val:`Null`,
        # but :field:`is_paired` will indicate if a work account is linked.
        self.is_paired = is_paired

class InfoRequest(object):

    def __init__(self,
                 account_id):
        # A user's account identifier. Use :val:`"me"` to get information for
        # the current account.
        self.account_id = account_id

