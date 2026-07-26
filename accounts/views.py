from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import EmailLoginForm, RegistrationForm
from .models import CustomUser
from .tokens import email_verification_token


def home_redirect_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    return redirect('accounts:register')


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.is_active = True
            user.is_email_verified = False
            user.save()
            _send_verification_email(request, user)
            messages.success(
                request,
                "Account created! Check your email (console output, in "
                "development) for a verification link before you can "
                "list or borrow items."
            )
            return redirect('accounts:login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_path = reverse('accounts:verify_email', args=[uid, token])
    verify_url = request.build_absolute_uri(verify_path)

    send_mail(
        subject="Verify your P2P Asset Exchange account",
        message=(
            f"Hi {user.username},\n\n"
            f"Confirm your institutional email by visiting:\n{verify_url}\n\n"
            "If you didn't create this account, ignore this message."
        ),
        from_email=None,
        recipient_list=[user.email],
    )


def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        messages.success(request, "Email verified -- you can now log in.")
    else:
        messages.error(request, "That verification link is invalid or has expired.")
    return redirect('accounts:login')


def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            if user is None:
                messages.error(request, "Invalid email or password.")
            elif not user.is_email_verified:
                messages.error(request, "Please verify your email before logging in.")
            else:
                login(request, user)
                return redirect(request.GET.get('next') or 'accounts:profile')
    else:
        form = EmailLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    from listings.models import Asset
    my_assets = Asset.objects.filter(owner=request.user)
    return render(request, 'accounts/profile.html', {
        'profile_user': request.user,
        'my_assets': my_assets,
        'active_count': my_assets.filter(status='available').count(),
        'reserved_count': my_assets.exclude(status='available').count(),
        'total_count': my_assets.count(),
    })