class Empty(object):

    def __init__(self):
        pass

class FileTarget(object):

    def __init__(self,
                 path,
                 rev):
        # Path from root. Should be an empty string for root.
        self.path = path
        # Revision of target file.
        self.rev = rev

class FileInfo(object):

    def __init__(self,
                 name):
        # Name of file.
        self.name = name

class SubError(object):

    def __init__(self,
                 reason):
        # A code indicating the type of error.
        self.reason = reason

class UploadSessionStart(object):

    def __init__(self,
                 upload_id):
        # A unique identifier for the upload session.
        self.upload_id = upload_id

class UploadAppend(object):

    def __init__(self,
                 upload_id,
                 offset):
        # Identifies the upload session to append data to.
        self.upload_id = upload_id
        # The offset into the file of the current chunk of data being uploaded.
        # It can also be thought of as the amount of data that has been uploaded
        # so far. We use the offset as a sanity check.
        self.offset = offset

class IncorrectOffsetError(object):

    def __init__(self,
                 correct_offset):
        self.correct_offset = correct_offset

class UpdateParentRev(object):

    def __init__(self,
                 parent_rev):
        self.parent_rev = parent_rev

class UploadCommit(object):

    def __init__(self,
                 path,
                 mode,
                 append_to,
                 autorename,
                 client_modified_utc,
                 mute):
        # Path in the user's Dropbox to save the file.
        self.path = path
        # The course of action to take if a file already exists at
        # :field:`path`.
        self.mode = mode
        # If specified, the current chunk of data should be appended to an
        # existing upload session.
        self.append_to = append_to
        # Whether the file should be autorenamed in the event of a conflict.
        self.autorename = autorename
        # Self reported time of when this file was created or modified.
        self.client_modified_utc = client_modified_utc
        # Whether the devices that the user has linked should notify them of the
        # new or updated file.
        self.mute = mute

class ConflictError(object):

    def __init__(self,
                 reason):
        self.reason = reason

