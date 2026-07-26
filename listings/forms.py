from django import forms

from .models import Asset

MAX_PHOTO_SIZE_MB = 5
ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp']


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['title', 'description', 'category', 'condition', 'photo']

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo:
            return photo

        if photo.size > MAX_PHOTO_SIZE_MB * 1024 * 1024:
            raise forms.ValidationError(f"Photo must be smaller than {MAX_PHOTO_SIZE_MB}MB.")

        if hasattr(photo, 'content_type') and photo.content_type not in ALLOWED_PHOTO_TYPES:
            raise forms.ValidationError("Photo must be a JPEG, PNG, or WEBP image.")

        return photo