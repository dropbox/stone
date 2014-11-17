from .base_files import (
    BaseFiles,
    ConflictPolicy as _ConflictPolicy,
    UpdateParentRev as _UpdateParentRev,
    Append,
)

ConflictPolicy = _ConflictPolicy
UpdateParentRev = _UpdateParentRev

class Files(BaseFiles):
    """
    Routes for the files namespace.
    """
    def get_chunked_uploader(self, file_obj, length):
        """Creates a :class:`ChunkedUploader` to upload the given file-like object.

        :param file_obj: A file-like object which is the source of the data
            being uploaded.
        :param int length: The number of bytes to upload.

        :rtype: :class:`ChunkedUploader`
        """
        return ChunkedUploader(self, file_obj, length)

class ChunkedUploader(object):
    """
    Wrapper for uploading a file in chunks. This is ideal for uploading large
    files (10MB+) which take time to upload and may be interrupted.
    """

    def __init__(self, files_client, file_obj, length):
        self.files_client = files_client
        self.offset = 0
        self.upload_id = None

        self.file_obj = file_obj
        self.target_length = length

    def upload(self, chunk_size=2**22):
        """
        Uploads data from this ChunkedUploader's file_obj in chunks.

        :param int chunk-size: The maximum number of bytes to put in each chunk.
        """

        first_chunk_size = min(chunk_size, self.target_length - self.offset)
        first_chunk = self.file_obj.read(first_chunk_size)
        session = self.files_client.upload_session_start(first_chunk)
        self.offset += first_chunk_size
        self.upload_id = session.upload_id

        while self.offset < self.target_length:
            next_chunk_size = min(chunk_size, self.target_length - self.offset)
            next_chunk = self.file_obj.read(next_chunk_size)
            self.files_client.upload_session_append(next_chunk, self.upload_id, self.offset)
            self.offset += next_chunk_size

    def finish(self,
               path,
               mode,
               autorename=False,
               client_modified_utc=None,
               mute=False):
        """Commits the bytes uploaded by this ChunkedUploader to a file
        in the users dropbox

        Use this endpoint to either finish an ongoing upload session that was
        begun with :func:`upload`.

        :param str path: Path in the user's Dropbox to save the file.
        :param ConflictPolicy mode: The course of action to take if a file already exists at
            path.
        :type mode: :class:`~dropbox.base_files.ConflictPolicy`
        :param bool autorename: Whether the file should be autorenamed in the event of a
            conflict.
        :param int client_modified_utc: Self reported time of when this file was
            created or modified.
        :param bool mute: Whether the devices that the user has linked should notify
            them of the new or updated file.

        :raises ApiError:
            ApiError with the following codes:
                conflict
                no_write_permission: User does not have permission to write in
                    the folder. An example of this is if the folder is a read-
                    only shared folder.
                insufficient_quota: User does not have sufficient space quota to
                    save the file.
        """
        append_to = Append(self.upload_id, self.offset)

        return self.files_client.upload_session_finish(
            None,
            path,
            mode,
            autorename=autorename,
            client_modified_utc=client_modified_utc,
            mute=mute,
            append_to=append_to,
        )
