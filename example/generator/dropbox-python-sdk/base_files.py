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

class FileTarget(object):

    def __init__(self,
                 path,
                 rev=None,
                 **kwargs):
        """
        :param str path: Path from root. Should be an empty string for root.
        :param str rev: Revision of target file.
        """
        assert isinstance(path, six.string_types), 'path must be of type six.string_types'
        self.path = path

        if rev is not None:
            assert isinstance(rev, six.string_types), 'rev must be of type six.string_types'
        self.rev = rev

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return FileTarget(**obj)

    def to_json(self):
        d = dict(path=self.path)
        if self.rev:
            d['rev'] = self.rev
        return d

    def __repr__(self):
        return 'FileTarget(%r)' % self.path

class FileInfo(object):

    def __init__(self,
                 name,
                 **kwargs):
        """
        :param str name: Name of file.
        """
        assert isinstance(name, six.string_types), 'name must be of type six.string_types'
        self.name = name

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return FileInfo(**obj)

    def to_json(self):
        d = dict(name=self.name)
        return d

    def __repr__(self):
        return 'FileInfo(%r)' % self.name

class SubError(object):

    def __init__(self,
                 reason,
                 **kwargs):
        """
        :param str reason: A code indicating the type of error.
        """
        assert isinstance(reason, six.string_types), 'reason must be of type six.string_types'
        self.reason = reason

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return SubError(**obj)

    def to_json(self):
        d = dict(reason=self.reason)
        return d

    def __repr__(self):
        return 'SubError(%r)' % self.reason

class DownloadError(object):

    Disallowed = SubError
    NoFile = SubError

    def __init__(self,
                 disallowed=None,
                 no_file=None,
                 **kwargs):
        """
        Only one argument can be set.

        :type disallowed: :class:`SubError`
        :type no_file: :class:`SubError`
        """
        assert_only_one(disallowed=disallowed,
                        no_file=no_file,
                        **kwargs)
        self.disallowed = None
        self.no_file = None

        if disallowed is not None:
            assert isinstance(disallowed, SubError), 'disallowed must be of type SubError'
            self.disallowed = disallowed
            self._tag = 'disallowed'

        if no_file is not None:
            assert isinstance(no_file, SubError), 'no_file must be of type SubError'
            self.no_file = no_file
            self._tag = 'no_file'

    def is_disallowed(self):
        return self._tag == 'disallowed'

    def is_no_file(self):
        return self._tag == 'no_file'

    @classmethod
    def from_json(self, obj):
        obj = copy.copy(obj)
        assert len(obj) == 1, 'One key must be set, not %d' % len(obj)
        if 'disallowed' in obj:
            obj['disallowed'] = SubError.from_json(obj['disallowed'])
        if 'no_file' in obj:
            obj['no_file'] = SubError.from_json(obj['no_file'])
        return DownloadError(**obj)

    def to_json(self):
        if self._tag == 'disallowed':
            return dict(disallowed=self.disallowed.to_json())
        if self._tag == 'no_file':
            return dict(no_file=self.no_file.to_json())

    def __repr__(self):
        return 'DownloadError(%r)' % self._tag

class UploadSessionStart(object):

    def __init__(self,
                 upload_id,
                 **kwargs):
        """
        :param str upload_id: A unique identifier for the upload session.
        """
        assert isinstance(upload_id, six.string_types), 'upload_id must be of type six.string_types'
        self.upload_id = upload_id

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return UploadSessionStart(**obj)

    def to_json(self):
        d = dict(upload_id=self.upload_id)
        return d

    def __repr__(self):
        return 'UploadSessionStart(%r)' % self.upload_id

class UploadAppend(object):

    def __init__(self,
                 upload_id,
                 offset,
                 **kwargs):
        """
        :param str upload_id: Identifies the upload session to append data to.
        :param long offset: The offset into the file of the current chunk of
            data being uploaded. It can also be thought of as the amount of data
            that has been uploaded so far. We use the offset as a sanity check.
        """
        assert isinstance(upload_id, six.string_types), 'upload_id must be of type six.string_types'
        self.upload_id = upload_id

        assert isinstance(offset, numbers.Integral), 'offset must be of type numbers.Integral'
        self.offset = offset

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return UploadAppend(**obj)

    def to_json(self):
        d = dict(upload_id=self.upload_id,
                 offset=self.offset)
        return d

    def __repr__(self):
        return 'UploadAppend(%r)' % self.upload_id

class IncorrectOffsetError(object):

    def __init__(self,
                 correct_offset,
                 **kwargs):
        """
        :type correct_offset: long
        """
        assert isinstance(correct_offset, numbers.Integral), 'correct_offset must be of type numbers.Integral'
        self.correct_offset = correct_offset

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return IncorrectOffsetError(**obj)

    def to_json(self):
        d = dict(correct_offset=self.correct_offset)
        return d

    def __repr__(self):
        return 'IncorrectOffsetError(%r)' % self.correct_offset

class UploadAppendError(object):

    NotFound = object()
    Closed = object()
    IncorrectOffset = IncorrectOffsetError

    def __init__(self,
                 not_found=None,
                 closed=None,
                 incorrect_offset=None,
                 **kwargs):
        """
        Only one argument can be set.

        :param bool not_found: ``upload_id`` was not found.
        :param bool closed: Upload session was closed.
        :type incorrect_offset: :class:`IncorrectOffsetError`
        """
        assert_only_one(not_found=not_found,
                        closed=closed,
                        incorrect_offset=incorrect_offset,
                        **kwargs)
        self.not_found = None
        self.closed = None
        self.incorrect_offset = None

        if not_found is not None:
            assert isinstance(not_found, bool), 'not_found must be of type bool'
            self.not_found = not_found
            self._tag = 'not_found'

        if closed is not None:
            assert isinstance(closed, bool), 'closed must be of type bool'
            self.closed = closed
            self._tag = 'closed'

        if incorrect_offset is not None:
            assert isinstance(incorrect_offset, IncorrectOffsetError), 'incorrect_offset must be of type IncorrectOffsetError'
            self.incorrect_offset = incorrect_offset
            self._tag = 'incorrect_offset'

    def is_not_found(self):
        return self._tag == 'not_found'

    def is_closed(self):
        return self._tag == 'closed'

    def is_incorrect_offset(self):
        return self._tag == 'incorrect_offset'

    @classmethod
    def from_json(self, obj):
        obj = copy.copy(obj)
        assert len(obj) == 1, 'One key must be set, not %d' % len(obj)
        if obj == 'not_found':
            return obj
        if obj == 'closed':
            return obj
        if 'incorrect_offset' in obj:
            obj['incorrect_offset'] = IncorrectOffsetError.from_json(obj['incorrect_offset'])
        return UploadAppendError(**obj)

    def to_json(self):
        if self._tag == 'not_found':
            return self._tag
        if self._tag == 'closed':
            return self._tag
        if self._tag == 'incorrect_offset':
            return dict(incorrect_offset=self.incorrect_offset.to_json())

    def __repr__(self):
        return 'UploadAppendError(%r)' % self._tag

class UpdateParentRev(object):

    def __init__(self,
                 parent_rev,
                 **kwargs):
        """
        :type parent_rev: str
        """
        assert isinstance(parent_rev, six.string_types), 'parent_rev must be of type six.string_types'
        self.parent_rev = parent_rev

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        return UpdateParentRev(**obj)

    def to_json(self):
        d = dict(parent_rev=self.parent_rev)
        return d

    def __repr__(self):
        return 'UpdateParentRev(%r)' % self.parent_rev

class ConflictPolicy(object):
    """
    The action to take when a file path conflict exists.

    :ivar Overwrite: On a conflict, the target is overridden.
    :ivar Add: On a conflict, the upload is rejected. You can call the
        :meth:`upload` endpoint again and attempt a different path.
    :ivar Update: On a conflict, only overwrite the target if the parent_rev
        matches.
    """

    Overwrite = object()
    Add = object()
    Update = UpdateParentRev

    def __init__(self,
                 overwrite=None,
                 add=None,
                 update=None,
                 **kwargs):
        """
        Only one argument can be set.

        :param bool overwrite: On a conflict, the target is overridden.
        :param bool add: On a conflict, the upload is rejected. You can call the
            :meth:`upload` endpoint again and attempt a different path.
        :param update: On a conflict, only overwrite the target if the
            parent_rev matches.
        :type update: :class:`UpdateParentRev`
        """
        assert_only_one(overwrite=overwrite,
                        add=add,
                        update=update,
                        **kwargs)
        self.overwrite = None
        self.add = None
        self.update = None

        if overwrite is not None:
            assert isinstance(overwrite, bool), 'overwrite must be of type bool'
            self.overwrite = overwrite
            self._tag = 'overwrite'

        if add is not None:
            assert isinstance(add, bool), 'add must be of type bool'
            self.add = add
            self._tag = 'add'

        if update is not None:
            assert isinstance(update, UpdateParentRev), 'update must be of type UpdateParentRev'
            self.update = update
            self._tag = 'update'

    def is_overwrite(self):
        return self._tag == 'overwrite'

    def is_add(self):
        return self._tag == 'add'

    def is_update(self):
        return self._tag == 'update'

    @classmethod
    def from_json(self, obj):
        obj = copy.copy(obj)
        assert len(obj) == 1, 'One key must be set, not %d' % len(obj)
        if obj == 'overwrite':
            return obj
        if obj == 'add':
            return obj
        if 'update' in obj:
            obj['update'] = UpdateParentRev.from_json(obj['update'])
        return ConflictPolicy(**obj)

    def to_json(self):
        if self._tag == 'overwrite':
            return self._tag
        if self._tag == 'add':
            return self._tag
        if self._tag == 'update':
            return dict(update=self.update.to_json())

    def __repr__(self):
        return 'ConflictPolicy(%r)' % self._tag

class UploadCommit(object):

    def __init__(self,
                 path,
                 mode,
                 append_to=None,
                 autorename=None,
                 client_modified_utc=None,
                 mute=None,
                 **kwargs):
        """
        :param str path: Path in the user's Dropbox to save the file.
        :param mode: The course of action to take if a file already exists at
            ``path``.
        :type mode: :class:`ConflictPolicy`
        :param append_to: If specified, the current chunk of data should be
            appended to an existing upload session.
        :type append_to: :class:`UploadAppend`
        :param bool autorename: Whether the file should be autorenamed in the
            event of a conflict.
        :param long client_modified_utc: Self reported time of when this file
            was created or modified.
        :param bool mute: Whether the devices that the user has linked should
            notify them of the new or updated file.
        """
        assert isinstance(path, six.string_types), 'path must be of type six.string_types'
        self.path = path

        if mode == ConflictPolicy.Overwrite:
            self.mode = ConflictPolicy(overwrite=True)
        if mode == ConflictPolicy.Add:
            self.mode = ConflictPolicy(add=True)
        if isinstance(mode, ConflictPolicy.Update):
            self.mode = ConflictPolicy(update=mode)

        if append_to is not None:
            assert isinstance(append_to, UploadAppend), 'append_to must be of type UploadAppend'
        self.append_to = append_to

        if autorename is not None:
            assert isinstance(autorename, bool), 'autorename must be of type bool'
        self.autorename = autorename

        if client_modified_utc is not None:
            assert isinstance(client_modified_utc, numbers.Integral), 'client_modified_utc must be of type numbers.Integral'
        self.client_modified_utc = client_modified_utc

        if mute is not None:
            assert isinstance(mute, bool), 'mute must be of type bool'
        self.mute = mute

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        obj['mode'] = ConflictPolicy.from_json(obj['mode'])
        obj['append_to'] = UploadAppend.from_json(obj['append_to'])
        return UploadCommit(**obj)

    def to_json(self):
        d = dict(path=self.path,
                 mode=self.mode.to_json())
        if self.append_to:
            d['append_to'] = self.append_to.to_json()
        if self.autorename:
            d['autorename'] = self.autorename
        if self.client_modified_utc:
            d['client_modified_utc'] = self.client_modified_utc
        if self.mute:
            d['mute'] = self.mute
        return d

    def __repr__(self):
        return 'UploadCommit(%r)' % self.path

class ConflictReason(object):

    Folder = object()
    File = object()
    AutorenameFailed = object()
    Unknown = object()

    def __init__(self,
                 folder=None,
                 file=None,
                 autorename_failed=None,
                 unknown=None,
                 **kwargs):
        """
        Only one argument can be set.

        :param bool folder: Conflict with a folder.
        :param bool file: Conflict with a file.
        :param bool autorename_failed: Could not autorename.
        :type unknown: bool
        """
        assert_only_one(folder=folder,
                        file=file,
                        autorename_failed=autorename_failed,
                        unknown=unknown,
                        **kwargs)
        self.folder = None
        self.file = None
        self.autorename_failed = None
        self.unknown = None

        if folder is not None:
            assert isinstance(folder, bool), 'folder must be of type bool'
            self.folder = folder
            self._tag = 'folder'

        if file is not None:
            assert isinstance(file, bool), 'file must be of type bool'
            self.file = file
            self._tag = 'file'

        if autorename_failed is not None:
            assert isinstance(autorename_failed, bool), 'autorename_failed must be of type bool'
            self.autorename_failed = autorename_failed
            self._tag = 'autorename_failed'

        if unknown is not None:
            assert isinstance(unknown, bool), 'unknown must be of type bool'
            self.unknown = unknown
            self._tag = 'unknown'

    def is_folder(self):
        return self._tag == 'folder'

    def is_file(self):
        return self._tag == 'file'

    def is_autorename_failed(self):
        return self._tag == 'autorename_failed'

    def is_unknown(self):
        return self._tag == 'unknown'

    @classmethod
    def from_json(self, obj):
        obj = copy.copy(obj)
        assert len(obj) == 1, 'One key must be set, not %d' % len(obj)
        if obj == 'folder':
            return obj
        if obj == 'file':
            return obj
        if obj == 'autorename_failed':
            return obj
        if obj == 'unknown':
            return obj
        return ConflictReason(**obj)

    def to_json(self):
        if self._tag == 'folder':
            return self._tag
        if self._tag == 'file':
            return self._tag
        if self._tag == 'autorename_failed':
            return self._tag
        if self._tag == 'unknown':
            return self._tag

    def __repr__(self):
        return 'ConflictReason(%r)' % self._tag

class ConflictError(object):

    def __init__(self,
                 reason,
                 **kwargs):
        """
        :type reason: :class:`ConflictReason`
        """
        if reason == ConflictReason.Folder:
            self.reason = ConflictReason(folder=True)
        if reason == ConflictReason.File:
            self.reason = ConflictReason(file=True)
        if reason == ConflictReason.AutorenameFailed:
            self.reason = ConflictReason(autorename_failed=True)
        if reason == ConflictReason.Unknown:
            self.reason = ConflictReason(unknown=True)

    @classmethod
    def from_json(cls, obj):
        obj = copy.copy(obj)
        obj['reason'] = ConflictReason.from_json(obj['reason'])
        return ConflictError(**obj)

    def to_json(self):
        d = dict(reason=self.reason.to_json())
        return d

    def __repr__(self):
        return 'ConflictError(%r)' % self.reason

class UploadCommitError(object):

    Conflict = ConflictError
    NoWritePermission = object()
    InsufficientQuota = object()

    def __init__(self,
                 conflict=None,
                 no_write_permission=None,
                 insufficient_quota=None,
                 **kwargs):
        """
        Only one argument can be set.

        :type conflict: :class:`ConflictError`
        :param bool no_write_permission: User does not have permission to write
            in the folder. An example of this is if the folder is a read-only
            shared folder.
        :param bool insufficient_quota: User does not have sufficient space
            quota to save the file.
        """
        assert_only_one(conflict=conflict,
                        no_write_permission=no_write_permission,
                        insufficient_quota=insufficient_quota,
                        **kwargs)
        self.conflict = None
        self.no_write_permission = None
        self.insufficient_quota = None

        if conflict is not None:
            assert isinstance(conflict, ConflictError), 'conflict must be of type ConflictError'
            self.conflict = conflict
            self._tag = 'conflict'

        if no_write_permission is not None:
            assert isinstance(no_write_permission, bool), 'no_write_permission must be of type bool'
            self.no_write_permission = no_write_permission
            self._tag = 'no_write_permission'

        if insufficient_quota is not None:
            assert isinstance(insufficient_quota, bool), 'insufficient_quota must be of type bool'
            self.insufficient_quota = insufficient_quota
            self._tag = 'insufficient_quota'

    def is_conflict(self):
        return self._tag == 'conflict'

    def is_no_write_permission(self):
        return self._tag == 'no_write_permission'

    def is_insufficient_quota(self):
        return self._tag == 'insufficient_quota'

    @classmethod
    def from_json(self, obj):
        obj = copy.copy(obj)
        assert len(obj) == 1, 'One key must be set, not %d' % len(obj)
        if 'conflict' in obj:
            obj['conflict'] = ConflictError.from_json(obj['conflict'])
        if obj == 'no_write_permission':
            return obj
        if obj == 'insufficient_quota':
            return obj
        return UploadCommitError(**obj)

    def to_json(self):
        if self._tag == 'conflict':
            return dict(conflict=self.conflict.to_json())
        if self._tag == 'no_write_permission':
            return self._tag
        if self._tag == 'insufficient_quota':
            return self._tag

    def __repr__(self):
        return 'UploadCommitError(%r)' % self._tag

class BaseFiles(Namespace):
    """Methods for routes in the files namespace"""

    def download(self,
                 path,
                 rev=None):
        """
        Download a file in a user's Dropbox.

        :param str path: Path from root. Should be an empty string for root.
        :param str rev: Revision of target file.
        :rtype: :class:`FileInfo`, :class:`requests.models.Response`
        :raises: :class:`dropbox.exceptions.ApiError`

        Error codes:
            disallowed
            no_file
        """
        o = FileTarget(path,
                       rev).to_json()
        r = self._dropbox.request(Dropbox.Host.API_CONTENT,
                                  'files/download',
                                  Dropbox.RouteStyle.DOWNLOAD,
                                  o,
                                  None)
        return (FileInfo.from_json(r.obj_segment),
                r.binary_segment)

    def download_to_file(self,
                         download_path,
                         path,
                         rev=None):
        """
        Download a file in a user's Dropbox.

        :param str download_path: Path on local machine to save file.
        :param str path: Path from root. Should be an empty string for root.
        :param str rev: Revision of target file.
        :rtype: :class:`FileInfo`
        :raises: :class:`dropbox.exceptions.ApiError`

        Error codes:
            disallowed
            no_file
        """
        o = FileTarget(path,
                       rev).to_json()
        r = self._dropbox.request(Dropbox.Host.API_CONTENT,
                                  'files/download',
                                  Dropbox.RouteStyle.DOWNLOAD,
                                  o,
                                  None)
        with open(download_path, 'w') as f:
            for c in r.binary_segment.iter_content(2**16):
                f.write(c)
        return FileInfo.from_json(r.obj_segment)

    def upload_start(self,
                     f):
        """
        Start an upload session.

        :param f: A string or file-like obj of data.
        :rtype: :class:`UploadSessionStart`
        """
        o = Empty().to_json()
        r = self._dropbox.request(Dropbox.Host.API_CONTENT,
                                  'files/upload/start',
                                  Dropbox.RouteStyle.UPLOAD,
                                  o,
                                  f)
        return UploadSessionStart.from_json(r.obj_segment)

    def upload_append(self,
                      f,
                      upload_id,
                      offset):
        """
        Start an upload session.

        :param f: A string or file-like obj of data.
        :param str upload_id: Identifies the upload session to append data to.
        :param long offset: The offset into the file of the current chunk of
            data being uploaded. It can also be thought of as the amount of data
            that has been uploaded so far. We use the offset as a sanity check.
        :rtype: :class:`Empty`
        """
        o = UploadAppend(upload_id,
                         offset).to_json()
        r = self._dropbox.request(Dropbox.Host.API_CONTENT,
                                  'files/upload/append',
                                  Dropbox.RouteStyle.UPLOAD,
                                  o,
                                  f)
        return Empty.from_json(r.obj_segment)

    def upload(self,
               f,
               path,
               mode,
               append_to=None,
               autorename=False,
               client_modified_utc=None,
               mute=False):
        """
        Use this endpoint to either finish an ongoing upload session that was
        begun with :meth:`upload_start` or upload a file in one shot.

        :param f: A string or file-like obj of data.
        :param str path: Path in the user's Dropbox to save the file.
        :param mode: The course of action to take if a file already exists at
            ``path``.
        :type mode: :class:`ConflictPolicy`
        :param append_to: If specified, the current chunk of data should be
            appended to an existing upload session.
        :type append_to: :class:`UploadAppend`
        :param bool autorename: Whether the file should be autorenamed in the
            event of a conflict.
        :param long client_modified_utc: Self reported time of when this file
            was created or modified.
        :param bool mute: Whether the devices that the user has linked should
            notify them of the new or updated file.
        :rtype: :class:`FileInfo`
        :raises: :class:`dropbox.exceptions.ApiError`

        Error codes:
            conflict
            no_write_permission: User does not have permission to write in the
                folder. An example of this is if the folder is a read-only
                shared folder.
            insufficient_quota: User does not have sufficient space quota to
                save the file.
        """
        o = UploadCommit(path,
                         mode,
                         append_to,
                         autorename,
                         client_modified_utc,
                         mute).to_json()
        r = self._dropbox.request(Dropbox.Host.API_CONTENT,
                                  'files/upload',
                                  Dropbox.RouteStyle.UPLOAD,
                                  o,
                                  f)
        return FileInfo.from_json(r.obj_segment)

