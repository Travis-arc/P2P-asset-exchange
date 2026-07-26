from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from transactions.models import Reservation
from .forms import RatingForm
from .models import Rating


@login_required
def rate_view(request, reservation_pk):
    reservation = get_object_or_404(Reservation, pk=reservation_pk)

    if reservation.status != 'returned':
        messages.error(request, "You can only rate exchanges after the item has been returned.")
        return redirect('transactions:my_reservations')

    owner = reservation.asset.owner
    borrower = reservation.requester

    if request.user not in (owner, borrower):
        messages.error(request, "You weren't part of this exchange.")
        return redirect('transactions:my_reservations')

    ratee = borrower if request.user == owner else owner

    if Rating.objects.filter(reservation=reservation, rater=request.user).exists():
        messages.info(request, "You've already rated this exchange.")
        return redirect('transactions:my_reservations')

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.reservation = reservation
            rating.rater = request.user
            rating.ratee = ratee
            rating.save()
            messages.success(request, f"Rating submitted for {ratee.username}.")
            return redirect('transactions:my_reservations')
    else:
        form = RatingForm()

    return render(request, 'ratings/rate_form.html', {'form': form, 'ratee': ratee, 'reservation': reservation})