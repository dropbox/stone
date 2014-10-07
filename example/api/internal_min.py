from babelsdk.api import (
    Api,
    ApiOperation,
)
from babelsdk.segmentation import (
    Segment,
    SegmentList,
    Segmentation,
)
from babelsdk.data_type import (
    Binary,
    Boolean,
    Field,
    Float32,
    SymbolField,
    List,
    Int32,
    Int64,
    UInt32,
    UInt64,
    String,
    Struct,
    Timestamp,
    Union,
)

Field('shared', UInt32(), "The user's used quota in shared folders (bytes).")

Team = Struct(
    'Team',
    "Information about the team a user belongs to.",
    [
     Field('name', String(), "The name of the team."),
    ],
)

Team.add_example(
    'default',
    dict(
        name='Acme, Inc.',
    )
)

QuotaInfo = Struct(
    'QuotaInfo',
    'The space quota information for a user.',
    [
     Field('quota', UInt32(), "The user's total quota allocation (bytes)."),
     Field('normal', UInt32(), "The user's used quota outside of shared folders (bytes)."),
     Field('shared', UInt32(), "The user's used quota in shared folders (bytes)."),
     ],
)

QuotaInfo.add_example(
    'default',
    dict(
        quota=1000000,
        normal=1000,
        shared=500,
    )
)

AccountInfo = Struct(
    'AccountInfo',
    "Information regarding a user's account.",
    [
     Field('user_id', String(), "The user's unique Dropbox ID."),
     Field('display_name', String(), 'The name of the user.'),
     Field('country', String(), "The user's two-letter country code, if available."),
     Field('referral_link', String(), "The user's referral link.", nullable=True),
     Field('team', Team, "If the user belongs to a team, contains team information. Otherwise, null", nullable=True),
     Field('quota_info', QuotaInfo, "The user's quota."),
     ],
)

# Paired account should be another example!
AccountInfo.add_example(
    'default',
    dict(
        user_id='abcd1234',
        display_name='Ken Elkabany',
        country='US',
        referral_link=None,
    ),
)

AccountInfo.add_example(
    'unpaired',
    dict(
        user_id='abcd1234',
        display_name='Ken Elkabany',
        country='US',
        referral_link=None,
        team=None,
    ),
)

InfoRequest = Struct(
    'InfoRequest',
    "Query details about a user.",
    [
     Field('user_id', String(), "The user to query."),
    ],
)

InfoOp = ApiOperation(
    'Info',
    'info',
    "Get information about a user's account.",
    Segmentation([Segment('in', InfoRequest)]),
    Segmentation([Segment('info', AccountInfo)]),
)

UpdateIfMatchingParentRev = Struct(
    'UpdateIfMatchingParentRev',
    "On a write conflict, overwrite the existing file.",
    [
     Field('parent_rev', String(), "The revision to be updated."),
     Field('auto_rename', Boolean(), "Whether the new file should be renamed on a conflict."),
    ]
)
UpdateIfMatchingParentRev.add_example(
    'default',
    {'parent_rev': '2342',
     'auto_rename': False},
)

WriteConflictPolicy = Union(
    'WriteConflictPolicy',
    "Policy for managing write conflicts.",
    [
     SymbolField('reject', "On a write conflict, reject the new file."),
     SymbolField('overwrite', "On a write conflict, overwrite the existing file."),
     SymbolField('rename', "On a write conflict, rename the new file with a numerical suffix."),
     Field('update_if_matching_parent_rev', UpdateIfMatchingParentRev, "Update only if the parent revision matches."),
     ]
)

DbxTimestamp = Timestamp('%a, %d %b %Y %H:%M:%S')

MediaInfo = Struct(
    'MediaInfo',
    "Media type specific metadata.",
    [
     Field('lat_long', List(Float32(), min_items=2, max_items=2), 'The coordinates where a photo was taken.'),
     Field('time_taken', DbxTimestamp, 'When created.'),
     ],
)

MediaInfo.add_example(
    'default',
    {'lat_long': [1234.3232, 1],
     'time_taken': 'Sat, 28 Jun 2014 18:23:21'}
)

EntryInfo = Struct(
    'EntryInfo',
    'Information for a file or directory.',
    [
     Field('created', DbxTimestamp, 'When created.')
     ]
)

EntryInfo.add_example(
    'default',
    {'created': 'Sat, 28 Jun 2014 18:23:21'},
)

api = Api('0.1')
users_namespace = api.ensure_namespace('users')
users_namespace.add_data_type(Team)
users_namespace.add_data_type(QuotaInfo)
users_namespace.add_data_type(AccountInfo)
users_namespace.add_operation(InfoOp)
