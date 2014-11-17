class ApiError(Exception):
    """Errors produced by the Dropbox API."""
    def __init__(self, reason, details):
        super(ApiError, self).__init__(reason, details)
        self.reason = reason
        self.details = details
    def __repr__(self):
        return 'ApiError({}, {!r})'.format(self.reason, self.details)

class HttpError(Exception):
    """Errors produced at the HTTP layer."""
    def __init__(self, status_code, body):
        super(HttpError, self).__init__(status_code, body)
        self.status_code = status_code
        self.body = body
    def __repr__(self):
        return 'HttpError({}, {!r})'.format(self.status_code, self.body)

class BadInputError(HttpError):
    """Errors due to bad input parameters to an API Operation."""
    def __init__(self, message):
        super(BadInputError, self).__init__(400, message)
        self.message = message
    def __repr__(self):
        return 'BadInputError({!r})'.format(self.message)

class RateLimitError(HttpError):
    """Error caused by rate limiting."""
    def __init__(self, backoff=None):
        super(RateLimitError, self).__init__(429)
        self.backoff = backoff
    def __repr__(self):
        return 'RateLimitError({!r})'.format(self.backoff)

class InternalServerError(HttpError):
    """Errors due to a problem on Dropbox."""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
    def __repr__(self):
        return 'InternalServerError({}, {!r})'.format(self.status_code, self.message)
