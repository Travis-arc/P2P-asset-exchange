from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AssetForm
from .models import Asset, Category


def asset_list_view(request):
    assets = Asset.objects.filter(status='available').select_related('owner', 'category')

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    condition = request.GET.get('condition', '')

    if query:
        assets = assets.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(owner__username__icontains=query) |
            models.Q(owner__department__icontains=query)
        )
    if category_id:
        assets = assets.filter(category_id=category_id)
    if condition:
        assets = assets.filter(condition=condition)

    paginator = Paginator(assets, 6)  # 6 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'assets': page_obj,
        'categories': Category.objects.all(),
        'conditions': Asset.CONDITION_CHOICES,
        'query': query,
        'selected_category': category_id,
        'selected_condition': condition,
    }
    return render(request, 'listings/asset_list.html', context)

def asset_detail_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    return render(request, 'listings/asset_detail.html', {'asset': asset})


@login_required
def asset_create_view(request):
    if not request.user.is_email_verified:
        messages.error(request, "Verify your email before listing an item.")
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.owner = request.user
            asset.save()
            messages.success(request, "Item listed successfully.")
            return redirect('listings:asset_detail', pk=asset.pk)
    else:
        form = AssetForm()
    return render(request, 'listings/asset_form.html', {'form': form})


@login_required
def asset_edit_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk)

    if asset.owner != request.user:
        messages.error(request, "You can only edit your own listings.")
        return redirect('listings:asset_detail', pk=asset.pk)

    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, "Listing updated.")
            return redirect('listings:asset_detail', pk=asset.pk)
    else:
        form = AssetForm(instance=asset)
    return render(request, 'listings/asset_form.html', {'form': form, 'editing': True})


@login_required
def asset_delete_view(request, pk):
    asset = get_object_or_404(Asset, pk=pk)

    if asset.owner != request.user:
        messages.error(request, "You can only delete your own listings.")
        return redirect('listings:asset_detail', pk=asset.pk)

    if asset.status != 'available':
        messages.error(request, "You can't delete an item that's reserved or borrowed.")
        return redirect('listings:asset_detail', pk=asset.pk)

    if request.method == 'POST':
        asset.delete()
        messages.success(request, "Listing deleted.")
        return redirect('listings:asset_list')

    return render(request, 'listings/asset_confirm_delete.html', {'asset': asset})