import uuid

from django.conf import settings
from django.db import models

from listings.models import Asset


class Reservation(models.Model):
    """
    Chapter 3.4 Stage 4: a request from one student (the requester) to
    borrow/exchange another student's listed item. This is the step
    before the QR handshake -- it represents "I'd like this item,"
    which the owner then accepts or declines.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
        ('picked_up', 'Picked Up'),   # Stage 6: borrower has the item
        ('returned', 'Returned'),      # Stage 7: item safely back with owner
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations_made',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Chapter 3.4 Stage 5/7: once accepted, this unique token becomes the
    # payload of a QR code. Scanning it (and confirming as the borrower)
    # is what proves the physical handover actually happened.
    # Stage 5/6: pickup handshake (owner shows this, borrower scans/confirms)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    picked_up_at = models.DateTimeField(null=True, blank=True)

    # Stage 7: reverse handshake (borrower shows this, owner scans/confirms)
    return_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    returned_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester} wants '{self.asset.title}' ({self.get_status_display()})"