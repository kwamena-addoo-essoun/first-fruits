import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# When running under pytest (TESTING=true) use a ceiling high enough that
# tests never hit the limit; in production the real limits apply.
_IS_TESTING = os.getenv("TESTING", "").lower() in ("1", "true", "yes")

LOGIN_RATE_LIMIT = "10000/minute" if _IS_TESTING else "10/minute"
REGISTER_RATE_LIMIT = "10000/minute" if _IS_TESTING else "5/minute"
FORGOT_PASSWORD_RATE_LIMIT = "10000/minute" if _IS_TESTING else "3/minute"
RESEND_VERIFICATION_RATE_LIMIT = "10000/minute" if _IS_TESTING else "3/minute"

limiter = Limiter(key_func=get_remote_address)
