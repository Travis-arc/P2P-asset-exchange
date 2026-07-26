from django.db.models import Avg, Count
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Rating


@receiver(post_save, sender=Rating)
def update_reputation_score(sender, instance, created, **kwargs):
    """
    Whenever a Rating is saved, recalculate the ratee's average score
    and total count from scratch. Recalculating (rather than doing
    running-average math) is simpler to get right and cheap enough at
    this scale.
    """
    if not created:
        return  # only recalculate when a NEW rating is added

    ratee = instance.ratee
    stats = Rating.objects.filter(ratee=ratee).aggregate(
        avg_score=Avg('score'),
        count=Count('id'),
    )
    ratee.reputation_score = round(stats['avg_score'], 2)
    ratee.total_ratings = stats['count']
    ratee.save(update_fields=['reputation_score', 'total_ratings'])