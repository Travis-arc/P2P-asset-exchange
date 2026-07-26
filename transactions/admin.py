from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('asset', 'requester', 'status', 'created_at', 'responded_at')
    list_filter = ('status',)
    search_fields = ('asset__title', 'requester__email')
    readonly_fields = ('qr_token', 'return_token')