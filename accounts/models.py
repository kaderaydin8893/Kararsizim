from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("E-posta adresi zorunludur.")
        if not username:
            raise ValueError("Kullanıcı adı zorunludur.")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Süper kullanıcı is_staff=True olmalıdır.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Süper kullanıcı is_superuser=True olmalıdır.")

        return self.create_user(email, username, password, **extra_fields)


username_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9_]{3,30}$",
    message="Kullanıcı adı 3-30 karakter uzunluğunda olmalı; sadece harf, rakam ve alt çizgi içermelidir.",
)


class User(AbstractUser):
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[username_validator],
        verbose_name="Kullanıcı Adı",
        help_text="Herkese açık görünen isim (3-30 karakter, harf/rakam/alt çizgi).",
        error_messages={
            "unique": "Bu kullanıcı adı zaten alınmış.",
        },
    )
    email = models.EmailField(
        unique=True,
        verbose_name="E-posta",
        error_messages={
            "unique": "Bu e-posta adresi ile zaten bir hesap mevcut.",
        },
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username
