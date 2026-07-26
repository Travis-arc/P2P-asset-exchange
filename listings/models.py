from django.conf import settings
from django.db import models


class Category(models.Model):
    """
    Chapter 3.4 Stage 2: items are grouped by category (e.g. Textbooks,
    Electronics, Lab Equipment) so the search/filter module (built next)
    has something structured to filter on.
    """
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Asset(models.Model):
    """
    A single item a verified user is offering to lend/exchange.
    """

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('worn', 'Worn'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('borrowed', 'Borrowed'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assets',
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='assets',
    )
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    photo = models.ImageField(upload_to='asset_photos/', blank=True, null=True)

    # Chapter 3.4 Stage 4/6: tracks where the item is in the exchange
    # lifecycle -- this is what the reservation and QR-handshake modules
    # will update later.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"