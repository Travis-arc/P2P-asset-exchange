from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from transactions.models import Reservation


class Rating(models.Model):
    """
    Chapter 1.7 'Reputation-Based Rating System': after a completed
    exchange, each side rates the other. Both the owner and the
    borrower can leave one rating each per reservation.
    """

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    rater = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings_given',
    )
    ratee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings_received',
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A person can only rate the other side of a given reservation once.
        unique_together = ('reservation', 'rater')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rater.username} rated {self.ratee.username}: {self.score}/5"