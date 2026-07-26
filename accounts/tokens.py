from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Reuses Django's PasswordResetTokenGenerator machinery (a signed,
    time-limited, single-use hash) to produce email-verification tokens
    instead of writing our own crypto. The token becomes invalid once
    is_email_verified flips to True, because that field feeds the hash.
    """

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_email_verified}"


email_verification_token = EmailVerificationTokenGenerator()