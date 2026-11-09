from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, username_validator


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Parola",
        widget=forms.PasswordInput(attrs={"placeholder": "En az 8 karakter", "autocomplete": "new-password"}),
        min_length=8,
        error_messages={
            "required": "Lütfen bir parola belirleyin.",
            "min_length": "Parola en az 8 karakter olmalıdır.",
        },
    )
    password_confirm = forms.CharField(
        label="Parola Tekrar",
        widget=forms.PasswordInput(attrs={"placeholder": "Parolanızı tekrar girin", "autocomplete": "new-password"}),
        error_messages={
            "required": "Lütfen parolanızı tekrar girin.",
        },
    )

    class Meta:
        model = User
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "örn. kararsiz_biri", "autocomplete": "username"}),
            "email": forms.EmailInput(attrs={"placeholder": "ornek@eposta.com", "autocomplete": "email"}),
        }
        labels = {
            "username": "Kullanıcı Adı",
            "email": "E-posta",
        }
        help_texts = {
            "username": "3-30 karakter; yalnızca harf, rakam ve alt çizgi içerebilir. Herkese görünür.",
            "email": "Yalnızca giriş için kullanılır; diğer kullanıcılara ASLA gösterilmez.",
        }

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        username_validator(username)
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Bu kullanıcı adı zaten alınmış. Lütfen başka bir isim seçin.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Bu e-posta adresi ile zaten kayıtlı bir hesap var.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Girdiğiniz parolalar birbiriyle eşleşmiyor.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        label="E-posta",
        widget=forms.EmailInput(attrs={"placeholder": "ornek@eposta.com", "autocomplete": "email"}),
        error_messages={
            "required": "Lütfen e-posta adresinizi girin.",
            "invalid": "Geçerli bir e-posta adresi girin.",
        },
    )
    password = forms.CharField(
        label="Parola",
        widget=forms.PasswordInput(attrs={"placeholder": "Parolanız", "autocomplete": "current-password"}),
        error_messages={
            "required": "Lütfen parolanızı girin.",
        },
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").strip().lower()
        password = cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise ValidationError("E-posta adresi veya parola hatalı.")
            elif not self.user_cache.is_active:
                raise ValidationError("Bu hesap devre dışı bırakılmıştır.")

        return cleaned_data

    def get_user(self):
        return self.user_cache
