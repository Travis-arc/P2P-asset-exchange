from django.contrib import admin

from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('rater', 'ratee', 'score', 'reservation', 'created_at')
    list_filter = ('score',)
    search_fields = ('rater__email', 'ratee__email', 'comment')