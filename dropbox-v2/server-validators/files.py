import copy
import datetime
import numbers
import six

import babel_data_types as dt

class Empty(object):

    __fields = {
    }

    def __init__(self):
        pass

    def validate(self):
        return all([
        ])

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        empty = Empty()
        return empty

    def to_dict(self, transformer):
        d = dict()
        return d

    def __repr__(self):
        return 'Empty()'

class PathTarget(object):

    __path_data_type = dt.String(pattern=None)

    __fields = {
        'path',
    }

    def __init__(self):
        self._path = None
        self.__has_path = False

    def validate(self):
        return all([
            self.__has_path,
        ])

    @property
    def path(self):
        """
        Path from root. Should be an empty string for root.
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
    def path(self, val):
        self._path = None
        self.__has_path = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        path_target = PathTarget()
        if 'path' not in obj:
            raise KeyError("missing required field 'path'")
        path_target.path = transformer.convert_from(path_target.__path_data_type, obj['path'])
        return path_target

    def to_dict(self, transformer):
        d = dict(path=transformer.convert_to(self.__path_data_type, self._path))
        return d

    def __repr__(self):
        return 'PathTarget(%r)' % self._path

class FileTarget(PathTarget):

    __rev_data_type = dt.String(pattern=None)

    __fields = {
        'path',
        'rev',
    }

    def __init__(self):
        super(FileTarget, self).__init__()
        self._rev = None
        self.__has_rev = False

    def validate(self):
        return all([
            self.__has_path,
        ])

    @property
    def rev(self):
        """
        Revision of target file.
        """
        if self.__has_rev:
            return self._rev
        else:
            return None

    @rev.setter
    def rev(self, val):
        self.__rev_data_type.validate(val)
        self._rev = val
        self.__has_rev = True

    @rev.deleter
    def rev(self, val):
        self._rev = None
        self.__has_rev = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        file_target = FileTarget()
        if 'path' not in obj:
            raise KeyError("missing required field 'path'")
        file_target.path = transformer.convert_from(file_target.__path_data_type, obj['path'])
        file_target.rev = transformer.convert_from(file_target.__rev_data_type, obj.get('rev'))
        return file_target

    def to_dict(self, transformer):
        d = dict(path=transformer.convert_to(self.__path_data_type, self._path))
        if self._rev is not None:
            d['rev'] = transformer.convert_to(self.__rev_data_type, self._rev)
        return d

    def __repr__(self):
        return 'FileTarget(%r)' % self._rev

class FileInfo(object):

    __name_data_type = dt.String(pattern=None)

    __fields = {
        'name',
    }

    def __init__(self):
        self._name = None
        self.__has_name = False

    def validate(self):
        return all([
            self.__has_name,
        ])

    @property
    def name(self):
        """
        Name of file.
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
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        file_info = FileInfo()
        if 'name' not in obj:
            raise KeyError("missing required field 'name'")
        file_info.name = transformer.convert_from(file_info.__name_data_type, obj['name'])
        return file_info

    def to_dict(self, transformer):
        d = dict(name=transformer.convert_to(self.__name_data_type, self._name))
        return d

    def __repr__(self):
        return 'FileInfo(%r)' % self._name

class SubError(object):

    __reason_data_type = dt.String(pattern=None)

    __fields = {
        'reason',
    }

    def __init__(self):
        self._reason = None
        self.__has_reason = False

    def validate(self):
        return all([
            self.__has_reason,
        ])

    @property
    def reason(self):
        """
        A code indicating the type of error.
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
    def reason(self, val):
        self._reason = None
        self.__has_reason = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        sub_error = SubError()
        if 'reason' not in obj:
            raise KeyError("missing required field 'reason'")
        sub_error.reason = transformer.convert_from(sub_error.__reason_data_type, obj['reason'])
        return sub_error

    def to_dict(self, transformer):
        d = dict(reason=transformer.convert_to(self.__reason_data_type, self._reason))
        return d

    def __repr__(self):
        return 'SubError(%r)' % self._reason

class DownloadError(object):

    Disallowed = SubError
    NoFile = SubError

    def __init__(self):
        self._disallowed = None
        self._no_file = None
        self.__tag = None

    def validate(self):
        return self.__tag is not None

    def is_disallowed(self):
        return self.__tag == 'disallowed'

    def is_no_file(self):
        return self.__tag == 'no_file'

    @property
    def disallowed(self):
        if not self.is_disallowed():
            raise KeyError("tag 'disallowed' not set")
        return self._disallowed

    @disallowed.setter
    def disallowed(self, val):
        if not isinstance(val, SubError):
            raise TypeError('disallowed is of type %r but must be of type SubError' % type(val).__name__)
        val.validate()
        self._disallowed = val
        self.__tag = 'disallowed'

    @property
    def no_file(self):
        if not self.is_no_file():
            raise KeyError("tag 'no_file' not set")
        return self._no_file

    @no_file.setter
    def no_file(self, val):
        if not isinstance(val, SubError):
            raise TypeError('no_file is of type %r but must be of type SubError' % type(val).__name__)
        val.validate()
        self._no_file = val
        self.__tag = 'no_file'

    @classmethod
    def from_dict(cls, transformer, obj):
        download_error = cls()
        if isinstance(obj, dict) and len(obj) != 1:
            raise KeyError("Union can only have one key set not %d" % len(obj))
        if isinstance(obj, dict) and 'disallowed' == obj.keys()[0]:
            download_error.disallowed = SubError.from_dict(transformer, obj['disallowed'])
        if isinstance(obj, dict) and 'no_file' == obj.keys()[0]:
            download_error.no_file = SubError.from_dict(transformer, obj['no_file'])
        return download_error

    def to_dict(self, transformer):
        if self.is_disallowed():
            return dict(disallowed=self.disallowed.to_dict(transformer))
        if self.is_no_file():
            return dict(no_file=self.no_file.to_dict(transformer))

    def __repr__(self):
        return 'DownloadError(%r)' % self.__tag

class UploadSessionStart(object):

    __upload_id_data_type = dt.String(pattern=None)

    __fields = {
        'upload_id',
    }

    def __init__(self):
        self._upload_id = None
        self.__has_upload_id = False

    def validate(self):
        return all([
            self.__has_upload_id,
        ])

    @property
    def upload_id(self):
        """
        A unique identifier for the upload session.
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
    def upload_id(self, val):
        self._upload_id = None
        self.__has_upload_id = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        upload_session_start = UploadSessionStart()
        if 'upload_id' not in obj:
            raise KeyError("missing required field 'upload_id'")
        upload_session_start.upload_id = transformer.convert_from(upload_session_start.__upload_id_data_type, obj['upload_id'])
        return upload_session_start

    def to_dict(self, transformer):
        d = dict(upload_id=transformer.convert_to(self.__upload_id_data_type, self._upload_id))
        return d

    def __repr__(self):
        return 'UploadSessionStart(%r)' % self._upload_id

class UploadAppend(object):

    __upload_id_data_type = dt.String(pattern=None)
    __offset_data_type = dt.UInt64()

    __fields = {
        'upload_id',
        'offset',
    }

    def __init__(self):
        self._upload_id = None
        self.__has_upload_id = False
        self._offset = None
        self.__has_offset = False

    def validate(self):
        return all([
            self.__has_upload_id,
            self.__has_offset,
        ])

    @property
    def upload_id(self):
        """
        Identifies the upload session to append data to.
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
    def upload_id(self, val):
        self._upload_id = None
        self.__has_upload_id = False

    @property
    def offset(self):
        """
        The offset into the file of the current chunk of data being uploaded. It
        can also be thought of as the amount of data that has been uploaded so
        far. We use the offset as a sanity check.
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
    def offset(self, val):
        self._offset = None
        self.__has_offset = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        upload_append = UploadAppend()
        if 'upload_id' not in obj:
            raise KeyError("missing required field 'upload_id'")
        upload_append.upload_id = transformer.convert_from(upload_append.__upload_id_data_type, obj['upload_id'])
        if 'offset' not in obj:
            raise KeyError("missing required field 'offset'")
        upload_append.offset = transformer.convert_from(upload_append.__offset_data_type, obj['offset'])
        return upload_append

    def to_dict(self, transformer):
        d = dict(upload_id=transformer.convert_to(self.__upload_id_data_type, self._upload_id),
                 offset=transformer.convert_to(self.__offset_data_type, self._offset))
        return d

    def __repr__(self):
        return 'UploadAppend(%r)' % self._upload_id

class IncorrectOffsetError(object):

    __correct_offset_data_type = dt.UInt64()

    __fields = {
        'correct_offset',
    }

    def __init__(self):
        self._correct_offset = None
        self.__has_correct_offset = False

    def validate(self):
        return all([
            self.__has_correct_offset,
        ])

    @property
    def correct_offset(self):
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
    def correct_offset(self, val):
        self._correct_offset = None
        self.__has_correct_offset = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        incorrect_offset_error = IncorrectOffsetError()
        if 'correct_offset' not in obj:
            raise KeyError("missing required field 'correct_offset'")
        incorrect_offset_error.correct_offset = transformer.convert_from(incorrect_offset_error.__correct_offset_data_type, obj['correct_offset'])
        return incorrect_offset_error

    def to_dict(self, transformer):
        d = dict(correct_offset=transformer.convert_to(self.__correct_offset_data_type, self._correct_offset))
        return d

    def __repr__(self):
        return 'IncorrectOffsetError(%r)' % self._correct_offset

class UploadAppendError(object):

    NotFound = object()
    Closed = object()
    IncorrectOffset = IncorrectOffsetError

    def __init__(self):
        self._incorrect_offset = None
        self.__tag = None

    def validate(self):
        return self.__tag is not None

    def is_not_found(self):
        return self.__tag == 'not_found'

    def is_closed(self):
        return self.__tag == 'closed'

    def is_incorrect_offset(self):
        return self.__tag == 'incorrect_offset'

    def set_not_found(self):
        self.__tag = 'not_found'

    def set_closed(self):
        self.__tag = 'closed'

    @property
    def incorrect_offset(self):
        if not self.is_incorrect_offset():
            raise KeyError("tag 'incorrect_offset' not set")
        return self._incorrect_offset

    @incorrect_offset.setter
    def incorrect_offset(self, val):
        if not isinstance(val, IncorrectOffsetError):
            raise TypeError('incorrect_offset is of type %r but must be of type IncorrectOffsetError' % type(val).__name__)
        val.validate()
        self._incorrect_offset = val
        self.__tag = 'incorrect_offset'

    @classmethod
    def from_dict(cls, transformer, obj):
        upload_append_error = cls()
        if isinstance(obj, dict) and len(obj) != 1:
            raise KeyError("Union can only have one key set not %d" % len(obj))
        if obj == 'not_found':
            upload_append_error.set_not_found()
        if obj == 'closed':
            upload_append_error.set_closed()
        if isinstance(obj, dict) and 'incorrect_offset' == obj.keys()[0]:
            upload_append_error.incorrect_offset = IncorrectOffsetError.from_dict(transformer, obj['incorrect_offset'])
        return upload_append_error

    def to_dict(self, transformer):
        if self.is_not_found():
            return 'not_found'
        if self.is_closed():
            return 'closed'
        if self.is_incorrect_offset():
            return dict(incorrect_offset=self.incorrect_offset.to_dict(transformer))

    def __repr__(self):
        return 'UploadAppendError(%r)' % self.__tag

class UpdateParentRev(object):

    __parent_rev_data_type = dt.String(pattern=None)

    __fields = {
        'parent_rev',
    }

    def __init__(self):
        self._parent_rev = None
        self.__has_parent_rev = False

    def validate(self):
        return all([
            self.__has_parent_rev,
        ])

    @property
    def parent_rev(self):
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
    def parent_rev(self, val):
        self._parent_rev = None
        self.__has_parent_rev = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        update_parent_rev = UpdateParentRev()
        if 'parent_rev' not in obj:
            raise KeyError("missing required field 'parent_rev'")
        update_parent_rev.parent_rev = transformer.convert_from(update_parent_rev.__parent_rev_data_type, obj['parent_rev'])
        return update_parent_rev

    def to_dict(self, transformer):
        d = dict(parent_rev=transformer.convert_to(self.__parent_rev_data_type, self._parent_rev))
        return d

    def __repr__(self):
        return 'UpdateParentRev(%r)' % self._parent_rev

class A(object):
    """
    Boo

    :ivar top: This is blah.
    """

    def __init__(self, top):
        """
        :param str top: asdfa
        """
        # asdfa
        self.top = top # yes

    @property
    def junk(self):
        """hello2"""
        return 'halleluja'

    def hi(self):
        """test"""
        return 3


a = A()
a.hi()
print a.junk
print a.top


class ConflictPolicy(object):
    """
    The action to take when a file path conflict exists.

    :ivar Add: On a conflict, the upload is rejected. You can call the Upload
        endpoint again and try a different path.
    :ivar Overwrite: On a conflict, the target is overridden.
    :ivar Update: On a conflict, only overwrite the target if the parent_rev
        matches.
    """

    Add = object()
    Overwrite = object()
    Update = UpdateParentRev

    def __init__(self):
        self._update = None
        self.__tag = None

    def validate(self):
        return self.__tag is not None

    def is_add(self):
        return self.__tag == 'add'

    def is_overwrite(self):
        return self.__tag == 'overwrite'

    def is_update(self):
        return self.__tag == 'update'

    def set_add(self):
        self.__tag = 'add'

    def set_overwrite(self):
        self.__tag = 'overwrite'

    @property
    def update(self):
        if not self.is_update():
            raise KeyError("tag 'update' not set")
        return self._update

    @update.setter
    def update(self, val):
        if not isinstance(val, UpdateParentRev):
            raise TypeError('update is of type %r but must be of type UpdateParentRev' % type(val).__name__)
        val.validate()
        self._update = val
        self.__tag = 'update'

    @classmethod
    def from_dict(cls, transformer, obj):
        conflict_policy = cls()
        if isinstance(obj, dict) and len(obj) != 1:
            raise KeyError("Union can only have one key set not %d" % len(obj))
        if obj == 'add':
            conflict_policy.set_add()
        if obj == 'overwrite':
            conflict_policy.set_overwrite()
        if isinstance(obj, dict) and 'update' == obj.keys()[0]:
            conflict_policy.update = UpdateParentRev.from_dict(transformer, obj['update'])
        return conflict_policy

    def to_dict(self, transformer):
        if self.is_add():
            return 'add'
        if self.is_overwrite():
            return 'overwrite'
        if self.is_update():
            return dict(update=self.update.to_dict(transformer))

    def __repr__(self):
        return 'ConflictPolicy(%r)' % self.__tag

class UploadCommit(object):

    __path_data_type = dt.String(pattern=None)
    __autorename_data_type = dt.Boolean()
    __client_modified_utc_data_type = dt.UInt64()
    __mute_data_type = dt.Boolean()

    __fields = {
        'path',
        'mode',
        'append_to',
        'autorename',
        'client_modified_utc',
        'mute',
    }

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

    def validate(self):
        return all([
            self.__has_path,
            self.__has_mode,
        ])

    @property
    def path(self):
        """
        Path in the user's Dropbox to save the file.
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
    def path(self, val):
        self._path = None
        self.__has_path = False

    @property
    def mode(self):
        """
        The course of action to take if a file already exists at ``path``.
        """
        if self.__has_mode:
            return self._mode
        else:
            raise KeyError("missing required field 'mode'")

    @mode.setter
    def mode(self, val):
        if not isinstance(val, ConflictPolicy):
            raise TypeError('mode is of type %r but must be of type ConflictPolicy' % type(val).__name__)
        val.validate()
        self._mode = val
        self.__has_mode = True

    @mode.deleter
    def mode(self, val):
        self._mode = None
        self.__has_mode = False

    @property
    def append_to(self):
        """
        If specified, the current chunk of data should be appended to an
        existing upload session.
        """
        if self.__has_append_to:
            return self._append_to
        else:
            return None

    @append_to.setter
    def append_to(self, val):
        if not isinstance(val, UploadAppend):
            raise TypeError('append_to is of type %r but must be of type UploadAppend' % type(val).__name__)
        val.validate()
        self._append_to = val
        self.__has_append_to = True

    @append_to.deleter
    def append_to(self, val):
        self._append_to = None
        self.__has_append_to = False

    @property
    def autorename(self):
        if self.__has_autorename:
            return self._autorename
        else:
            False

    @autorename.setter
    def autorename(self, val):
        self.__autorename_data_type.validate(val)
        self._autorename = val
        self.__has_autorename = True

    @autorename.deleter
    def autorename(self, val):
        self._autorename = None
        self.__has_autorename = False

    @property
    def client_modified_utc(self):
        if self.__has_client_modified_utc:
            return self._client_modified_utc
        else:
            None

    @client_modified_utc.setter
    def client_modified_utc(self, val):
        self.__client_modified_utc_data_type.validate(val)
        self._client_modified_utc = val
        self.__has_client_modified_utc = True

    @client_modified_utc.deleter
    def client_modified_utc(self, val):
        self._client_modified_utc = None
        self.__has_client_modified_utc = False

    @property
    def mute(self):
        if self.__has_mute:
            return self._mute
        else:
            False

    @mute.setter
    def mute(self, val):
        self.__mute_data_type.validate(val)
        self._mute = val
        self.__has_mute = True

    @mute.deleter
    def mute(self, val):
        self._mute = None
        self.__has_mute = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        upload_commit = UploadCommit()
        if 'path' not in obj:
            raise KeyError("missing required field 'path'")
        upload_commit.path = transformer.convert_from(upload_commit.__path_data_type, obj['path'])
        if 'mode' not in obj:
            raise KeyError("missing required field 'mode'")
        upload_commit.mode = ConflictPolicy.from_dict(transformer, obj['mode'])
        if obj.get('append_to') is not None:
            upload_commit.append_to = UploadAppend.from_dict(transformer, obj['append_to'])
        upload_commit.autorename = transformer.convert_from(upload_commit.__autorename_data_type, obj.get('autorename'))
        upload_commit.client_modified_utc = transformer.convert_from(upload_commit.__client_modified_utc_data_type, obj.get('client_modified_utc'))
        upload_commit.mute = transformer.convert_from(upload_commit.__mute_data_type, obj.get('mute'))
        return upload_commit

    def to_dict(self, transformer):
        d = dict(path=transformer.convert_to(self.__path_data_type, self._path),
                 mode=self._mode.to_dict(transformer))
        if self._append_to is not None:
            d['append_to'] = self._append_to.to_dict(transformer)
        if self._autorename is not None:
            d['autorename'] = transformer.convert_to(self.__autorename_data_type, self._autorename)
        if self._client_modified_utc is not None:
            d['client_modified_utc'] = transformer.convert_to(self.__client_modified_utc_data_type, self._client_modified_utc)
        if self._mute is not None:
            d['mute'] = transformer.convert_to(self.__mute_data_type, self._mute)
        return d

    def __repr__(self):
        return 'UploadCommit(%r)' % self._path

class ConflictReason(object):

    Folder = object()
    File = object()
    AutorenameFailed = object()

    def __init__(self):
        pass
        self.__tag = None

    def validate(self):
        return self.__tag is not None

    def is_folder(self):
        return self.__tag == 'folder'

    def is_file(self):
        return self.__tag == 'file'

    def is_autorename_failed(self):
        return self.__tag == 'autorename_failed'

    def set_folder(self):
        self.__tag = 'folder'

    def set_file(self):
        self.__tag = 'file'

    def set_autorename_failed(self):
        self.__tag = 'autorename_failed'

    @classmethod
    def from_dict(cls, transformer, obj):
        conflict_reason = cls()
        if isinstance(obj, dict) and len(obj) != 1:
            raise KeyError("Union can only have one key set not %d" % len(obj))
        if obj == 'folder':
            conflict_reason.set_folder()
        if obj == 'file':
            conflict_reason.set_file()
        if obj == 'autorename_failed':
            conflict_reason.set_autorename_failed()
        return conflict_reason

    def to_dict(self, transformer):
        if self.is_folder():
            return 'folder'
        if self.is_file():
            return 'file'
        if self.is_autorename_failed():
            return 'autorename_failed'

    def __repr__(self):
        return 'ConflictReason(%r)' % self.__tag

class ConflictError(object):

    __fields = {
        'reason',
    }

    def __init__(self):
        self._reason = None
        self.__has_reason = False

    def validate(self):
        return all([
            self.__has_reason,
        ])

    @property
    def reason(self):
        if self.__has_reason:
            return self._reason
        else:
            raise KeyError("missing required field 'reason'")

    @reason.setter
    def reason(self, val):
        if not isinstance(val, ConflictReason):
            raise TypeError('reason is of type %r but must be of type ConflictReason' % type(val).__name__)
        val.validate()
        self._reason = val
        self.__has_reason = True

    @reason.deleter
    def reason(self, val):
        self._reason = None
        self.__has_reason = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        conflict_error = ConflictError()
        if 'reason' not in obj:
            raise KeyError("missing required field 'reason'")
        conflict_error.reason = ConflictReason.from_dict(transformer, obj['reason'])
        return conflict_error

    def to_dict(self, transformer):
        d = dict(reason=self._reason.to_dict(transformer))
        return d

    def __repr__(self):
        return 'ConflictError(%r)' % self._reason

class UploadCommitError(object):

    Conflict = ConflictError
    NoWritePermission = object()
    InsufficientQuota = object()

    def __init__(self):
        self._conflict = None
        self.__tag = None

    def validate(self):
        return self.__tag is not None

    def is_conflict(self):
        return self.__tag == 'conflict'

    def is_no_write_permission(self):
        return self.__tag == 'no_write_permission'

    def is_insufficient_quota(self):
        return self.__tag == 'insufficient_quota'

    @property
    def conflict(self):
        if not self.is_conflict():
            raise KeyError("tag 'conflict' not set")
        return self._conflict

    @conflict.setter
    def conflict(self, val):
        if not isinstance(val, ConflictError):
            raise TypeError('conflict is of type %r but must be of type ConflictError' % type(val).__name__)
        val.validate()
        self._conflict = val
        self.__tag = 'conflict'

    def set_no_write_permission(self):
        self.__tag = 'no_write_permission'

    def set_insufficient_quota(self):
        self.__tag = 'insufficient_quota'

    @classmethod
    def from_dict(cls, transformer, obj):
        upload_commit_error = cls()
        if isinstance(obj, dict) and len(obj) != 1:
            raise KeyError("Union can only have one key set not %d" % len(obj))
        if isinstance(obj, dict) and 'conflict' == obj.keys()[0]:
            upload_commit_error.conflict = ConflictError.from_dict(transformer, obj['conflict'])
        if obj == 'no_write_permission':
            upload_commit_error.set_no_write_permission()
        if obj == 'insufficient_quota':
            upload_commit_error.set_insufficient_quota()
        return upload_commit_error

    def to_dict(self, transformer):
        if self.is_conflict():
            return dict(conflict=self.conflict.to_dict(transformer))
        if self.is_no_write_permission():
            return 'no_write_permission'
        if self.is_insufficient_quota():
            return 'insufficient_quota'

    def __repr__(self):
        return 'UploadCommitError(%r)' % self.__tag

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

    __client_modified_data_type = dt.Timestamp(format='%a, %d %b %Y %H:%M:%S +0000')
    __server_modified_data_type = dt.Timestamp(format='%a, %d %b %Y %H:%M:%S +0000')
    __rev_data_type = dt.String(pattern=None)
    __size_data_type = dt.UInt64()

    __fields = {
        'client_modified',
        'server_modified',
        'rev',
        'size',
    }

    def __init__(self):
        self._client_modified = None
        self.__has_client_modified = False
        self._server_modified = None
        self.__has_server_modified = False
        self._rev = None
        self.__has_rev = False
        self._size = None
        self.__has_size = False

    def validate(self):
        return all([
            self.__has_client_modified,
            self.__has_server_modified,
            self.__has_rev,
            self.__has_size,
        ])

    @property
    def client_modified(self):
        """
        For files, this is the modification time set by the desktop client when
        the file was added to Dropbox. Since this time is not verified (the
        Dropbox server stores whatever the desktop client sends up), this should
        only be used for display purposes (such as sorting) and not, for
        example, to determine if a file has changed or not.
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
    def client_modified(self, val):
        self._client_modified = None
        self.__has_client_modified = False

    @property
    def server_modified(self):
        """
        The last time the file was modified on Dropbox.
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
    def server_modified(self, val):
        self._server_modified = None
        self.__has_server_modified = False

    @property
    def rev(self):
        """
        A unique identifier for the current revision of a file. This field is
        the same rev as elsewhere in the API and can be used to detect changes
        and avoid conflicts.
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
    def rev(self, val):
        self._rev = None
        self.__has_rev = False

    @property
    def size(self):
        """
        The file size in bytes.
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
    def size(self, val):
        self._size = None
        self.__has_size = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        file = File()
        if 'client_modified' not in obj:
            raise KeyError("missing required field 'client_modified'")
        file.client_modified = transformer.convert_from(file.__client_modified_data_type, obj['client_modified'])
        if 'server_modified' not in obj:
            raise KeyError("missing required field 'server_modified'")
        file.server_modified = transformer.convert_from(file.__server_modified_data_type, obj['server_modified'])
        if 'rev' not in obj:
            raise KeyError("missing required field 'rev'")
        file.rev = transformer.convert_from(file.__rev_data_type, obj['rev'])
        if 'size' not in obj:
            raise KeyError("missing required field 'size'")
        file.size = transformer.convert_from(file.__size_data_type, obj['size'])
        return file

    def to_dict(self, transformer):
        d = dict(client_modified=transformer.convert_to(self.__client_modified_data_type, self._client_modified),
                 server_modified=transformer.convert_to(self.__server_modified_data_type, self._server_modified),
                 rev=transformer.convert_to(self.__rev_data_type, self._rev),
                 size=transformer.convert_to(self.__size_data_type, self._size))
        return d

    def __repr__(self):
        return 'File(%r)' % self._client_modified

class Folder(object):
    """
    A folder resource

    """

    __fields = {
    }

    def __init__(self):
        pass

    def validate(self):
        return all([
        ])

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        folder = Folder()
        return folder

    def to_dict(self, transformer):
        d = dict()
        return d

    def __repr__(self):
        return 'Folder()'

class Metadata(object):

    File = File
    Folder = Folder

    def __init__(self):
        self._file = None
        self._folder = None
        self.__tag = None

    def validate(self):
        return self.__tag is not None

    def is_file(self):
        return self.__tag == 'file'

    def is_folder(self):
        return self.__tag == 'folder'

    @property
    def file(self):
        if not self.is_file():
            raise KeyError("tag 'file' not set")
        return self._file

    @file.setter
    def file(self, val):
        if not isinstance(val, File):
            raise TypeError('file is of type %r but must be of type File' % type(val).__name__)
        val.validate()
        self._file = val
        self.__tag = 'file'

    @property
    def folder(self):
        if not self.is_folder():
            raise KeyError("tag 'folder' not set")
        return self._folder

    @folder.setter
    def folder(self, val):
        if not isinstance(val, Folder):
            raise TypeError('folder is of type %r but must be of type Folder' % type(val).__name__)
        val.validate()
        self._folder = val
        self.__tag = 'folder'

    @classmethod
    def from_dict(cls, transformer, obj):
        metadata = cls()
        if isinstance(obj, dict) and len(obj) != 1:
            raise KeyError("Union can only have one key set not %d" % len(obj))
        if isinstance(obj, dict) and 'file' == obj.keys()[0]:
            metadata.file = File.from_dict(transformer, obj['file'])
        if isinstance(obj, dict) and 'folder' == obj.keys()[0]:
            metadata.folder = Folder.from_dict(transformer, obj['folder'])
        return metadata

    def to_dict(self, transformer):
        if self.is_file():
            return dict(file=self.file.to_dict(transformer))
        if self.is_folder():
            return dict(folder=self.folder.to_dict(transformer))

    def __repr__(self):
        return 'Metadata(%r)' % self.__tag

class Entry(object):

    __name_data_type = dt.String(pattern=None)

    __fields = {
        'metadata',
        'name',
    }

    def __init__(self):
        self._metadata = None
        self.__has_metadata = False
        self._name = None
        self.__has_name = False

    def validate(self):
        return all([
            self.__has_metadata,
            self.__has_name,
        ])

    @property
    def metadata(self):
        if self.__has_metadata:
            return self._metadata
        else:
            raise KeyError("missing required field 'metadata'")

    @metadata.setter
    def metadata(self, val):
        if not isinstance(val, Metadata):
            raise TypeError('metadata is of type %r but must be of type Metadata' % type(val).__name__)
        val.validate()
        self._metadata = val
        self.__has_metadata = True

    @metadata.deleter
    def metadata(self, val):
        self._metadata = None
        self.__has_metadata = False

    @property
    def name(self):
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
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        entry = Entry()
        if 'metadata' not in obj:
            raise KeyError("missing required field 'metadata'")
        entry.metadata = Metadata.from_dict(transformer, obj['metadata'])
        if 'name' not in obj:
            raise KeyError("missing required field 'name'")
        entry.name = transformer.convert_from(entry.__name_data_type, obj['name'])
        return entry

    def to_dict(self, transformer):
        d = dict(metadata=self._metadata.to_dict(transformer),
                 name=transformer.convert_to(self.__name_data_type, self._name))
        return d

    def __repr__(self):
        return 'Entry(%r)' % self._metadata

class ListFolderResponse(object):

    __cursor_data_type = dt.String(pattern=None)
    __has_more_data_type = dt.Boolean()
    __entries_data_type = dt.List(data_type=Entry)

    __fields = {
        'cursor',
        'has_more',
        'entries',
    }

    def __init__(self):
        self._cursor = None
        self.__has_cursor = False
        self._has_more = None
        self.__has_has_more = False
        self._entries = None
        self.__has_entries = False

    def validate(self):
        return all([
            self.__has_cursor,
            self.__has_has_more,
            self.__has_entries,
        ])

    @property
    def cursor(self):
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
    def cursor(self, val):
        self._cursor = None
        self.__has_cursor = False

    @property
    def has_more(self):
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
    def has_more(self, val):
        self._has_more = None
        self.__has_has_more = False

    @property
    def entries(self):
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
    def entries(self, val):
        self._entries = None
        self.__has_entries = False

    @classmethod
    def from_dict(cls, transformer, obj):
        for key in obj:
            if key not in cls.__fields:
                raise KeyError("Unknown key: %r" % key)
        list_folder_response = ListFolderResponse()
        if 'cursor' not in obj:
            raise KeyError("missing required field 'cursor'")
        list_folder_response.cursor = transformer.convert_from(list_folder_response.__cursor_data_type, obj['cursor'])
        if 'has_more' not in obj:
            raise KeyError("missing required field 'has_more'")
        list_folder_response.has_more = transformer.convert_from(list_folder_response.__has_more_data_type, obj['has_more'])
        if 'entries' not in obj:
            raise KeyError("missing required field 'entries'")
        list_folder_response.entries = transformer.convert_from(list_folder_response.__entries_data_type, obj['entries'])
        return list_folder_response

    def to_dict(self, transformer):
        d = dict(cursor=transformer.convert_to(self.__cursor_data_type, self._cursor),
                 has_more=transformer.convert_to(self.__has_more_data_type, self._has_more),
                 entries=transformer.convert_to(self.__entries_data_type, self._entries))
        return d

    def __repr__(self):
        return 'ListFolderResponse(%r)' % self._cursor

