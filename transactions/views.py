import io

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from listings.models import Asset
from .models import Reservation
from ratings.models import Rating

@login_required
def reservation_request_view(request, asset_pk):
    asset = get_object_or_404(Asset, pk=asset_pk)

    if asset.owner == request.user:
        messages.error(request, "You can't reserve your own item.")
        return redirect('listings:asset_detail', pk=asset.pk)

    if asset.status != 'available':
        messages.error(request, "This item isn't available right now.")
        return redirect('listings:asset_detail', pk=asset.pk)

    if not request.user.is_email_verified:
        messages.error(request, "Verify your email before requesting items.")
        return redirect('accounts:profile')

    if Reservation.objects.filter(asset=asset, requester=request.user, status='pending').exists():
        messages.error(request, "You already have a pending request for this item.")
        return redirect('listings:asset_detail', pk=asset.pk)

    Reservation.objects.create(asset=asset, requester=request.user)
    messages.success(request, "Request sent! The owner will respond soon.")
    return redirect('listings:asset_detail', pk=asset.pk)


@login_required
def reservation_qr_view(request, pk):
    """
    Generates the QR code image for an accepted reservation. Only the
    owner (who needs to show/print it) or the requester (who scans it)
    should be able to view it.
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    if request.user not in (reservation.asset.owner, reservation.requester):
        messages.error(request, "You don't have access to this QR code.")
        return redirect('transactions:my_reservations')

    if reservation.status != 'accepted':
        messages.error(request, "This QR code is only valid for accepted reservations.")
        return redirect('transactions:my_reservations')

    confirm_url = request.build_absolute_uri(
        f'/transactions/confirm/{reservation.qr_token}/'
    )
    img = qrcode.make(confirm_url)

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


ACTIVE_STATUSES = ['pending', 'accepted', 'picked_up']
CANCELLED_STATUSES = ['declined', 'cancelled']


@login_required
def my_reservations_view(request):
    made_qs = Reservation.objects.filter(requester=request.user).select_related('asset', 'asset__category')
    received_qs = Reservation.objects.filter(asset__owner=request.user).select_related('asset', 'asset__category', 'requester')

    def bucket_counts(qs):
        return {
            'active': qs.filter(status__in=ACTIVE_STATUSES).count(),
            'completed': qs.filter(status='returned').count(),
            'cancelled': qs.filter(status__in=CANCELLED_STATUSES).count(),
        }

    made_counts = bucket_counts(made_qs)
    received_counts = bucket_counts(received_qs)
    counts = {
        'all': made_qs.count() + received_qs.count(),
        'active': made_counts['active'] + received_counts['active'],
        'completed': made_counts['completed'] + received_counts['completed'],
        'cancelled': made_counts['cancelled'] + received_counts['cancelled'],
    }

    selected_filter = request.GET.get('filter', 'all')
    if selected_filter == 'active':
        made_qs = made_qs.filter(status__in=ACTIVE_STATUSES)
        received_qs = received_qs.filter(status__in=ACTIVE_STATUSES)
    elif selected_filter == 'completed':
        made_qs = made_qs.filter(status='returned')
        received_qs = received_qs.filter(status='returned')
    elif selected_filter == 'cancelled':
        made_qs = made_qs.filter(status__in=CANCELLED_STATUSES)
        received_qs = received_qs.filter(status__in=CANCELLED_STATUSES)

    rated_ids = set(
        Rating.objects.filter(rater=request.user).values_list('reservation_id', flat=True)
    )

    return render(request, 'transactions/my_reservations.html', {
        'made': made_qs,
        'received': received_qs,
        'counts': counts,
        'selected_filter': selected_filter,
        'rated_ids': rated_ids,
    })


@login_required
def reservation_respond_view(request, pk, action):
    reservation = get_object_or_404(Reservation, pk=pk, asset__owner=request.user)

    if reservation.status != 'pending':
        messages.error(request, "This request has already been responded to.")
        return redirect('transactions:my_reservations')

    if action == 'accept':
        reservation.status = 'accepted'
        reservation.asset.status = 'reserved'
        reservation.asset.save(update_fields=['status'])

        # Auto-decline any other pending requests on this same item --
        # only one borrower can have it at a time.
        Reservation.objects.filter(
            asset=reservation.asset, status='pending'
        ).exclude(pk=reservation.pk).update(status='declined', responded_at=timezone.now())

        messages.success(request, f"Accepted request from {reservation.requester.username}.")
    elif action == 'decline':
        reservation.status = 'declined'
        messages.info(request, f"Declined request from {reservation.requester.username}.")
    else:
        messages.error(request, "Unknown action.")
        return redirect('transactions:my_reservations')

    reservation.responded_at = timezone.now()
    reservation.save()
    return redirect('transactions:my_reservations')


@login_required
def reservation_confirm_view(request, token):
    """
    Chapter 3.4 Stage 7: whoever scans the QR code lands here. Only the
    requester (the borrower) can confirm -- the owner showing/printing
    the code isn't enough on its own to prove the item changed hands;
    it has to be the other party actively confirming receipt.
    """
    reservation = get_object_or_404(Reservation, qr_token=token)

    if request.user != reservation.requester:
        messages.error(request, "Only the borrower can confirm this handover.")
        return redirect('transactions:my_reservations')

    if reservation.status != 'accepted':
        messages.error(request, "This handover has already been completed or isn't ready yet.")
        return redirect('transactions:my_reservations')

    if request.method == 'POST':
        reservation.status = 'picked_up'
        reservation.picked_up_at = timezone.now()
        reservation.save()

        reservation.asset.status = 'borrowed'
        reservation.asset.save(update_fields=['status'])

        messages.success(request, "Pickup confirmed! Remember to confirm the return once you're done.")
        return redirect('transactions:my_reservations')

    return render(request, 'transactions/confirm_handover.html', {'reservation': reservation})


@login_required
def return_qr_view(request, pk):
    """
    Stage 7 (Reverse QR Return): the BORROWER displays this QR code;
    the OWNER scans/confirms it to acknowledge the item came back safely.
    Roles are swapped compared to the pickup QR.
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    if request.user not in (reservation.asset.owner, reservation.requester):
        messages.error(request, "You don't have access to this QR code.")
        return redirect('transactions:my_reservations')

    if reservation.status != 'picked_up':
        messages.error(request, "This QR code is only valid once the item has been picked up.")
        return redirect('transactions:my_reservations')

    confirm_url = request.build_absolute_uri(
        f'/transactions/return-confirm/{reservation.return_token}/'
    )
    img = qrcode.make(confirm_url)

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


@login_required
def return_confirm_view(request, token):
    """
    Only the OWNER can confirm a return -- mirrors reservation_confirm_view,
    but with roles reversed: the owner is the one physically receiving
    the item back, so they're the one who must confirm it arrived.
    """
    reservation = get_object_or_404(Reservation, return_token=token)

    if request.user != reservation.asset.owner:
        messages.error(request, "Only the item owner can confirm a return.")
        return redirect('transactions:my_reservations')

    if reservation.status != 'picked_up':
        messages.error(request, "This return has already been confirmed or isn't ready yet.")
        return redirect('transactions:my_reservations')

    if request.method == 'POST':
        reservation.status = 'returned'
        reservation.returned_at = timezone.now()
        reservation.save()

        reservation.asset.status = 'available'
        reservation.asset.save(update_fields=['status'])

        messages.success(request, "Return confirmed! The item is available again.")
        return redirect('transactions:my_reservations')

    return render(request, 'transactions/confirm_return.html', {'reservation': reservation})