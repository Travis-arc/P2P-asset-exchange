from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


def validate_institutional_email(value):
    """
    Chapter 1.7 'Institutional Verification Filter': registration is
    restricted to official university email domains (e.g. @unizik.edu.ng).
    """
    domain = value.split('@')[-1].lower()
    allowed = [d.lower() for d in settings.ALLOWED_EMAIL_DOMAINS]
    if domain not in allowed:
        raise ValidationError(
            f"Registration is restricted to institutional email addresses "
            f"({', '.join('@' + d for d in allowed)})."
        )


class CustomUser(AbstractUser):
    """
    Our own user model. We extend AbstractUser so we keep Django's
    password hashing, login/logout, and permissions system, and only
    add the fields this project needs on top of it.
    """

    email = models.EmailField(
        unique=True,
        validators=[validate_institutional_email],
        help_text="Must be a valid institutional email address.",
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. Computer Science, Mechanical Engineering",
    )

    matric_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="e.g. 2021/241832CS",
    )

    # Chapter 3.4 Stage 1: accounts must confirm their institutional
    # email before they can list or borrow items.
    is_email_verified = models.BooleanField(default=False)

    # Chapter 3.4 Stage 8 / 1.7 'Reputation-Based Rating System'
    reputation_score = models.DecimalField(
        max_digits=3, decimal_places=2, default=5.00,
        help_text="Average peer rating out of 5. Starts neutral at 5.00.",
    )
    total_ratings = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email