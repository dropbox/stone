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

class PathTarget(object):

    __slots__ = [
        '_path',
        '__has_path',
    ]

    __path_data_type = dt.String(pattern=None)

    _field_names_ = {
        'path',
    }

    _fields_ = [
        ('path', False, __path_data_type),
    ]

    def __init__(self):
        self._path = None
        self.__has_path = False

    @property
    def path(self):
        """
        Path from root. Should be an empty string for root.
        :rtype: str
        """
        if self.__has_path:
            return self._path
        else:
            raise KeyError("missing required field 'path'")

    @path.setter
    def path(self, val):
        self.__path_data_type.validate(val)
        self._path = val
        self.__has_path = True

    @path.deleter
    def path(self):
        self._path = None
        self.__has_path = False

    def __repr__(self):
        return 'PathTarget(path=%r)' % self._path

class FileTarget(PathTarget):

    __slots__ = [
        '_rev',
        '__has_rev',
    ]

    __rev_data_type = dt.String(pattern=None)

    _field_names_ = PathTarget._field_names_.union({
        'rev',
    })

    _fields_ = PathTarget._fields_ + [
        ('rev', True, __rev_data_type),
    ]

    def __init__(self):
        super(FileTarget, self).__init__()
        self._rev = None
        self.__has_rev = False

    @property
    def rev(self):
        """
        Revision of target file.
        :rtype: str
        """
        if self.__has_rev:
            return self._rev
        else:
            return None

    @rev.setter
    def rev(self, val):
        if val is None:
            del self.rev
            return
        self.__rev_data_type.validate(val)
        self._rev = val
        self.__has_rev = True

    @rev.deleter
    def rev(self):
        self._rev = None
        self.__has_rev = False

    def __repr__(self):
        return 'FileTarget(path=%r)' % self._path

class FileInfo(object):

    __slots__ = [
        '_name',
        '__has_name',
    ]

    __name_data_type = dt.String(pattern=None)

    _field_names_ = {
        'name',
    }

    _fields_ = [
        ('name', False, __name_data_type),
    ]

    def __init__(self):
        self._name = None
        self.__has_name = False

    @property
    def name(self):
        """
        Name of file.
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
    def name(self):
        self._name = None
        self.__has_name = False

    def __repr__(self):
        return 'FileInfo(name=%r)' % self._name

class SubError(object):

    __slots__ = [
        '_reason',
        '__has_reason',
    ]

    __reason_data_type = dt.String(pattern=None)

    _field_names_ = {
        'reason',
    }

    _fields_ = [
        ('reason', False, __reason_data_type),
    ]

    def __init__(self):
        self._reason = None
        self.__has_reason = False

    @property
    def reason(self):
        """
        A code indicating the type of error.
        :rtype: str
        """
        if self.__has_reason:
            return self._reason
        else:
            raise KeyError("missing required field 'reason'")

    @reason.setter
    def reason(self, val):
        self.__reason_data_type.validate(val)
        self._reason = val
        self.__has_reason = True

    @reason.deleter
    def reason(self):
        self._reason = None
        self.__has_reason = False

    def __repr__(self):
        return 'SubError(reason=%r)' % self._reason

class DownloadError(object):

    _field_names_ = {
        'disallowed',
        'no_file',
        'unknown',
    }

    _fields_ = {
        'disallowed': SubError,
        'no_file': SubError,
        'unknown': None,
    }

    def __init__(self):
        self._disallowed = None
        self._no_file = None
        self._tag = None

    @classmethod
    def create_and_set_unknown(cls):
        """
        :rtype: DownloadError
        """
        c = cls()
        c.set_unknown()
        return c

    def is_disallowed(self):
        return self._tag == 'disallowed'

    def is_no_file(self):
        return self._tag == 'no_file'

    def is_unknown(self):
        return self._tag == 'unknown'

    @property
    def disallowed(self):
        if not self.is_disallowed():
            raise KeyError("tag 'disallowed' not set")
        return self._disallowed

    @disallowed.setter
    def disallowed(self, val):
        self.__disallowed_data_type.validate_type_only(val)
        self._disallowed = val
        self._tag = 'disallowed'

    @property
    def no_file(self):
        if not self.is_no_file():
            raise KeyError("tag 'no_file' not set")
        return self._no_file

    @no_file.setter
    def no_file(self, val):
        self.__no_file_data_type.validate_type_only(val)
        self._no_file = val
        self._tag = 'no_file'

    def set_unknown(self):
        self._tag = 'unknown'

    def __repr__(self):
        return 'DownloadError(%r)' % self._tag

class UploadSessionStart(object):

    __slots__ = [
        '_upload_id',
        '__has_upload_id',
    ]

    __upload_id_data_type = dt.String(pattern=None)

    _field_names_ = {
        'upload_id',
    }

    _fields_ = [
        ('upload_id', False, __upload_id_data_type),
    ]

    def __init__(self):
        self._upload_id = None
        self.__has_upload_id = False

    @property
    def upload_id(self):
        """
        A unique identifier for the upload session.
        :rtype: str
        """
        if self.__has_upload_id:
            return self._upload_id
        else:
            raise KeyError("missing required field 'upload_id'")

    @upload_id.setter
    def upload_id(self, val):
        self.__upload_id_data_type.validate(val)
        self._upload_id = val
        self.__has_upload_id = True

    @upload_id.deleter
    def upload_id(self):
        self._upload_id = None
        self.__has_upload_id = False

    def __repr__(self):
        return 'UploadSessionStart(upload_id=%r)' % self._upload_id

class UploadAppend(object):

    __slots__ = [
        '_upload_id',
        '__has_upload_id',
        '_offset',
        '__has_offset',
    ]

    __upload_id_data_type = dt.String(pattern=None)
    __offset_data_type = dt.UInt64()

    _field_names_ = {
        'upload_id',
        'offset',
    }

    _fields_ = [
        ('upload_id', False, __upload_id_data_type),
        ('offset', False, __offset_data_type),
    ]

    def __init__(self):
        self._upload_id = None
        self.__has_upload_id = False
        self._offset = None
        self.__has_offset = False

    @property
    def upload_id(self):
        """
        Identifies the upload session to append data to.
        :rtype: str
        """
        if self.__has_upload_id:
            return self._upload_id
        else:
            raise KeyError("missing required field 'upload_id'")

    @upload_id.setter
    def upload_id(self, val):
        self.__upload_id_data_type.validate(val)
        self._upload_id = val
        self.__has_upload_id = True

    @upload_id.deleter
    def upload_id(self):
        self._upload_id = None
        self.__has_upload_id = False

    @property
    def offset(self):
        """
        The offset into the file of the current chunk of data being uploaded. It
        can also be thought of as the amount of data that has been uploaded so
        far. We use the offset as a sanity check.
        :rtype: long
        """
        if self.__has_offset:
            return self._offset
        else:
            raise KeyError("missing required field 'offset'")

    @offset.setter
    def offset(self, val):
        self.__offset_data_type.validate(val)
        self._offset = val
        self.__has_offset = True

    @offset.deleter
    def offset(self):
        self._offset = None
        self.__has_offset = False

    def __repr__(self):
        return 'UploadAppend(upload_id=%r)' % self._upload_id

class IncorrectOffsetError(object):

    __slots__ = [
        '_correct_offset',
        '__has_correct_offset',
    ]

    __correct_offset_data_type = dt.UInt64()

    _field_names_ = {
        'correct_offset',
    }

    _fields_ = [
        ('correct_offset', False, __correct_offset_data_type),
    ]

    def __init__(self):
        self._correct_offset = None
        self.__has_correct_offset = False

    @property
    def correct_offset(self):
        """
        :rtype: long
        """
        if self.__has_correct_offset:
            return self._correct_offset
        else:
            raise KeyError("missing required field 'correct_offset'")

    @correct_offset.setter
    def correct_offset(self, val):
        self.__correct_offset_data_type.validate(val)
        self._correct_offset = val
        self.__has_correct_offset = True

    @correct_offset.deleter
    def correct_offset(self):
        self._correct_offset = None
        self.__has_correct_offset = False

    def __repr__(self):
        return 'IncorrectOffsetError(correct_offset=%r)' % self._correct_offset

class UploadAppendError(object):

    _field_names_ = {
        'not_found',
        'closed',
        'incorrect_offset',
    }

    _fields_ = {
        'not_found': None,
        'closed': None,
        'incorrect_offset': IncorrectOffsetError,
    }

    def __init__(self):
        self._incorrect_offset = None
        self._tag = None

    @classmethod
    def create_and_set_not_found(cls):
        """
        :rtype: UploadAppendError
        """
        c = cls()
        c.set_not_found()
        return c

    @classmethod
    def create_and_set_closed(cls):
        """
        :rtype: UploadAppendError
        """
        c = cls()
        c.set_closed()
        return c

    def is_not_found(self):
        return self._tag == 'not_found'

    def is_closed(self):
        return self._tag == 'closed'

    def is_incorrect_offset(self):
        return self._tag == 'incorrect_offset'

    def set_not_found(self):
        self._tag = 'not_found'

    def set_closed(self):
        self._tag = 'closed'

    @property
    def incorrect_offset(self):
        if not self.is_incorrect_offset():
            raise KeyError("tag 'incorrect_offset' not set")
        return self._incorrect_offset

    @incorrect_offset.setter
    def incorrect_offset(self, val):
        self.__incorrect_offset_data_type.validate_type_only(val)
        self._incorrect_offset = val
        self._tag = 'incorrect_offset'

    def __repr__(self):
        return 'UploadAppendError(%r)' % self._tag

class UpdateParentRev(object):

    __slots__ = [
        '_parent_rev',
        '__has_parent_rev',
    ]

    __parent_rev_data_type = dt.String(pattern=None)

    _field_names_ = {
        'parent_rev',
    }

    _fields_ = [
        ('parent_rev', False, __parent_rev_data_type),
    ]

    def __init__(self):
        self._parent_rev = None
        self.__has_parent_rev = False

    @property
    def parent_rev(self):
        """
        :rtype: str
        """
        if self.__has_parent_rev:
            return self._parent_rev
        else:
            raise KeyError("missing required field 'parent_rev'")

    @parent_rev.setter
    def parent_rev(self, val):
        self.__parent_rev_data_type.validate(val)
        self._parent_rev = val
        self.__has_parent_rev = True

    @parent_rev.deleter
    def parent_rev(self):
        self._parent_rev = None
        self.__has_parent_rev = False

    def __repr__(self):
        return 'UpdateParentRev(parent_rev=%r)' % self._parent_rev

class ConflictPolicy(object):
    """
    The action to take when a file path conflict exists.

    :ivar Add: On a conflict, the upload is rejected. You can call the Upload
        endpoint again and try a different path.
    :ivar Overwrite: On a conflict, the target is overridden.
    :ivar Update: On a conflict, only overwrite the target if the parent_rev
        matches.
    """

    _field_names_ = {
        'add',
        'overwrite',
        'update',
    }

    _fields_ = {
        'add': None,
        'overwrite': None,
        'update': UpdateParentRev,
    }

    def __init__(self):
        self._update = None
        self._tag = None

    @classmethod
    def create_and_set_add(cls):
        """
        :rtype: ConflictPolicy
        """
        c = cls()
        c.set_add()
        return c

    @classmethod
    def create_and_set_overwrite(cls):
        """
        :rtype: ConflictPolicy
        """
        c = cls()
        c.set_overwrite()
        return c

    def is_add(self):
        return self._tag == 'add'

    def is_overwrite(self):
        return self._tag == 'overwrite'

    def is_update(self):
        return self._tag == 'update'

    def set_add(self):
        self._tag = 'add'

    def set_overwrite(self):
        self._tag = 'overwrite'

    @property
    def update(self):
        if not self.is_update():
            raise KeyError("tag 'update' not set")
        return self._update

    @update.setter
    def update(self, val):
        self.__update_data_type.validate_type_only(val)
        self._update = val
        self._tag = 'update'

    def __repr__(self):
        return 'ConflictPolicy(%r)' % self._tag

class UploadCommit(object):

    __slots__ = [
        '_path',
        '__has_path',
        '_mode',
        '__has_mode',
        '_append_to',
        '__has_append_to',
        '_autorename',
        '__has_autorename',
        '_client_modified_utc',
        '__has_client_modified_utc',
        '_mute',
        '__has_mute',
    ]

    __path_data_type = dt.String(pattern=None)
    __mode_data_type = dt.Union(ConflictPolicy)
    __append_to_data_type = dt.Struct(UploadAppend)
    __autorename_data_type = dt.Boolean()
    __client_modified_utc_data_type = dt.UInt64()
    __mute_data_type = dt.Boolean()

    _field_names_ = {
        'path',
        'mode',
        'append_to',
        'autorename',
        'client_modified_utc',
        'mute',
    }

    _fields_ = [
        ('path', False, __path_data_type),
        ('mode', False, __mode_data_type),
        ('append_to', True, __append_to_data_type),
        ('autorename', True, __autorename_data_type),
        ('client_modified_utc', True, __client_modified_utc_data_type),
        ('mute', True, __mute_data_type),
    ]

    def __init__(self):
        self._path = None
        self.__has_path = False
        self._mode = None
        self.__has_mode = False
        self._append_to = None
        self.__has_append_to = False
        self._autorename = None
        self.__has_autorename = False
        self._client_modified_utc = None
        self.__has_client_modified_utc = False
        self._mute = None
        self.__has_mute = False

    @property
    def path(self):
        """
        Path in the user's Dropbox to save the file.
        :rtype: str
        """
        if self.__has_path:
            return self._path
        else:
            raise KeyError("missing required field 'path'")

    @path.setter
    def path(self, val):
        self.__path_data_type.validate(val)
        self._path = val
        self.__has_path = True

    @path.deleter
    def path(self):
        self._path = None
        self.__has_path = False

    @property
    def mode(self):
        """
        The course of action to take if a file already exists at ``path``.
        :rtype: ConflictPolicy
        """
        if self.__has_mode:
            return self._mode
        else:
            raise KeyError("missing required field 'mode'")

    @mode.setter
    def mode(self, val):
        self.__mode_data_type.validate_type_only(val)
        self._mode = val
        self.__has_mode = True

    @mode.deleter
    def mode(self):
        self._mode = None
        self.__has_mode = False

    @property
    def append_to(self):
        """
        If specified, the current chunk of data should be appended to an
        existing upload session.
        :rtype: UploadAppend
        """
        if self.__has_append_to:
            return self._append_to
        else:
            return None

    @append_to.setter
    def append_to(self, val):
        if val is None:
            del self.append_to
            return
        self.__append_to_data_type.validate_type_only(val)
        self._append_to = val
        self.__has_append_to = True

    @append_to.deleter
    def append_to(self):
        self._append_to = None
        self.__has_append_to = False

    @property
    def autorename(self):
        """
        :rtype: bool
        """
        if self.__has_autorename:
            return self._autorename
        else:
            False

    @autorename.setter
    def autorename(self, val):
        if val is None:
            del self.autorename
            return
        self.__autorename_data_type.validate(val)
        self._autorename = val
        self.__has_autorename = True

    @autorename.deleter
    def autorename(self):
        self._autorename = None
        self.__has_autorename = False

    @property
    def client_modified_utc(self):
        """
        :rtype: long
        """
        if self.__has_client_modified_utc:
            return self._client_modified_utc
        else:
            None

    @client_modified_utc.setter
    def client_modified_utc(self, val):
        if val is None:
            del self.client_modified_utc
            return
        self.__client_modified_utc_data_type.validate(val)
        self._client_modified_utc = val
        self.__has_client_modified_utc = True

    @client_modified_utc.deleter
    def client_modified_utc(self):
        self._client_modified_utc = None
        self.__has_client_modified_utc = False

    @property
    def mute(self):
        """
        :rtype: bool
        """
        if self.__has_mute:
            return self._mute
        else:
            False

    @mute.setter
    def mute(self, val):
        if val is None:
            del self.mute
            return
        self.__mute_data_type.validate(val)
        self._mute = val
        self.__has_mute = True

    @mute.deleter
    def mute(self):
        self._mute = None
        self.__has_mute = False

    def __repr__(self):
        return 'UploadCommit(path=%r)' % self._path

class ConflictReason(object):

    _field_names_ = {
        'folder',
        'file',
        'autorename_failed',
    }

    _fields_ = {
        'folder': None,
        'file': None,
        'autorename_failed': None,
    }

    def __init__(self):
        self._tag = None

    @classmethod
    def create_and_set_folder(cls):
        """
        :rtype: ConflictReason
        """
        c = cls()
        c.set_folder()
        return c

    @classmethod
    def create_and_set_file(cls):
        """
        :rtype: ConflictReason
        """
        c = cls()
        c.set_file()
        return c

    @classmethod
    def create_and_set_autorename_failed(cls):
        """
        :rtype: ConflictReason
        """
        c = cls()
        c.set_autorename_failed()
        return c

    def is_folder(self):
        return self._tag == 'folder'

    def is_file(self):
        return self._tag == 'file'

    def is_autorename_failed(self):
        return self._tag == 'autorename_failed'

    def set_folder(self):
        self._tag = 'folder'

    def set_file(self):
        self._tag = 'file'

    def set_autorename_failed(self):
        self._tag = 'autorename_failed'

    def __repr__(self):
        return 'ConflictReason(%r)' % self._tag

class ConflictError(object):

    __slots__ = [
        '_reason',
        '__has_reason',
    ]

    __reason_data_type = dt.Union(ConflictReason)

    _field_names_ = {
        'reason',
    }

    _fields_ = [
        ('reason', False, __reason_data_type),
    ]

    def __init__(self):
        self._reason = None
        self.__has_reason = False

    @property
    def reason(self):
        """
        :rtype: ConflictReason
        """
        if self.__has_reason:
            return self._reason
        else:
            raise KeyError("missing required field 'reason'")

    @reason.setter
    def reason(self, val):
        self.__reason_data_type.validate_type_only(val)
        self._reason = val
        self.__has_reason = True

    @reason.deleter
    def reason(self):
        self._reason = None
        self.__has_reason = False

    def __repr__(self):
        return 'ConflictError(reason=%r)' % self._reason

class UploadCommitError(object):

    _field_names_ = {
        'conflict',
        'no_write_permission',
        'insufficient_quota',
    }

    _fields_ = {
        'conflict': ConflictError,
        'no_write_permission': None,
        'insufficient_quota': None,
    }

    def __init__(self):
        self._conflict = None
        self._tag = None

    @classmethod
    def create_and_set_no_write_permission(cls):
        """
        :rtype: UploadCommitError
        """
        c = cls()
        c.set_no_write_permission()
        return c

    @classmethod
    def create_and_set_insufficient_quota(cls):
        """
        :rtype: UploadCommitError
        """
        c = cls()
        c.set_insufficient_quota()
        return c

    def is_conflict(self):
        return self._tag == 'conflict'

    def is_no_write_permission(self):
        return self._tag == 'no_write_permission'

    def is_insufficient_quota(self):
        return self._tag == 'insufficient_quota'

    @property
    def conflict(self):
        if not self.is_conflict():
            raise KeyError("tag 'conflict' not set")
        return self._conflict

    @conflict.setter
    def conflict(self, val):
        self.__conflict_data_type.validate_type_only(val)
        self._conflict = val
        self._tag = 'conflict'

    def set_no_write_permission(self):
        self._tag = 'no_write_permission'

    def set_insufficient_quota(self):
        self._tag = 'insufficient_quota'

    def __repr__(self):
        return 'UploadCommitError(%r)' % self._tag

class File(object):
    """
    A file resource

    :ivar client_modified: For files, this is the modification time set by the
        desktop client when the file was added to Dropbox. Since this time is
        not verified (the Dropbox server stores whatever the desktop client
        sends up), this should only be used for display purposes (such as
        sorting) and not, for example, to determine if a file has changed or
        not.
    :ivar server_modified: The last time the file was modified on Dropbox.
    :ivar rev: A unique identifier for the current revision of a file. This
        field is the same rev as elsewhere in the API and can be used to detect
        changes and avoid conflicts.
    :ivar size: The file size in bytes.
    """

    __slots__ = [
        '_client_modified',
        '__has_client_modified',
        '_server_modified',
        '__has_server_modified',
        '_rev',
        '__has_rev',
        '_size',
        '__has_size',
    ]

    __client_modified_data_type = dt.Timestamp(format='%a, %d %b %Y %H:%M:%S +0000')
    __server_modified_data_type = dt.Timestamp(format='%a, %d %b %Y %H:%M:%S +0000')
    __rev_data_type = dt.String(pattern=None)
    __size_data_type = dt.UInt64()

    _field_names_ = {
        'client_modified',
        'server_modified',
        'rev',
        'size',
    }

    _fields_ = [
        ('client_modified', False, __client_modified_data_type),
        ('server_modified', False, __server_modified_data_type),
        ('rev', False, __rev_data_type),
        ('size', False, __size_data_type),
    ]

    def __init__(self):
        self._client_modified = None
        self.__has_client_modified = False
        self._server_modified = None
        self.__has_server_modified = False
        self._rev = None
        self.__has_rev = False
        self._size = None
        self.__has_size = False

    @property
    def client_modified(self):
        """
        For files, this is the modification time set by the desktop client when
        the file was added to Dropbox. Since this time is not verified (the
        Dropbox server stores whatever the desktop client sends up), this should
        only be used for display purposes (such as sorting) and not, for
        example, to determine if a file has changed or not.
        :rtype: datetime.datetime
        """
        if self.__has_client_modified:
            return self._client_modified
        else:
            raise KeyError("missing required field 'client_modified'")

    @client_modified.setter
    def client_modified(self, val):
        self.__client_modified_data_type.validate(val)
        self._client_modified = val
        self.__has_client_modified = True

    @client_modified.deleter
    def client_modified(self):
        self._client_modified = None
        self.__has_client_modified = False

    @property
    def server_modified(self):
        """
        The last time the file was modified on Dropbox.
        :rtype: datetime.datetime
        """
        if self.__has_server_modified:
            return self._server_modified
        else:
            raise KeyError("missing required field 'server_modified'")

    @server_modified.setter
    def server_modified(self, val):
        self.__server_modified_data_type.validate(val)
        self._server_modified = val
        self.__has_server_modified = True

    @server_modified.deleter
    def server_modified(self):
        self._server_modified = None
        self.__has_server_modified = False

    @property
    def rev(self):
        """
        A unique identifier for the current revision of a file. This field is
        the same rev as elsewhere in the API and can be used to detect changes
        and avoid conflicts.
        :rtype: str
        """
        if self.__has_rev:
            return self._rev
        else:
            raise KeyError("missing required field 'rev'")

    @rev.setter
    def rev(self, val):
        self.__rev_data_type.validate(val)
        self._rev = val
        self.__has_rev = True

    @rev.deleter
    def rev(self):
        self._rev = None
        self.__has_rev = False

    @property
    def size(self):
        """
        The file size in bytes.
        :rtype: long
        """
        if self.__has_size:
            return self._size
        else:
            raise KeyError("missing required field 'size'")

    @size.setter
    def size(self, val):
        self.__size_data_type.validate(val)
        self._size = val
        self.__has_size = True

    @size.deleter
    def size(self):
        self._size = None
        self.__has_size = False

    def __repr__(self):
        return 'File(client_modified=%r)' % self._client_modified

class Folder(object):
    """
    A folder resource

    """

    __slots__ = [
    ]

    _field_names_ = {
    }

    _fields_ = [
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return 'Folder()'

class Metadata(object):

    _field_names_ = {
        'file',
        'folder',
    }

    _fields_ = {
        'file': File,
        'folder': Folder,
    }

    def __init__(self):
        self._file = None
        self._folder = None
        self._tag = None

    def is_file(self):
        return self._tag == 'file'

    def is_folder(self):
        return self._tag == 'folder'

    @property
    def file(self):
        if not self.is_file():
            raise KeyError("tag 'file' not set")
        return self._file

    @file.setter
    def file(self, val):
        self.__file_data_type.validate_type_only(val)
        self._file = val
        self._tag = 'file'

    @property
    def folder(self):
        if not self.is_folder():
            raise KeyError("tag 'folder' not set")
        return self._folder

    @folder.setter
    def folder(self, val):
        self.__folder_data_type.validate_type_only(val)
        self._folder = val
        self._tag = 'folder'

    def __repr__(self):
        return 'Metadata(%r)' % self._tag

class Entry(object):

    __slots__ = [
        '_metadata',
        '__has_metadata',
        '_name',
        '__has_name',
    ]

    __metadata_data_type = dt.Union(Metadata)
    __name_data_type = dt.String(pattern=None)

    _field_names_ = {
        'metadata',
        'name',
    }

    _fields_ = [
        ('metadata', False, __metadata_data_type),
        ('name', False, __name_data_type),
    ]

    def __init__(self):
        self._metadata = None
        self.__has_metadata = False
        self._name = None
        self.__has_name = False

    @property
    def metadata(self):
        """
        :rtype: Metadata
        """
        if self.__has_metadata:
            return self._metadata
        else:
            raise KeyError("missing required field 'metadata'")

    @metadata.setter
    def metadata(self, val):
        self.__metadata_data_type.validate_type_only(val)
        self._metadata = val
        self.__has_metadata = True

    @metadata.deleter
    def metadata(self):
        self._metadata = None
        self.__has_metadata = False

    @property
    def name(self):
        """
        The name of the resource as seen by the user in their Dropbox.
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
    def name(self):
        self._name = None
        self.__has_name = False

    def __repr__(self):
        return 'Entry(metadata=%r)' % self._metadata

class ListFolderResponse(object):

    __slots__ = [
        '_cursor',
        '__has_cursor',
        '_has_more',
        '__has_has_more',
        '_entries',
        '__has_entries',
    ]

    __cursor_data_type = dt.String(pattern=None)
    __has_more_data_type = dt.Boolean()
    __entries_data_type = dt.List(data_type=Entry)

    _field_names_ = {
        'cursor',
        'has_more',
        'entries',
    }

    _fields_ = [
        ('cursor', False, __cursor_data_type),
        ('has_more', False, __has_more_data_type),
        ('entries', False, __entries_data_type),
    ]

    def __init__(self):
        self._cursor = None
        self.__has_cursor = False
        self._has_more = None
        self.__has_has_more = False
        self._entries = None
        self.__has_entries = False

    @property
    def cursor(self):
        """
        Pass the cursor into ListFolderContinue to see what's changed in the
        folder since your previous query.
        :rtype: str
        """
        if self.__has_cursor:
            return self._cursor
        else:
            raise KeyError("missing required field 'cursor'")

    @cursor.setter
    def cursor(self, val):
        self.__cursor_data_type.validate(val)
        self._cursor = val
        self.__has_cursor = True

    @cursor.deleter
    def cursor(self):
        self._cursor = None
        self.__has_cursor = False

    @property
    def has_more(self):
        """
        If true, then there are more entries available.
        :rtype: bool
        """
        if self.__has_has_more:
            return self._has_more
        else:
            raise KeyError("missing required field 'has_more'")

    @has_more.setter
    def has_more(self, val):
        self.__has_more_data_type.validate(val)
        self._has_more = val
        self.__has_has_more = True

    @has_more.deleter
    def has_more(self):
        self._has_more = None
        self.__has_has_more = False

    @property
    def entries(self):
        """
        Each entry is a resource in the folder.
        :rtype: list of [Entry]
        """
        if self.__has_entries:
            return self._entries
        else:
            raise KeyError("missing required field 'entries'")

    @entries.setter
    def entries(self, val):
        self.__entries_data_type.validate(val)
        self._entries = val
        self.__has_entries = True

    @entries.deleter
    def entries(self):
        self._entries = None
        self.__has_entries = False

    def __repr__(self):
        return 'ListFolderResponse(cursor=%r)' % self._cursor

